"""Pictures of a kernel classifier (v0.8.2, no Qt): the kernel map, and the 3-D decision view.

Kernel map (kernel PCA, Schölkopf et al.): centre the training kernel, Kc = H K H with
H = I − 1/N, and place each training point at its coordinates along Kc's two leading eigenvectors,
scaled by √λ. Test points use their kernel values against the training points, centred the same
way. Points the kernel finds similar land close together; it needs no new circuits.
"""
import numpy as np


def kernel_map(K_train, K_test=None, dims=2):
    """(train coordinates, test coordinates or None, share of the variance shown, eigenvalues)."""
    K = np.asarray(K_train, float)
    n = len(K)
    ones = np.full((n, n), 1.0 / n)
    Kc = K - ones @ K - K @ ones + ones @ K @ ones
    Kc = (Kc + Kc.T) / 2                                          # exactly symmetric for eigh
    values, vectors = np.linalg.eigh(Kc)
    order = np.argsort(values)[::-1]
    values, vectors = values[order], vectors[:, order]
    positive = np.clip(values, 0, None)
    lam = positive[:dims]
    scale = np.where(lam > 1e-12, np.sqrt(lam), 1.0)
    alphas = vectors[:, :dims] / scale                            # projection weights
    train = Kc @ alphas
    shown = float(lam.sum() / positive.sum()) if positive.sum() > 1e-12 else 0.0
    test = None
    if K_test is not None:
        Kt = np.atleast_2d(np.asarray(K_test, float))
        ones_t = np.full((len(Kt), n), 1.0 / n)
        Kt_c = Kt - ones_t @ K - Kt @ ones + ones_t @ K @ ones
        test = Kt_c @ alphas
    return train, test, shown, values


# ---- the 3-D decision view -------------------------------------------------------------------------
AXES = (('Principal components', 'pca'), ('Separating axes', 'separating'))


def axes3d(X, y, kind='pca'):
    """Three orthonormal directions to view n-D data in 3-D (n ≥ 3), the data's mean, axis names and
    the share of the data's variance along each axis.
      pca         the three directions of greatest variance
      separating  first the line from one class's centre to the other's, then the two main
                  directions of what is left (perpendicular to it): the class separation in view.
                  With more classes (labels 0 … k−1), the directions along which the class centres
                  spread most (between-class principal components), completed by the data's own."""
    X, y = np.asarray(X, float), np.asarray(y)
    if X.shape[1] < 3:
        raise ValueError('The 3-D view needs at least 3 features')
    mean = X.mean(axis=0)
    centred = X - mean
    total = float((centred ** 2).sum()) or 1.0
    labels = np.unique(y)
    if kind == 'separating' and not (len(labels) <= 2 and set(labels.tolist()) <= {-1, 1}):
        centres = np.array([X[y == c].mean(axis=0) for c in labels]) - mean
        _, spread, between = np.linalg.svd(centres, full_matrices=False)
        between = [v for v, size in zip(between, spread) if size > 1e-9 * max(1.0, spread[0])][:3]
        _, _, within = np.linalg.svd(centred, full_matrices=False)
        basis = []
        for v in between + list(within):                           # Gram–Schmidt: class spread first
            for b in basis:
                v = v - (v @ b) * b
            if np.linalg.norm(v) > 1e-9 and len(basis) < 3:
                basis.append(v / np.linalg.norm(v))
        basis = np.array(basis)
        m = len(between)
        names = [f'class spread {i + 1}' for i in range(m)] + [f'remaining PC{i + 1}' for i in range(3 - m)]
        short = [f'C{i + 1}' for i in range(m)] + [f'R{i + 1}' for i in range(3 - m)]
    elif kind == 'separating':
        d = X[y == 1].mean(axis=0) - X[y != 1].mean(axis=0)
        d = d / (np.linalg.norm(d) or 1.0)
        rest = centred - np.outer(centred @ d, d)
        _, _, vt = np.linalg.svd(rest, full_matrices=False)
        others = [v - (v @ d) * d for v in vt[:2]]
        basis = np.array([d] + [v / (np.linalg.norm(v) or 1.0) for v in others])
        names = ['class separation', 'separation PC1', 'separation PC2']
        short = ['Sep', 'S1', 'S2']
    elif kind == 'pca':
        _, _, vt = np.linalg.svd(centred, full_matrices=False)
        basis = vt[:3]
        names = ['PC1', 'PC2', 'PC3']
        short = names
    else:
        raise ValueError(f'Unknown axes {kind!r}')
    shares = [float(((centred @ b) ** 2).sum() / total) for b in basis]
    return dict(mean=mean, basis=basis, names=names, short=short, shares=shares, kind=kind)


def project(axes, X):
    """Coordinates of rows of X in the 3-D view."""
    return (np.asarray(X, float) - axes['mean']) @ axes['basis'].T


def lift(axes, P):
    """Points of the 3-D view back in the full feature space (the slice through the data's mean)."""
    return axes['mean'] + np.asarray(P, float) @ axes['basis']


def grid_resolution(features):
    """Grid points per axis: fewer at more qubits, where every point costs 2ⁿ amplitudes."""
    return 30 if features <= 4 else 24 if features <= 6 else 18 if features <= 8 else 14


def decision_grid(decision, axes, P_all, resolution, chunk=2000, cancelled=None):
    """The decision function on a cube around the projected data: (axis ticks ×3, values res³)."""
    lo, hi = P_all.min(axis=0), P_all.max(axis=0)
    pad = 0.1 * np.maximum(hi - lo, 1e-6)
    ticks = [np.linspace(lo[k] - pad[k], hi[k] + pad[k], resolution) for k in range(3)]
    gx, gy, gz = np.meshgrid(*ticks, indexing='ij')
    points = lift(axes, np.c_[gx.ravel(), gy.ravel(), gz.ravel()])
    values = None
    for start in range(0, len(points), chunk):
        if cancelled is not None and cancelled():
            return None
        part = np.asarray(decision(points[start:start + chunk]), float)
        if values is None:                                         # one column per class for k > 2
            values = np.empty((len(points),) + part.shape[1:])
        values[start:start + chunk] = part
    return ticks, values.reshape((resolution, resolution, resolution) + values.shape[1:])


def class_margins(values):
    """For decision values with one column per class (…, k): for each class, its value minus the
    largest of the others (…, k). Positive where the class wins; 0 on its region's boundary."""
    values = np.asarray(values, float)
    out = np.empty_like(values)
    for c in range(values.shape[-1]):
        others = np.delete(values, c, axis=-1)
        out[..., c] = values[..., c] - others.max(axis=-1)
    return out


def winners(values):
    """The predicted label for decision values: the sign (±1) for one value, else the largest column."""
    values = np.asarray(values, float)
    return np.argmax(values, axis=-1) if values.ndim > 1 else np.where(values >= 0, 1, -1)


def slice_agreement(decision, axes, X):
    """The share of points where the decision on the slice (at the point's projection) predicts the
    same class as the classifier's real decision at the point: how far to trust the drawn surface."""
    X = np.asarray(X, float)
    real = winners(decision(X))
    on_slice = winners(decision(lift(axes, project(axes, X))))
    return float(np.mean(real == on_slice))
