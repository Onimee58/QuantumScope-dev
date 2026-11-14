"""Quantum kernels and kernel classifiers (NumPy only, no Qt).

A feature map turns a data point x into a quantum state |φ(x)⟩; the quantum kernel is
K(x, x′) = |⟨φ(x)|φ(x′)⟩|², the overlap of two such states. A classical method (kernel ridge, or a
support vector machine) then separates the classes using only these overlaps.

Feature maps (one feature per qubit):
  angle — RY(xᵢ) on qubit i: a product state, K = ∏ cos²((xᵢ − x′ᵢ)/2).
  zz    — the ZZ feature map of Havlíček et al. (2019): reps × [H on every qubit, then
          exp(i Σᵢ xᵢ Zᵢ + i Σᵢ<ⱼ (π − xᵢ)(π − xⱼ) Zᵢ Zⱼ)], here with all-to-all pairs.
A bandwidth b scales the data first (x → b·x): small b makes the kernel smoother, which often
generalizes better (Shaydulin & Wild, 2022; Canatar et al., 2023).
On a quantum computer each kernel entry is estimated from shots (the share of all-zero results of
the circuit U(x′)† U(x)), so it carries statistical noise; estimate() reproduces that.
"""
import math

import numpy as np

from quantumscope.physics.circuits import Gate

from quantumscope import caching

FEATURE_MAPS = {'angle': 'Angle encoding (RY on each qubit)', 'zz': 'ZZ feature map (entangling)'}


def _zz_phases(x):
    """φᵢ = xᵢ and φᵢⱼ = (π − xᵢ)(π − xⱼ) for every pair i < j."""
    n = len(x)
    pairs = [(i, j, (math.pi - x[i]) * (math.pi - x[j])) for i in range(n) for j in range(i + 1, n)]
    return [(i, x[i]) for i in range(n)], pairs


def circuit(x, kind='zz', reps=2, bandwidth=1.0):
    """The feature-map circuit for one data point, as gates for the circuit simulator.
    exp(iφZ) is RZ(−2φ), and exp(iφ ZᵢZⱼ) is CX(i→j), RZ(−2φ) on j, CX(i→j)."""
    x = [float(v) * bandwidth for v in x]
    n = len(x)
    if kind == 'angle':
        return [Gate('RY', (i,), x[i]) for i in range(n)]
    if kind != 'zz':
        raise ValueError(f'Unknown feature map {kind!r}')
    gates = []
    for _ in range(max(1, int(reps))):
        gates += [Gate('H', (i,)) for i in range(n)]
        singles, pairs = _zz_phases(x)
        gates += [Gate('RZ', (i,), -2 * phi) for i, phi in singles]
        for i, j, phi in pairs:
            gates += [Gate('CX', (i, j)), Gate('RZ', (j,), -2 * phi), Gate('CX', (i, j))]
    return gates


def _z_values(n):
    """zₖ = ±1 for every basis state, q0 as the most significant bit (as in the simulator)."""
    index = np.arange(2 ** n)
    return np.array([1 - 2 * ((index >> (n - 1 - k)) & 1) for k in range(n)], float)   # n × 2ⁿ


def states(X, kind='zz', reps=2, bandwidth=1.0):
    """|φ(x)⟩ for every row of X: an array of shape (samples, 2ⁿ)."""
    X = np.atleast_2d(np.asarray(X, float)) * bandwidth
    samples, n = X.shape
    if kind == 'angle':
        out = np.ones((samples, 1), complex)
        for k in range(n):
            qubit = np.stack([np.cos(X[:, k] / 2), np.sin(X[:, k] / 2)], axis=1)
            out = np.einsum('si,sj->sij', out, qubit).reshape(samples, -1)
        return out
    if kind != 'zz':
        raise ValueError(f'Unknown feature map {kind!r}')
    z = _z_values(n)
    i, j = np.triu_indices(n, 1)                                         # every pair i < j at once:
    pairs = (math.pi - X)[:, i] * (math.pi - X)[:, j]                    # (π − xᵢ)(π − xⱼ) …
    phase = X @ z + pairs @ (z[i] * z[j])                                # … times zᵢzⱼ, as one product
    diagonal = np.exp(1j * phase)                                        # samples × 2ⁿ
    state = diagonal / math.sqrt(2 ** n)                                 # H⊗ⁿ|0…0⟩ is uniform: no transform
    for _ in range(max(1, int(reps)) - 1):
        state = hadamard_all(state, n) * diagonal
    return state


def hadamard_all(states, n):
    """H on every qubit of each state (rows): the fast Walsh–Hadamard transform, n·2ⁿ operations per
    state instead of the 4ⁿ of multiplying by the full H⊗ⁿ matrix (about 100× fewer at 10 qubits)."""
    out = np.array(states, complex)
    samples = len(out)
    for k in range(n):                                                   # one butterfly layer per qubit
        view = out.reshape(samples, 2 ** k, 2, 2 ** (n - k - 1))
        zero, one = view[:, :, 0, :].copy(), view[:, :, 1, :]
        view[:, :, 0, :] += one
        view[:, :, 1, :] = zero - one
    return out / math.sqrt(2 ** n)


def kernel(A, B=None, kind='zz', reps=2, bandwidth=1.0):
    """K[a, b] = |⟨φ(A[a])|φ(B[b])⟩|² (B defaults to A). Remembered (0.9.10): retraining with another
    C or λ, and Search, ask for the same matrices again. The result is read-only; copy it to change it."""
    A = np.asarray(A, float)
    key = (caching.fingerprint(A), None if B is None else caching.fingerprint(np.asarray(B, float)),
           kind, int(reps), float(bandwidth))

    def compute():
        SA = states(A, kind, reps, bandwidth)
        SB = SA if B is None else states(B, kind, reps, bandwidth)
        return np.abs(SA.conj() @ SB.T) ** 2
    return KERNELS.get(key, compute)


KERNELS = caching.Cache('kernel matrices', 256 * caching.MB, entries=24)


def estimate(K, shots, rng=None, symmetric=False):
    """K as a quantum computer would estimate it: each entry from `shots` runs (the share of
    all-zero results). symmetric: a training kernel, with its diagonal exactly 1 (no circuit needed)."""
    rng = rng or np.random.default_rng()
    if not shots:
        return np.array(K, float)
    noisy = rng.binomial(int(shots), np.clip(K, 0, 1)) / int(shots)
    if symmetric:
        upper = np.triu(noisy, 1)
        noisy = upper + upper.T + np.eye(len(K))
    return noisy


def rbf(A, B=None, gamma=1.0):
    """The classical Gaussian (RBF) kernel exp(−γ |a − b|²), for comparison."""
    A = np.atleast_2d(np.asarray(A, float))
    B = A if B is None else np.atleast_2d(np.asarray(B, float))
    d2 = (A ** 2).sum(1)[:, None] + (B ** 2).sum(1)[None, :] - 2 * A @ B.T
    return np.exp(-gamma * np.clip(d2, 0, None))


def accuracy(y_true, y_pred):
    return float(np.mean(np.asarray(y_true) == np.asarray(y_pred)))


class KernelRidge:
    """Kernel ridge classification: α = (K + λI)⁻¹ y, f(x) = Σ αᵢ K(x, xᵢ), label sign(f)."""

    def __init__(self, regularization=0.1):
        self.regularization = float(regularization)

    def fit(self, K, y):
        y = np.asarray(y, float)
        self.alpha = np.linalg.solve(K + self.regularization * np.eye(len(y)), y)
        return self

    def decision(self, K_test):
        """K_test: test × training kernel."""
        return K_test @ self.alpha

    def predict(self, K_test):
        return np.where(self.decision(K_test) >= 0, 1, -1)


class SVM:
    """A support vector machine for a precomputed kernel, trained with Platt's SMO algorithm.

    It solves  max Σαᵢ − ½ ΣΣ αᵢαⱼ yᵢyⱼ Kᵢⱼ  with 0 ≤ αᵢ ≤ C and Σ αᵢ yᵢ = 0;
    the decision is f(x) = Σ αᵢ yᵢ K(x, xᵢ) + b. Points with αᵢ > 0 are the support vectors.
    """

    def __init__(self, C=1.0, tolerance=1e-4, max_passes=200, seed=0):
        self.C, self.tolerance, self.max_passes, self.seed = float(C), tolerance, max_passes, seed   # seed: kept for compatibility

    def _step(self, i, j):
        """Optimize the pair (αᵢ, αⱼ) analytically; update the error cache E (fᵢ − yᵢ for every point)."""
        if i == j:
            return False
        C, K, y, a, E = self.C, self.K, self.y, self.alpha, self.E
        if y[i] != y[j]:
            low, high = max(0.0, a[j] - a[i]), min(C, C + a[j] - a[i])
        else:
            low, high = max(0.0, a[i] + a[j] - C), min(C, a[i] + a[j])
        if high - low < 1e-12:
            return False
        eta = K[i, i] + K[j, j] - 2 * K[i, j]
        if eta <= 1e-12:                                                 # flat direction: skip this pair
            return False
        aj = float(np.clip(a[j] + y[j] * (E[i] - E[j]) / eta, low, high))
        if abs(aj - a[j]) < 1e-10:
            return False
        ai = a[i] + y[i] * y[j] * (a[j] - aj)
        snap = 1e-12 * max(1.0, C)                                       # rounding leftovers sit on the bound
        ai = 0.0 if ai < snap else C if ai > C - snap else ai
        aj = 0.0 if aj < snap else C if aj > C - snap else aj
        di, dj = ai - a[i], aj - a[j]
        b1 = self.b - E[i] - y[i] * di * K[i, i] - y[j] * dj * K[i, j]
        b2 = self.b - E[j] - y[i] * di * K[i, j] - y[j] * dj * K[j, j]
        b_new = b1 if 0 < ai < C else b2 if 0 < aj < C else (b1 + b2) / 2
        E += y[i] * di * K[i] + y[j] * dj * K[j] + (b_new - self.b)       # O(N) instead of recomputing
        a[i], a[j], self.b = ai, aj, b_new
        return True

    def fit(self, K, y):
        """SMO with the maximal-violating-pair choice (as in LIBSVM): each iteration picks, in one
        vectorized search, the two points that most violate the optimality conditions, and stops when
        even that pair violates them by less than the tolerance."""
        self.K, self.y = np.asarray(K, float), np.asarray(y, float)
        m = len(self.y)
        self.alpha, self.b = np.zeros(m), 0.0
        self.E = -self.y.copy()                                         # f = 0 at the start
        C, y, a = self.C, self.y, self.alpha
        for _ in range(self.max_passes * m):
            eps = 1e-12 * max(1.0, C)
            up = ((y > 0) & (a < C - eps)) | ((y < 0) & (a > eps))      # αᵢyᵢ can increase
            low = ((y < 0) & (a < C - eps)) | ((y > 0) & (a > eps))     # αⱼyⱼ can decrease
            if not up.any() or not low.any():
                break
            i = int(np.flatnonzero(up)[np.argmin(self.E[up])])
            j = int(np.flatnonzero(low)[np.argmax(self.E[low])])
            if self.E[j] - self.E[i] < 2 * self.tolerance:              # optimal within the tolerance
                break
            if not self._step(i, j) and not self._step(j, i):           # no progress possible on this pair
                break
        self.support = np.flatnonzero(self.alpha > 1e-8)
        free = [k for k in self.support if self.alpha[k] < C - 1e-8]
        if free:                                                         # b from the margin's points
            self.b = float(np.mean([self.y[k] - (self.alpha * self.y) @ self.K[:, k] for k in free]))
        return self

    def dual_objective(self):
        ay = self.alpha * self.y
        return float(self.alpha.sum() - 0.5 * ay @ self.K @ ay)

    def decision(self, K_test):
        """K_test: test × training kernel."""
        return K_test @ (self.alpha * self.y) + self.b

    def predict(self, K_test):
        return np.where(self.decision(K_test) >= 0, 1, -1)


class OneVsRest:
    """Any number of classes (v0.9.3): one binary classifier per class, "this class (+1) or any other
    (−1)", all sharing one kernel matrix, so k classes cost k cheap fits but no extra circuits. Labels
    are 0 … k−1; the prediction is the class whose classifier is most confident (largest decision)."""

    def __init__(self, make_model, k):
        self.make_model, self.k = make_model, int(k)

    def fit(self, K, y):
        y = np.asarray(y)
        self.models = [self.make_model().fit(K, np.where(y == c, 1, -1)) for c in range(self.k)]
        return self

    @property
    def support(self):
        """Training points used by at least one of the classifiers."""
        used = [np.flatnonzero(np.abs(m.alpha) > 1e-8) for m in self.models]
        return np.unique(np.concatenate(used)) if used else np.array([], int)

    def decision(self, K_test):
        """test × k decision values, one column per class."""
        return np.column_stack([m.decision(K_test) for m in self.models])

    def predict(self, K_test):
        return np.argmax(self.decision(K_test), axis=1)


def classifier(method, strength, k=2):
    """A fresh classifier: 'svm' (C = strength) or 'ridge' (λ = strength), one-vs-rest when k > 2."""
    make = (lambda: SVM(C=strength)) if method == 'svm' else (lambda: KernelRidge(strength))
    return make() if k <= 2 else OneVsRest(make, k)


def classes_in(y):
    """The number of classes behind labels: 2 for ±1 labels, else max + 1 (labels 0 … k−1)."""
    y = np.asarray(y)
    return 2 if np.all(np.isin(y, (-1, 1))) and np.any(y == -1) else int(y.max()) + 1
