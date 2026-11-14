"""v0.8.3 (19a): metrics, ROC/AUC, stratified cross-validation and the kernel hyperparameter search."""
import numpy as np
import pytest

from quantumscope.ml import datasets as D
from quantumscope.ml import evaluation as E
from quantumscope.ml import kernels as K

RNG = np.random.default_rng(11)


def test_metrics_by_hand():
    y = np.array([1, 1, 1, -1, -1, -1, -1, 1])
    m = E.metrics(y, np.array([1, -1, 1, -1, 1, -1, -1, 1]))
    assert m.matrix().tolist() == [[3, 1], [1, 3]] and m.total == 8
    assert (m.accuracy, m.precision, m.recall, m.specificity) == (0.75, 0.75, 0.75, 0.75)
    m = E.metrics([1, 1, 1, 1, -1], [1, 1, -1, -1, 1])                  # unbalanced
    assert m.precision == pytest.approx(2 / 3) and m.recall == 0.5 and m.f1 == pytest.approx(4 / 7)
    assert m.balanced_accuracy == pytest.approx(0.25)
    assert E.metrics([-1, -1], [-1, -1]).precision == 0.0                 # nothing predicted +1: no division by 0


def test_auc_two_independent_ways_and_edge_cases():
    for _ in range(200):
        n = int(RNG.integers(4, 50))
        y = np.where(RNG.uniform(size=n) < 0.5, 1, -1)
        if len(set(y)) < 2:
            continue
        s = np.round(RNG.normal(size=n) + y, 1)                           # many ties
        assert E.auc(y, s) == pytest.approx(E.auc_by_ranks(y, s), abs=1e-12)
    assert E.auc([1, 1, -1, -1], [2, 1, 0, -1]) == 1.0 and E.auc([1, 1, -1, -1], [-1, 0, 1, 2]) == 0.0
    assert E.auc([1, -1, 1, -1], [0, 0, 0, 0]) == 0.5
    fpr, tpr, _ = E.roc([1, -1, 1, -1, 1], [0.9, 0.8, 0.7, 0.2, 0.1])
    assert (fpr[0], tpr[0], fpr[-1], tpr[-1]) == (0, 0, 1, 1) and np.all(np.diff(fpr) >= 0)
    with pytest.raises(ValueError):
        E.roc([1, 1], [0.1, 0.2])


def test_stratified_folds():
    y = np.array([1] * 30 + [-1] * 12)
    folds = E.stratified_folds(y, 4, seed=3)
    validated = np.concatenate([v for _, v in folds])
    assert sorted(validated.tolist()) == list(range(len(y)))              # each sample validated once
    for train, valid in folds:
        assert not set(train) & set(valid) and np.sum(y[valid] == -1) == 3   # proportions kept
    with pytest.raises(ValueError, match='at least 5 samples of each class'):
        E.stratified_folds(np.array([1] * 20 + [-1] * 3), 5)


@pytest.fixture(scope='module')
def digits():
    ds = D.load('mnist')
    recipe = D.check(ds, qubits=4)[2]
    recipe.classes = (3, 8)
    return D.prepare(ds, recipe)


def test_cross_validation_on_a_shared_kernel_equals_recomputing_every_fold(digits):
    p = digits
    folds = E.stratified_folds(p.y_train, 5)
    shared = E.cross_validate_kernel(K.kernel(p.X_train, kind='zz', bandwidth=0.5), p.y_train,
                                     lambda: K.SVM(C=1.0), folds)
    for (train, valid), score in zip(folds, shared.scores):
        model = K.SVM(C=1.0).fit(K.kernel(p.X_train[train], kind='zz', bandwidth=0.5), p.y_train[train])
        predicted = model.predict(K.kernel(p.X_train[valid], p.X_train[train], kind='zz', bandwidth=0.5))
        assert score == pytest.approx(np.mean(predicted == p.y_train[valid]))
    assert len(shared.metrics) == 5 and 0 <= shared.std <= 0.5


def test_the_search_shares_kernels_finds_the_best_and_can_stop(digits):
    p = digits
    grid = dict(feature_map=['angle', 'zz'], reps=[1, 2], bandwidth=[0.25, 0.5], method=['svm', 'ridge'],
                strength=[0.1, 1.0])
    calls = []

    def counting(*args, **kwargs):
        calls.append(kwargs)
        return K.kernel(*args, **kwargs)
    steps = []
    rows, best = E.search_kernel(p.X_train, p.y_train, grid, k=3, kernel=counting,
                                 progress=lambda done, total: steps.append((done, total)))
    assert len(calls) == 2 + 4                                           # angle: 2 bandwidths; zz: 2 reps × 2
    assert len(rows) == 6 * 4 and steps[-1] == (24, 24)
    assert best is rows[0] and all(best.mean >= r.mean for r in rows)
    assert all(r.settings['reps'] == 1 for r in rows if r.settings['feature_map'] == 'angle')
    ties = [r for r in rows if abs(r.mean - best.mean) < 1e-12]
    assert best.std == min(r.std for r in ties)                          # the steadiest among equals
    assert E.search_kernel(p.X_train, p.y_train, grid, k=3, cancelled=lambda: True) is None
