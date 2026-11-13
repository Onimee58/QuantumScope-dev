"""v0.9.3: more classes for the kernel classifier, and four more datasets (no Qt)."""
import json

import numpy as np
import pytest

from quantumscope.ml import datasets as D
from quantumscope.ml import evaluation as E
from quantumscope.ml import kernels as K
from quantumscope.ml import models as M
from quantumscope.ml import views


# ---- the new datasets ---------------------------------------------------------------------------
@pytest.mark.parametrize('name, samples, features, counts', [
    ('fashion_mnist', 2000, 784, [200] * 10),
    ('penguins', 344, 7, [152, 68, 124]),                      # Adelie, Chinstrap, Gentoo
    ('seeds', 210, 7, [70, 70, 70]),
    ('glass', 214, 9, [70, 76, 17, 13, 9, 29]),                # UCI's published counts (no type 4)
])
def test_new_datasets_match_their_published_counts(name, samples, features, counts):
    ds = D.load(name)
    assert ds.X.shape == (samples, features) and list(ds.counts) == counts
    assert ds.license and ds.citation and ds.description
    assert name in open(f'{D.DATA}/DATASETS.md', encoding='utf-8').read().replace('.npz', '').replace('.csv', '')


def test_fashion_mnist_is_an_image_subset_of_the_official_test_set():
    ds = D.load('fashion_mnist')
    assert ds.image_shape == (28, 28) and ds.classes[0] == 'T-shirt/top' and ds.classes[9] == 'Ankle boot'
    with np.load(f'{D.DATA}/fashion_mnist.npz') as z:
        index = z['index']
    assert len(set(index.tolist())) == 2000 and index.max() < 10000 and ds.X.max() == 255


def test_penguins_keeps_its_text_columns_and_missing_values():
    ds = D.load('penguins')
    assert ds.name == 'Palmer Penguins' and ds.license == 'CC0 1.0'
    text = {ds.features[i]: v for i, v in ds.text_columns.items()}
    assert text == {'island': ['Biscoe', 'Dream', 'Torgersen'], 'sex': ['female', 'male']}
    assert int(np.isnan(ds.X).sum()) == 19                       # 2 × 4 measurements + 11 unknown sexes
    verdict, findings, recipe = D.check(ds, qubits=4, max_classes=None)
    words = ' '.join(f.message for f in findings)
    assert verdict == 'preprocess' and 'missing values' in words and 'Text columns' in words
    assert recipe.missing in ('drop', 'mean') and recipe.classes == (0, 1, 2)


# ---- checking and preparing many classes ----------------------------------------------------
def test_the_checker_suggests_two_classes_by_default_and_all_on_request():
    ds = D.load('iris')
    assert D.check(ds)[2].classes == (0, 1)                      # unchanged: a pair
    verdict, findings, recipe = D.check(ds, max_classes=None)
    assert recipe.classes == (0, 1, 2) and any('one-vs-rest' in f.message for f in findings)


def test_classes_too_small_to_learn_and_test_are_left_out():
    verdict, findings, recipe = D.check(D.load('glass'), qubits=4, max_classes=None)
    assert verdict != 'stop' and recipe.classes == (0, 1, 2, 3, 5)          # tableware (9) left out
    assert any('tableware (9)' in f.message for f in findings)


def test_ten_classes_keep_enough_samples_of_each():
    recipe = D.check(D.load('mnist'), qubits=4, max_classes=None)[2]
    assert len(recipe.classes) == 10 and recipe.per_class == 40          # 400 in all, not 20 per digit


def test_prepare_many_classes_gives_labels_in_class_order_and_stratifies():
    ds = D.load('iris')
    recipe = D.check(ds, qubits=3, max_classes=None)[2]
    recipe.classes = (2, 0, 1)                                    # any order: labels follow it
    p = D.prepare(ds, recipe)
    assert p.k == 3 and p.classes == ('virginica', 'setosa', 'versicolor')
    assert set(np.unique(p.y_train)) == {0, 1, 2} and np.bincount(p.y_test).tolist() == [12, 12, 12]
    assert p.label_name(0) == 'virginica' and p.pipeline.classes == p.classes
    assert all((ds.y[p.train_rows] == np.array((2, 0, 1))[p.y_train]))    # each label names its rows' class
    with pytest.raises(ValueError):
        D.prepare(ds, D.Recipe(classes=(1, 1)))


# ---- one-vs-rest ----------------------------------------------------------------------------
def _iris(qubits=4):
    p = D.prepare(D.load('iris'), D.check(D.load('iris'), qubits=qubits, max_classes=None)[2])
    return p, K.kernel(p.X_train, kind='angle'), K.kernel(p.X_test, p.X_train, kind='angle')


def test_one_vs_rest_is_k_binary_classifiers_on_one_kernel():
    p, Ktr, Kte = _iris()
    model = K.classifier('svm', 1.0, 3).fit(Ktr, p.y_train)
    assert isinstance(model, K.OneVsRest) and len(model.models) == 3
    for c, binary in enumerate(model.models):
        alone = K.SVM(C=1.0).fit(Ktr, np.where(p.y_train == c, 1, -1))
        assert np.allclose(binary.decision(Kte), alone.decision(Kte))
    scores = model.decision(Kte)
    assert scores.shape == (len(p.y_test), 3) and np.array_equal(model.predict(Kte), scores.argmax(axis=1))
    assert K.accuracy(p.y_test, model.predict(Kte)) >= 0.9
    assert set(model.support) <= set(range(len(p.y_train))) and len(model.support) < len(p.y_train)
    assert isinstance(K.classifier('ridge', 0.1, 2), K.KernelRidge) and K.classes_in(p.y_train) == 3


def test_digits_ten_classes_on_eight_qubits():
    ds = D.load('digits')
    p = D.prepare(ds, D.check(ds, qubits=8, max_classes=None)[2])
    model = K.classifier('svm', 1.0, 10).fit(K.kernel(p.X_train, kind='angle'), p.y_train)
    accuracy = K.accuracy(p.y_test, model.predict(K.kernel(p.X_test, p.X_train, kind='angle')))
    assert p.k == 10 and accuracy >= 0.85                       # chance is 10%


# ---- evaluation -----------------------------------------------------------------------------
def test_multi_metrics_by_hand():
    y_true = [0, 0, 0, 1, 1, 2]
    y_pred = [0, 0, 1, 1, 2, 2]
    m = E.multi_metrics(y_true, y_pred, 3)
    assert m.matrix().tolist() == [[2, 1, 0], [0, 1, 1], [0, 0, 1]]
    assert m.accuracy == pytest.approx(4 / 6)
    assert np.allclose(m.recalls, [2 / 3, 1 / 2, 1]) and np.allclose(m.precisions, [1, 1 / 2, 1 / 2])
    assert m.balanced_accuracy == pytest.approx((2 / 3 + 1 / 2 + 1) / 3)
    assert m.macro_f1 == pytest.approx(np.mean([0.8, 0.5, 2 / 3]))
    assert E.multi_metrics([0, 1], [0, 0], 3).balanced_accuracy == pytest.approx(0.5)   # class 2 absent: not counted


def test_two_class_metrics_agree_with_the_general_ones():
    rng = np.random.default_rng(1)
    y, guess = rng.choice((-1, 1), 50), rng.choice((-1, 1), 50)
    two, general = E.score(y, guess, 2), E.multi_metrics((y == -1).astype(int), (guess == -1).astype(int), 2)
    assert two.accuracy == pytest.approx(general.accuracy)
    assert two.balanced_accuracy == pytest.approx(general.balanced_accuracy)
    assert two.recall == pytest.approx(general.recalls[0]) and two.precision == pytest.approx(general.precisions[0])


def test_one_vs_rest_roc_curves():
    p, Ktr, Kte = _iris()
    model = K.classifier('svm', 1.0, 3).fit(Ktr, p.y_train)
    curves = E.roc_by_class(p.y_test, model.decision(Kte))
    assert sorted(curves) == [0, 1, 2] and all(0.5 < c[2] <= 1 for c in curves.values())
    for c, (fpr, tpr, area) in curves.items():
        assert area == pytest.approx(E.auc_by_ranks(np.where(p.y_test == c, 1, -1), model.decision(Kte)[:, c]))


def test_cross_validation_and_search_with_many_classes():
    p, Ktr, _ = _iris()
    folds = E.stratified_folds(p.y_train, 5)
    cv = E.cross_validate_kernel(Ktr, p.y_train, lambda: K.classifier('svm', 1.0, 3), folds)
    assert len(cv.scores) == 5 and cv.mean > 0.85 and isinstance(cv.metrics[0], E.MultiMetrics)
    grid = dict(feature_map=['angle'], reps=[1], bandwidth=[0.5, 1.0], method=['svm', 'ridge'], strength=[1.0])
    rows, best = E.search_kernel(p.X_train, p.y_train, grid, k=3)
    assert len(rows) == 4 and best.mean >= max(r.mean for r in rows) - 1e-12


# ---- saved models ---------------------------------------------------------------------------
@pytest.mark.parametrize('method', ['svm', 'ridge'])
def test_many_class_models_save_load_and_predict(tmp_path, method):
    ds = D.load('seeds')
    p = D.prepare(ds, D.check(ds, qubits=3, max_classes=None)[2])
    settings = dict(kind='angle', reps=1, bandwidth=1.0, method=method, strength=1.0 if method == 'svm' else 0.1)
    model = K.classifier(method, settings['strength'], 3).fit(K.kernel(p.X_train, kind='angle'), p.y_train)
    trained = M.from_kernel(model, p, settings, 1.0, 1.0, 'seeds')
    expected = model.predict(K.kernel(p.X_test, p.X_train, kind='angle'))
    path = trained.save(tmp_path / 'seeds')
    with np.load(path) as z:
        assert json.loads(str(z['header']))['version'] == 2
    loaded = M.load(path)
    assert loaded.k == 3 and loaded.classes == p.classes
    names, values = loaded.predict(ds.X[p.test_rows])
    assert names == [p.classes[c] for c in expected] and len(values) == len(names)
    if method == 'svm':                                          # only the points some classifier uses
        assert len(loaded.arrays['points']) == len(model.support) < len(p.y_train)


def test_two_class_models_are_still_saved_as_version_1(tmp_path):
    ds = D.load('iris')
    p = D.prepare(ds, D.check(ds, qubits=2)[2])
    model = K.SVM().fit(K.kernel(p.X_train, kind='angle'), p.y_train)
    settings = dict(kind='angle', reps=1, bandwidth=1.0, method='svm', strength=1.0)
    path = M.from_kernel(model, p, settings, 1.0, 1.0, 'iris').save(tmp_path / 'pair')
    with np.load(path) as z:
        assert json.loads(str(z['header']))['version'] == 1      # older QuantumScope versions open it


def test_a_damaged_many_class_model_is_refused(tmp_path):
    ds = D.load('seeds')
    p = D.prepare(ds, D.check(ds, qubits=3, max_classes=None)[2])
    model = K.classifier('svm', 1.0, 3).fit(K.kernel(p.X_train, kind='angle'), p.y_train)
    trained = M.from_kernel(model, p, dict(kind='angle', reps=1, bandwidth=1.0, method='svm', strength=1.0), 1, 1)
    trained.arrays['b'] = np.array([0.0, 0.0])                   # one class's offset missing
    with pytest.raises(ValueError, match='classes'):
        M.load(trained.save(tmp_path / 'broken'))


# ---- the 3-D view ---------------------------------------------------------------------------
def test_separating_axes_for_many_classes_follow_the_class_centres():
    p, Ktr, _ = _iris()
    axes = views.axes3d(p.X_train, p.y_train, 'separating')
    B = axes['basis']
    assert np.allclose(B @ B.T, np.eye(3), atol=1e-9)
    assert axes['names'][:2] == ['class spread 1', 'class spread 2'] and axes['names'][2] == 'remaining PC1'
    centres = np.array([p.X_train[p.y_train == c].mean(axis=0) for c in range(3)]) - p.X_train.mean(axis=0)
    inside = np.linalg.norm(centres @ B[:2].T @ B[:2], axis=1)
    assert np.allclose(inside, np.linalg.norm(centres, axis=1))   # three centres span a plane: all in view


def test_many_class_decision_grid_margins_and_agreement():
    p, Ktr, _ = _iris(qubits=3)
    model = K.classifier('svm', 1.0, 3).fit(Ktr, p.y_train)

    def decision(X):
        return model.decision(K.kernel(X, p.X_train, kind='angle'))
    axes = views.axes3d(p.X_train, p.y_train, 'pca')
    ticks, f = views.decision_grid(decision, axes, views.project(axes, p.X_train), 6)
    assert f.shape == (6, 6, 6, 3)
    margins = views.class_margins(f)
    assert np.all((margins > 0).sum(axis=-1) <= 1)                 # at most one class wins anywhere
    assert np.array_equal(margins.argmax(axis=-1), f.argmax(axis=-1))
    assert views.slice_agreement(decision, axes, p.X_train) == 1.0                    # 3 features: no slice
    assert np.array_equal(views.winners(np.array([0.5, -0.2])), [1, -1])
