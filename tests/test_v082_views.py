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


def _trained(name='mnist', qubits=4):
    from quantumscope.ml import datasets as D
    from quantumscope.ml import models as M
    ds = D.load(name)
    p = D.prepare(ds, D.check(ds, qubits=qubits)[2])
    svm = K.SVM().fit(K.kernel(p.X_train, kind='zz', bandwidth=0.5), p.y_train)
    settings = dict(kind='zz', reps=2, bandwidth=0.5, method='svm', strength=1.0)
    return p, M.from_kernel(svm, p, settings, 1, 1, name)


def test_3d_axes_are_orthonormal_and_the_separating_axis_points_between_the_classes():
    p, _ = _trained('breast_cancer', 6)
    for kind in ('pca', 'separating'):
        axes = views.axes3d(p.X_train, p.y_train, kind)
        assert np.allclose(axes['basis'] @ axes['basis'].T, np.eye(3), atol=1e-10)
        assert len(axes['short']) == 3 and all(len(s) <= 3 for s in axes['short'])
    sep = views.axes3d(p.X_train, p.y_train, 'separating')
    gap = p.X_train[p.y_train == 1].mean(axis=0) - p.X_train[p.y_train != 1].mean(axis=0)
    assert np.isclose(abs(sep['basis'][0] @ gap), np.linalg.norm(gap))                 # along the class gap
    try:
        views.axes3d(p.X_train[:, :2], p.y_train)
    except ValueError as exc:
        assert 'at least 3' in str(exc)
    else:
        raise AssertionError('two features accepted')


def test_slice_agreement_is_complete_with_three_features_and_the_grid_matches_the_model():
    p, model = _trained('iris', 3)
    axes = views.axes3d(p.X_train, p.y_train, 'pca')
    assert views.slice_agreement(model.decision, axes, np.r_[p.X_train, p.X_test]) == 1.0   # the slice is everything
    ticks, f = views.decision_grid(model.decision, axes, views.project(axes, p.X_train), 7)
    i, j, k = 2, 5, 3
    point = views.lift(axes, [[ticks[0][i], ticks[1][j], ticks[2][k]]])
    assert np.isclose(f[i, j, k], model.decision(point)[0])                            # grid[i, j, k] is that point
    assert views.decision_grid(model.decision, axes, views.project(axes, p.X_train), 7, cancelled=lambda: True) is None
