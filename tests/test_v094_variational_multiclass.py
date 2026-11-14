"""v0.9.4: a variational classifier for any number of classes (no Qt)."""
import json
import math

import numpy as np
import pytest

from quantumscope.ml import datasets as D
from quantumscope.ml import evaluation as E
from quantumscope.ml import models as M
from quantumscope.ml import variational as V
from quantumscope.physics.circuits import evolution


def _data(name='iris', qubits=4):
    ds = D.load(name)
    return ds, D.prepare(ds, D.check(ds, qubits=qubits, max_classes=None, max_samples=300)[2])


def test_readout_qubits_name_the_classes():
    assert [V.readout_qubits(k) for k in (2, 3, 4, 5, 8, 9, 10)] == [1, 2, 2, 3, 3, 4, 4]
    with pytest.raises(ValueError, match='at least 4 qubits'):
        V.MultiClassifier(3, 10)
    model = V.MultiClassifier(4, 3)
    assert model.readout == 2 and model.bias.shape == (3,) and model.loss_name == 'cross-entropy'
    assert model.outcome_of_basis().tolist() == [0] * 4 + [1] * 4 + [2] * 4 + [3] * 4     # q0 q1 = outcome


def test_outcome_probabilities_match_the_circuit_simulator():
    rng = np.random.default_rng(3)
    model = V.MultiClassifier(4, 3, layers=2, seed=2)
    model.theta = rng.uniform(-math.pi, math.pi, len(model.theta))
    X = rng.uniform(0, math.pi, (5, 4))
    raw = model.expectation(X)
    for x, row in zip(X, raw):
        state = evolution(4, model.gates(x))[-1]                     # the same gates, simulated one by one
        outcome = np.abs(state.reshape(4, 4)) ** 2                    # q0 q1 × the rest
        assert np.allclose(row, outcome.sum(axis=1))
    assert np.allclose(raw.sum(axis=1), 1)


def test_class_probabilities_by_hand():
    model = V.MultiClassifier(2, 3, layers=1)
    raw = np.array([[0.5, 0.25, 0.125, 0.125]])                         # outcome 3 names no class: discarded
    model.bias = np.array([0.0, math.log(2), 0.0])                      # class 1 counts double
    values, slope, grad_bias, P = model._head(raw, np.array([1]), model.bias)
    assert np.allclose(P, [[0.5 / 1.125, 0.5 / 1.125, 0.125 / 1.125]])
    assert values[0] == pytest.approx(-math.log(0.5 / 1.125))
    assert np.allclose(grad_bias, P[0] - [0, 1, 0]) and slope[0, 3] == 0


def test_gradients_are_exact():
    rng = np.random.default_rng(0)
    model = V.MultiClassifier(4, 3, layers=2, seed=1)
    model.bias = rng.normal(size=3) * 0.3
    X, y = rng.uniform(0, 3, (12, 4)), rng.integers(0, 3, 12)
    g, gb = model.gradient(X, y)
    gs, gbs = model.gradient(X, y, method='shift')                      # the parameter-shift rule, as on hardware
    eps = 1e-6
    numeric = np.zeros(len(model.theta))
    for k in range(len(model.theta)):
        t = model.theta.copy()
        t[k] += eps
        up = model.loss(X, y, t)
        t[k] -= 2 * eps
        numeric[k] = (up - model.loss(X, y, t)) / (2 * eps)
    numeric_bias = np.zeros(3)
    for c in range(3):
        b = model.bias.copy()
        b[c] += eps
        up = model.loss(X, y, bias=b)
        b[c] -= 2 * eps
        numeric_bias[c] = (up - model.loss(X, y, bias=b)) / (2 * eps)
    assert np.allclose(g, numeric, atol=1e-7) and np.allclose(gs, numeric, atol=1e-7)
    assert np.allclose(gb, numeric_bias, atol=1e-7) and np.allclose(gbs, gb)


@pytest.mark.parametrize('method', ['BFGS', 'Adam'])
def test_three_iris_species(method):
    _, p = _data('iris')
    model = V.MultiClassifier(4, 3, layers=3, seed=0)
    history = model.train(p.X_train, p.y_train, method=method, steps=150 if method == 'BFGS' else 200, rate=0.1)
    assert history[-1][1] < history[0][1]                                # the loss fell
    assert float(np.mean(model.predict(p.X_test) == p.y_test)) >= 0.85
    P = model.decision(p.X_test)
    assert P.shape == (len(p.y_test), 3) and np.allclose(P.sum(axis=1), 1)


def test_ten_digits_beat_chance_by_far():
    _, p = _data('digits', qubits=6)
    model = V.MultiClassifier(6, 10, layers=4, seed=0)
    model.train(p.X_train, p.y_train, steps=150)
    assert p.k == 10 and float(np.mean(model.predict(p.X_test) == p.y_test)) >= 0.5      # chance: 10%


def test_validation_and_early_stopping_with_many_classes():
    _, p = _data('wine')
    kept, held = E.stratified_split(p.y_train, 0.25)
    model = V.MultiClassifier(4, 3, layers=2, seed=0)
    model.train(p.X_train[kept], p.y_train[kept], method='Adam', steps=300, rate=0.2,
                validation=(p.X_train[held], p.y_train[held]), patience=5)
    assert model.validation and (not model.stopped_early or model.best_step is not None)
    assert np.ndim(model.bias) == 1 and len(model.bias) == 3


def test_cross_validation_with_many_classes():
    _, p = _data('iris', qubits=3)
    folds = E.stratified_folds(p.y_train, 3)
    cv = E.cross_validate_variational(p.X_train, p.y_train, lambda: V.MultiClassifier(3, 3, layers=2), folds,
                                      dict(steps=60))
    assert len(cv.scores) == 3 and isinstance(cv.metrics[0], E.MultiMetrics) and cv.mean > 0.6


def test_two_class_training_is_unchanged():
    _, p = _data('iris', qubits=2)
    p2 = D.prepare(D.load('breast_cancer'), D.check(D.load('breast_cancer'), qubits=2)[2])
    model = V.Classifier(2, layers=2, seed=0)
    history = model.train(p2.X_train, p2.y_train, steps=40)
    assert isinstance(model.bias, float) and set(np.unique(model.predict(p2.X_test))) <= {-1, 1}
    assert history[-1][2] > 0.8


def test_many_class_variational_models_save_and_load(tmp_path):
    ds, p = _data('seeds', qubits=3)
    model = V.MultiClassifier(3, 3, layers=2, seed=0)
    model.train(p.X_train, p.y_train, steps=60)
    settings = dict(method='BFGS', layers=2)
    trained = M.from_variational(model, p, settings, 0.9, 0.9, 'seeds')
    path = trained.save(tmp_path / 'seeds-circuit')
    with np.load(path) as z:
        assert json.loads(str(z['header']))['version'] == 2
    loaded = M.load(path)
    assert isinstance(loaded.classifier(), V.MultiClassifier) and loaded.k == 3
    names, values = loaded.predict(ds.X[p.test_rows])
    assert names == [p.classes[c] for c in model.predict(p.X_test)]
    assert np.all((0 < values) & (values <= 1))                         # the winning class's probability
    trained.arrays['bias'] = np.zeros(2)
    with pytest.raises(ValueError, match='offsets'):
        M.load(trained.save(tmp_path / 'broken'))
