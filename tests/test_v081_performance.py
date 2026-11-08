"""v0.8.1: speed limits, so that performance cannot quietly regress.

Each limit is about four times the time measured on a development machine, to allow for slower CI
runners; the v0.8.0 times are noted for comparison.
"""
import time

import numpy as np
import pytest

from quantumscope.ml import datasets as D
from quantumscope.ml import kernels as K
from quantumscope.ml import variational as V


def timed(fn):
    start = time.perf_counter()
    out = fn()
    return out, time.perf_counter() - start


def prepared(name, qubits):
    ds = D.load(name)
    return D.prepare(ds, D.check(ds, qubits=qubits, max_samples=200)[2])


def test_variational_training_at_8_qubits():                                  # v0.8.0: 11.4 s; now ≈ 1.3 s
    p = prepared('mnist', 8)
    history, seconds = timed(lambda: V.Classifier(8, layers=3, seed=1).train(p.X_train, p.y_train, steps=40))
    assert seconds < 6.0, f'{seconds:.1f} s'
    assert history[-1][1] < history[0][1]


def test_adjoint_and_parameter_shift_give_the_same_training():
    p = prepared('moons', 2)
    a = V.Classifier(2, layers=2, seed=3, gradient='adjoint').train(p.X_train, p.y_train, steps=15)
    b = V.Classifier(2, layers=2, seed=3, gradient='shift').train(p.X_train, p.y_train, steps=15)
    # Equal up to rounding (the two gradients differ by about 1e-15), so the paths may part in the
    # last digits; a wrong gradient would part them visibly within a few steps.
    assert all(abs(x[1] - y[1]) < 1e-6 for x, y in zip(a, b)) and abs(len(a) - len(b)) <= 2


@pytest.mark.parametrize('name, qubits, kind', [('mnist', 4, 'zz'), ('breast_cancer', 8, 'zz'), ('circles', 2, 'angle')])
def test_svm_training(name, qubits, kind):                                    # v0.8.0: up to 1.0 s; now ≤ 0.02 s
    p = prepared(name, qubits)
    Ktr = K.kernel(p.X_train, kind=kind)
    svm, seconds = timed(lambda: K.SVM().fit(Ktr, p.y_train))
    assert seconds < 0.25, f'{seconds:.2f} s'
    margin = p.y_train * svm.decision(Ktr)                                       # still optimal (KKT)
    assert np.all(margin[svm.alpha < 1e-6] >= 1 - 1e-2)


def test_kernels_and_decision_grid_at_10_qubits():
    p = prepared('breast_cancer', 10)
    _, seconds = timed(lambda: K.kernel(p.X_train, kind='zz'))
    assert seconds < 1.0, f'{seconds:.2f} s'
    grid = np.random.default_rng(0).uniform(0, 3, (2500, 10))
    _, seconds = timed(lambda: K.kernel(grid, p.X_train, kind='zz'))
    assert seconds < 5.0, f'{seconds:.2f} s'
