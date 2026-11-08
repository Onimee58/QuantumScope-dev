"""v0.8.2 (18c): the kernel map (kernel PCA)."""
import numpy as np

from quantumscope.ml import kernels as K
from quantumscope.ml import views


def test_with_a_linear_kernel_the_kernel_map_is_ordinary_pca():
    rng = np.random.default_rng(0)
    X = rng.normal(size=(60, 5)) * [3, 2, 1, 0.5, 0.2]
    X_new = rng.normal(size=(10, 5))
    train, test, shown, _ = views.kernel_map(X @ X.T, X_new @ X.T)
    mean = X.mean(axis=0)
    _, s, vt = np.linalg.svd(X - mean, full_matrices=False)
    signs = np.sign(np.sum(train * ((X - mean) @ vt[:2].T), axis=0))             # each axis up to its sign
    assert np.allclose(train * signs, (X - mean) @ vt[:2].T, atol=1e-9)
    assert np.allclose(test * signs, (X_new - mean) @ vt[:2].T, atol=1e-9)
    assert shown == np.float64((s[:2] ** 2).sum() / (s ** 2).sum()) or abs(shown - (s[:2] ** 2).sum() / (s ** 2).sum()) < 1e-12


def test_a_training_point_given_as_new_lands_on_itself():
    X = np.random.default_rng(1).uniform(0, 3, (40, 3))
    Ktr = K.kernel(X, kind='zz', bandwidth=0.5)
    train, again, _, _ = views.kernel_map(Ktr, K.kernel(X[:5], X, kind='zz', bandwidth=0.5))
    assert np.allclose(again, train[:5], atol=1e-10)
