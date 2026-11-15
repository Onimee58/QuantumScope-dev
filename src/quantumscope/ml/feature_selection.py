"""Feature selection by annealing (v0.9.13): choose k features that predict the label well without
repeating each other, as the lowest-energy state of an Ising problem.

Each candidate feature is a spin: bit 1 (Z = −1) keeps it. The energy of a choice x ∈ {0, 1}ⁿ is

    E(x) = −α Σ rᵢ xᵢ + (1 − α) Σ_{i<j} Rᵢⱼ xᵢ xⱼ + λ (Σ xᵢ − k)²

rᵢ, the relevance, says how well feature i alone tells the classes apart (the correlation ratio η,
which is |correlation| with the label for two classes); Rᵢⱼ, the redundancy, is |correlation|
between features i and j; the penalty λ makes every choice of a size other than k cost more. This
is the QUBO formulation of, for example, Mücke et al. (2023), Quantum Machine Intelligence 5, 11.

Everything is computed from the training split only, so the test split stays unseen until the
choice is scored. No Qt here.
"""
from dataclasses import dataclass, field, replace
from itertools import combinations

import numpy as np

from quantumscope.ml import datasets as D
from quantumscope.physics import annealing as A

MAX_CANDIDATES = A.MAX_QUBITS          # one spin per candidate, and the simulation's spin limit
ALPHA = 0.7                            # relevance against redundancy: 1 = relevance only (greedy)


# ---- the two ingredients ------------------------------------------------------------------------
def relevance(X, y):
    """How well each feature alone separates the classes: the correlation ratio
    η = √(between-class variance / total variance), from 0 (no help) to 1 (separates perfectly).
    For two classes it equals |Pearson correlation| with the label."""
    X = np.asarray(X, float)
    y = np.asarray(y)
    total = X.var(axis=0)
    mean = X.mean(axis=0)
    between = np.zeros(X.shape[1])
    for c in np.unique(y):
        members = X[y == c]
        between += len(members) / len(X) * (members.mean(axis=0) - mean) ** 2
    with np.errstate(divide='ignore', invalid='ignore'):
        eta = np.sqrt(np.where(total > 0, between / total, 0.0))
    return np.clip(np.nan_to_num(eta), 0.0, 1.0)


def redundancy(X):
    """|Pearson correlation| between every pair of features (1 on the diagonal); 0 for a constant feature."""
    X = np.asarray(X, float)
    centred = X - X.mean(axis=0)
    norms = np.sqrt((centred ** 2).sum(axis=0))
    with np.errstate(divide='ignore', invalid='ignore'):
        R = np.abs(centred.T @ centred) / np.outer(norms, norms)
    R = np.nan_to_num(R)
    np.fill_diagonal(R, 1.0)
    return np.clip(R, 0.0, 1.0)


# ---- the task: data, candidates and settings ----------------------------------------------------
@dataclass
class Task:
    """A feature selection to anneal: the cleaned, split, unscaled data and the choices made."""
    source: str                        # where the data came from: a dataset key, 'imported' or 'store'
    title: str                         # the dataset's name, for people
    dataset: object                    # the Dataset (raw)
    recipe: object                     # the Datasets recipe the split was made with (select and PCA off)
    prepared: object                   # D.Prepared: X_train … unscaled, every cleaned feature
    relevance: np.ndarray              # of every cleaned feature, from the training split
    candidates: list = field(default_factory=list)   # indices of the candidate features (at most 10)
    k: int = 3
    alpha: float = ALPHA

    @property
    def names(self):
        return list(self.prepared.features)

    @property
    def candidate_names(self):
        return [self.names[i] for i in self.candidates]


def make_task(dataset, recipe, source, title, k=3, alpha=ALPHA, candidates=None):
    """Clean and split the data exactly as the Datasets tab would with `recipe` (same seed, so the
    same training rows), without scaling, PCA or a previous selection; then rank the features."""
    base = replace(recipe, components=0, scale='none', select=())
    prepared = D.prepare(dataset, base)
    if np.isnan(prepared.X_train).any() or np.isnan(prepared.X_test).any():
        raise ValueError('Some values are missing: choose Drop those samples or Fill with the mean first')
    if prepared.X_train.shape[1] < 2:
        raise ValueError('There is only one feature: there is nothing to choose from')
    rel = relevance(prepared.X_train, prepared.y_train)
    task = Task(source, title, dataset, base, prepared, rel, k=int(k), alpha=float(alpha))
    task.candidates = list(candidates) if candidates is not None else default_candidates(rel)
    check(task)
    return task


def default_candidates(rel, limit=MAX_CANDIDATES):
    """The `limit` features that are most relevant on their own, in their dataset order."""
    order = np.argsort(-np.asarray(rel), kind='stable')[:limit]
    return sorted(int(i) for i in order)


def check(task):
    n = len(task.candidates)
    if not 2 <= n <= MAX_CANDIDATES:
        raise ValueError(f'Choose 2 to {MAX_CANDIDATES} candidate features (one spin each); {n} are chosen')
    if not 1 <= task.k < n:
        raise ValueError(f'Keep between 1 and {n - 1} of the {n} candidates')
    if not 0 <= task.alpha <= 1:
        raise ValueError('α must be between 0 and 1')


# ---- the Ising problem -----------------------------------------------------------------------------
def qubo(rel, R, k, alpha, penalty):
    """E(x) = c + Σ hᵢ xᵢ + Σ_{i<j} Jᵢⱼ xᵢ xⱼ for x ∈ {0, 1}ⁿ: returns (c, h, J)."""
    h = -alpha * np.asarray(rel, float) + penalty * (1 - 2 * k)
    J = (1 - alpha) * np.asarray(R, float) + 2 * penalty
    J = np.triu(J, 1)
    return penalty * k * k, h, J


def ising_terms(c, h, J):
    """The same energy in spins: x = (1 − Z)/2, so bit 1 (Z = −1) keeps the feature."""
    n = len(h)
    constant = c + h.sum() / 2 + J.sum() / 4
    terms = [(constant, ())]
    for i in range(n):
        terms.append((-h[i] / 2 - (J[i].sum() + J[:, i].sum()) / 4, (i,)))
    for i, j in combinations(range(n), 2):
        if J[i, j]:
            terms.append((J[i, j] / 4, (i, j)))
    return terms


def penalty_for(rel, R, k, alpha):
    """A penalty λ large enough that adding or dropping one feature from any choice of k never lowers
    the energy: a safe upper bound (problem() then looks for a smaller one)."""
    R = np.asarray(R, float) - np.eye(len(rel))
    return float(max(alpha * np.max(rel), (1 - alpha) * np.max(R.sum(axis=1)))) + 0.05


MARGIN = 1.5                           # λ = this × the smallest penalty that keeps the answer at k


def _scaled(rel, R, k, alpha, penalty, n):
    terms = ising_terms(*qubo(rel, R, k, alpha, penalty))
    scale = max(abs(value) for value, qubits in terms if qubits)
    return [(value / scale, qubits) for value, qubits in terms]


def problem(task):
    """The annealing Problem for a task, scaled so its largest coefficient is 1 (like the other
    problems, so the same anneal times apply). Its answer keeps exactly k candidates.

    The penalty is kept as small as it can be: a large one makes every coefficient about the same
    size, so the differences between good and bad choices shrink and so does the gap. λ is MARGIN
    times the smallest value (found by bisection over all 2ⁿ energies) at which the lowest energy
    keeps exactly k."""
    check(task)
    c, k = task.candidates, task.k
    rel = task.relevance[c]
    R = redundancy(task.prepared.X_train[:, c])
    n = len(c)
    weights = np.array([bin(x).count('1') for x in range(1 << n)])

    def keeps_k(penalty):
        diagonal = A._diagonal(n, [(v, tuple(q)) for v, q in _scaled(rel, R, k, task.alpha, penalty, n)])
        return weights[int(np.argmin(diagonal))] == k and np.sum(diagonal <= diagonal.min() + 1e-9) == \
            np.sum((diagonal <= diagonal.min() + 1e-9) & (weights == k))
    low, high = 0.0, penalty_for(rel, R, k, task.alpha)
    if not keeps_k(high):
        raise ValueError('Could not make the lowest energy keep exactly k features')
    for _ in range(40):
        middle = (low + high) / 2
        low, high = (low, middle) if keeps_k(middle) else (middle, high)
    penalty = MARGIN * high
    label = f'Feature selection: {k} of {n} ({task.title})'
    result = A.from_terms(f'features-{task.source}-{k}-of-{n}', label, n, _scaled(rel, R, k, task.alpha, penalty, n))
    result.task, result.penalty = task, penalty
    return result


@dataclass
class Reads:
    """What `shots` measurements at the end of an anneal give, as a real annealer is used: run it
    many times and keep the best choice seen."""
    shots: int
    counts: dict                       # bitstring → how many reads gave it
    valid: int                         # reads that keep exactly k features
    hits: int                          # reads that gave the answer (the lowest-energy choice)
    best: str                          # the lowest-energy valid read, or '' if no read kept k
    rank: int                          # its place among all valid choices by energy (1 = the answer)
    choices: int                       # how many ways there are to keep k of the candidates


def read_out(problem, probabilities, shots=100, seed=0):
    """Sample `shots` bitstrings from final probabilities (over all 2ⁿ, qubit 0 first)."""
    n, k = problem.n, problem.task.k
    p = np.clip(np.asarray(probabilities, float), 0, None)
    draws = np.random.default_rng(seed).choice(len(p), size=int(shots), p=p / p.sum())
    values, counts = np.unique(draws, return_counts=True)
    strings = {format(int(v), f'0{n}b'): int(c) for v, c in zip(values, counts)}
    valid = {b: c for b, c in strings.items() if b.count('1') == k}
    answers = set(problem.solutions())
    order = sorted((x for x in range(1 << n) if bin(x).count('1') == k), key=lambda x: problem.diagonal[x])
    rank_of = {format(x, f'0{n}b'): r + 1 for r, x in enumerate(order)}
    best = min(valid, key=lambda b: problem.diagonal[int(b, 2)]) if valid else ''
    return Reads(int(shots), strings, sum(valid.values()), sum(c for b, c in strings.items() if b in answers),
                 best, rank_of.get(best, 0), len(order))


def subset(bits):
    """Candidate positions kept by a bitstring ('0110…': qubit 0 first; 1 keeps)."""
    return [i for i, b in enumerate(bits) if b == '1']


def energy(task, positions):
    """E(x) (unscaled) of keeping these candidate positions."""
    c = task.candidates
    rel = task.relevance[c]
    R = redundancy(task.prepared.X_train[:, c])
    x = np.zeros(len(c))
    x[list(positions)] = 1
    pair = float(x @ np.triu(R, 1) @ x)
    return float(-task.alpha * rel @ x + (1 - task.alpha) * pair)


# ---- other ways to choose, and scoring ---------------------------------------------------------------
def greedy(task):
    """Candidate positions of the k most relevant candidates on their own (α = 1)."""
    rel = task.relevance[task.candidates]
    return sorted(int(i) for i in np.argsort(-rel, kind='stable')[:task.k])


def score(task, columns=None, pca=0, regularization=0.1):
    """Test accuracy of a classical classifier (Gaussian-kernel ridge, one-vs-rest for more classes)
    on some features: `columns` (indices into every cleaned feature) or the first `pca` principal
    components of all of them. Standardized with the training split's statistics; γ = 1/(features)."""
    from quantumscope.ml import kernels as K
    p = task.prepared
    if pca:
        mean = p.X_train.mean(axis=0)
        _, _, vt = np.linalg.svd(p.X_train - mean, full_matrices=False)
        Xtr, Xte = (p.X_train - mean) @ vt[:pca].T, (p.X_test - mean) @ vt[:pca].T
    else:
        Xtr, Xte = p.X_train[:, columns], p.X_test[:, columns]
    mean, spread = Xtr.mean(axis=0), Xtr.std(axis=0)
    spread = np.where(spread > 0, spread, 1.0)
    Xtr, Xte = (Xtr - mean) / spread, (Xte - mean) / spread
    gamma = 1.0 / Xtr.shape[1]
    model = K.classifier('ridge', regularization, K.classes_in(p.y_train))
    model.fit(K.rbf(Xtr, gamma=gamma), p.y_train)
    return K.accuracy(p.y_test, model.predict(K.rbf(Xte, Xtr, gamma=gamma)))


@dataclass
class Row:
    method: str
    features: list                     # names (or a description, for PCA)
    accuracy: float
    redundancy: float = float('nan')   # mean |correlation| between the kept features


def compare(task, positions):
    """The annealed choice (candidate positions) against the other ways to reduce to k features."""
    c = task.candidates
    names = task.names

    def row(method, kept):
        columns = [c[i] for i in kept]
        R = redundancy(task.prepared.X_train[:, columns])
        mean_r = float(R[np.triu_indices(len(columns), 1)].mean()) if len(columns) > 1 else 0.0
        return Row(method, [names[i] for i in columns], score(task, columns), mean_r)
    rows = [row('Annealed', positions), row('Most relevant alone (greedy)', greedy(task))]
    rows.append(Row(f'PCA ({task.k} components of all {len(names)})', [f'PC1 … PC{task.k}'],
                    score(task, pca=task.k)))
    rows.append(Row(f'All {len(c)} candidates', [names[i] for i in c], score(task, list(c))))
    return rows
