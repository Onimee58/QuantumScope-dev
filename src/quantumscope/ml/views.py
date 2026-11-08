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
