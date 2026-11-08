"""v0.8.3 (19b): the variational classifier's losses, validation, early stopping and mini-batches."""
import math

import numpy as np
import pytest

from quantumscope.ml import datasets as D
from quantumscope.ml import models as M
from quantumscope.ml import variational as V

RNG = np.random.default_rng(8)


@pytest.mark.parametrize('loss', list(V.LOSSES))
def test_every_loss_has_an_exact_gradient(loss):
    X, y = RNG.uniform(0, math.pi, (12, 3)), np.where(RNG.uniform(size=12) > 0.5, 1.0, -1.0)
    model = V.Classifier(3, layers=2, feature_map='zz', loss=loss)
    model.theta, model.bias = RNG.uniform(-1, 1, 6), 0.1
    adjoint, adjoint_bias = model.gradient(X, y, method='adjoint')
    shift, shift_bias = model.gradient(X, y, method='shift')
    assert np.allclose(adjoint, shift, atol=1e-12) and adjoint_bias == pytest.approx(shift_bias, abs=1e-12)
    h = 1e-6
    for k in range(6):
        e = np.eye(6)[k] * h
        numeric = (model.loss(X, y, model.theta + e) - model.loss(X, y, model.theta - e)) / (2 * h)
        assert adjoint[k] == pytest.approx(numeric, abs=1e-7)
    with pytest.raises(ValueError):
        V.Classifier(2, loss='absolute')


def test_the_losses_by_hand():
    out, y = np.array([0.5, -2.0, 0.0]), np.array([1.0, 1.0, -1.0])
    assert V.LOSSES['mse'](out, y)[0] == pytest.approx([0.125, 4.5, 0.5])
    assert V.LOSSES['hinge'](out, y)[0] == pytest.approx([0.5, 3.0, 1.0])
    assert V.LOSSES['cross-entropy'](np.array([0.0]), np.array([1.0]))[0] == pytest.approx([math.log(2)])


@pytest.fixture(scope='module')
def cancer():
    ds = D.load('breast_cancer')
    p = D.prepare(ds, D.check(ds, qubits=4)[2])
    n = len(p.y_train) // 4
    return (p.X_train[n:], p.y_train[n:]), (p.X_train[:n], p.y_train[:n])


def test_validation_and_early_stopping_restore_the_best_step(cancer):
    train, valid = cancer
    seen = []
    model = V.Classifier(4, layers=3, seed=1)
    history = model.train(*train, method='Adam', steps=200, rate=0.08, validation=valid, patience=10,
                          callback=lambda *args: seen.append(len(args)))
    assert set(seen) == {4} and len(model.validation) == len(history)        # validation passed every step
    assert model.stopped_early and len(history) < 201
    best = min(model.validation, key=lambda v: v[1])
    assert model.best_step == best[0] and model.loss(*valid) == pytest.approx(best[1], abs=1e-12)
    with pytest.raises(ValueError, match='validation'):
        V.Classifier(4).train(*train, patience=5)


def test_mini_batches(cancer):
    train, _ = cancer
    a = V.Classifier(4, layers=2, seed=3).train(*train, method='Adam', steps=30, batch_size=24, seed=5)
    b = V.Classifier(4, layers=2, seed=3).train(*train, method='Adam', steps=30, batch_size=24, seed=5)
    assert a == b and a[-1][1] < a[0][1]                                       # reproducible, and it learns
    whole = V.Classifier(4, layers=2, seed=3)
    history = whole.train(*train, method='Adam', steps=4, batch_size=len(train[1]), seed=1)
    assert history[-1][1] == pytest.approx(whole.loss(*train), abs=1e-12)      # shuffled full batch: right loss
    with pytest.raises(ValueError, match='Adam'):
        V.Classifier(4).train(*train, method='BFGS', batch_size=16)


def test_defaults_train_exactly_as_before_and_models_record_the_loss(cancer):
    train, _ = cancer
    plain = V.Classifier(4, layers=2, seed=2).train(*train, steps=15)
    explicit = V.Classifier(4, layers=2, seed=2, loss='mse').train(*train, steps=15, validation=None, batch_size=0)
    assert plain == explicit
    ds = D.load('iris')
    p = D.prepare(ds, D.check(ds, qubits=2)[2])
    clf = V.Classifier(2, layers=2, loss='hinge')
    clf.train(p.X_train, p.y_train, steps=5)
    assert M.from_variational(clf, p, {'method': 'BFGS'}, 1, 1, 'iris').settings['loss'] == 'hinge'
