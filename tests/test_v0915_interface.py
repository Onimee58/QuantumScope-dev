"""v0.9.15: plain gradient descent for the variational classifier (no window)."""
import numpy as np
import pytest

from quantumscope.ml import variational as V


def data():
    rng = np.random.default_rng(0)
    X = rng.uniform(0, np.pi, (40, 2))
    y = np.where(X[:, 0] > np.pi / 2, 1.0, -1.0)
    return X, y


def test_gradient_descent_lowers_the_loss_with_a_sensible_rate():
    X, y = data()
    model = V.Classifier(2, layers=2, seed=1)
    history = model.train(X, y, method='gradient', steps=30, rate=0.2)
    assert len(history) == 31 and history[-1][1] < history[0][1]


def test_one_step_is_rate_times_the_gradient():
    X, y = data()
    model = V.Classifier(2, layers=1, seed=2)
    start = np.r_[model.theta, model.bias]
    g, gb = model.gradient(X, y, model.theta, model.bias)
    model.train(X, y, method='gradient', steps=1, rate=0.05)
    assert np.allclose(np.r_[model.theta, model.bias], start - 0.05 * np.r_[g, gb])


def test_mini_batches_work_and_bfgs_refuses_them():
    X, y = data()
    model = V.Classifier(2, layers=2, seed=1)
    small = model.train(X, y, method='gradient', steps=10, rate=0.1, batch_size=8)
    assert len(small) == 11
    with pytest.raises(ValueError, match='BFGS'):
        V.Classifier(2, layers=1).train(X, y, method='BFGS', steps=2, batch_size=8)
    with pytest.raises(ValueError, match='Unknown'):
        V.Classifier(2, layers=1).train(X, y, method='SGD', steps=2)
