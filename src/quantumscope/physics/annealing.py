"""Quantum annealing, simulated exactly (v0.9.2, no Qt).

The anneal follows H(s) = (1 − s)·H_d + s·H_p as s goes from 0 to 1 over a time T (ħ = 1):
H_d = −Σ X_i is the driver, whose ground state |+…+⟩ is easy to prepare, and H_p is the problem,
diagonal (an Ising Hamiltonian of Z terms), whose ground states are the answers. If the change is
slow compared with the gap Δ between the ground state and the first excited state that matters, the
state stays in the ground state (the adiabatic theorem), so it ends on an answer.

Symmetry. When every term of H_p has an even number of Z's (MaxCut, number partitioning), flipping
every spin changes nothing; H_d shares the symmetry and |+…+⟩ has it, so the state never leaves the
symmetric sector, spanned by (|x⟩ + |x̄⟩)/√2. Gaps are computed there: the gap to an antisymmetric
state, which closes at s = 1, can never be crossed. Working in the sector also halves the cost.
"""
import math
from dataclasses import dataclass, field

import numpy as np

MAX_QUBITS = 10


@dataclass
class Problem:
    key: str
    label: str
    n: int
    observable: str                   # H_p as a Pauli sum (for the circuit simulator)
    terms: list                       # [(coefficient, (qubit, …))]: Z on each listed qubit
    diagonal: np.ndarray = field(repr=False, default=None)   # E(x) for every bitstring x (qubit 0 first)
    tolerance: float = 1e-9           # answers: every bitstring within this of the lowest energy
                                      # (v0.9.13: feature selection counts near-best choices as answers)

    @property
    def symmetric(self):
        """Whether H_p is unchanged when every spin flips (every term has an even number of Z's)."""
        return all(len(qubits) % 2 == 0 for _, qubits in self.terms)

    @property
    def ground_energy(self):
        return float(self.diagonal.min())

    def solutions(self, tolerance=None):
        """The bitstrings of lowest energy (within the problem's tolerance)."""
        best = self.ground_energy
        tolerance = self.tolerance if tolerance is None else tolerance
        return [format(x, f'0{self.n}b') for x in np.flatnonzero(self.diagonal <= best + tolerance)]


def _diagonal(n, terms):
    x = np.arange(1 << n)
    spins = 1 - 2 * ((x[:, None] >> (n - 1 - np.arange(n))) & 1)          # Z eigenvalue of each qubit
    out = np.zeros(1 << n)
    for coefficient, qubits in terms:
        out += coefficient * (np.prod(spins[:, list(qubits)], axis=1) if qubits else 1.0)
    return out


def _text(terms):
    parts = []
    for coefficient, qubits in terms:
        word = ' '.join(f'Z{q}' for q in qubits)
        parts.append(f'{coefficient:+g}' + (f' {word}' if word else ''))
    text = ' '.join(parts).lstrip('+')
    return text.replace(' +', ' + ').replace(' -', ' - ').strip()


def from_terms(key, label, n, terms):
    if not 1 <= n <= MAX_QUBITS:
        raise ValueError(f'Annealing is simulated for 1 to {MAX_QUBITS} spins')
    terms = [(float(c), tuple(sorted(q))) for c, q in terms if abs(c) > 1e-15]
    return Problem(key, label, n, _text(terms), terms, _diagonal(n, terms))


def maxcut(graph):
    """MaxCut on one of the QAOA graphs: H_p = Σ ½(Z_i Z_j − 1) = −(cut size)."""
    from quantumscope.physics.maxcut import GRAPHS
    label, n, edges, _ = GRAPHS[graph]
    terms = [(0.5, (i, j)) for i, j in edges] + [(-0.5 * len(edges), ())]
    return from_terms(f'maxcut-{graph}', f'MaxCut: {label.lower()}', n, terms)


def spin_glass(n, seed=0):
    """A random spin glass: couplings ±1 between every pair, and random fields of 0.1 to 0.3 (which make
    the answer unique). Frustrated: no assignment satisfies every coupling. Instances whose best and
    second-best energies differ by less than 0.2 are skipped: a near-tie at the end would make the gap
    vanish at s = 1 for a reason that has nothing to do with the anneal."""
    rng = np.random.default_rng(seed)
    for _ in range(100):
        terms = [(float(rng.choice((-1.0, 1.0))), (i, j)) for i in range(n) for j in range(i + 1, n)]
        terms += [(round(float(rng.choice((-1, 1)) * rng.uniform(0.1, 0.3)), 2), (i,)) for i in range(n)]
        problem = from_terms(f'glass-{n}-{seed}', f'Spin glass, {n} spins (instance {seed})', n, terms)
        energies = np.unique(np.round(problem.diagonal, 9))
        if len(energies) > 1 and energies[1] - energies[0] >= 0.2:
            return problem
    return problem


def partition(numbers):
    """Number partitioning: split the numbers into two groups of equal sum. H_p = (Σ a_i Z_i)² is 0
    exactly for a perfect split (Z_i = ±1 says which group)."""
    a = [float(v) for v in numbers]
    n = len(a)
    terms = [(sum(v * v for v in a), ())] + [(2 * a[i] * a[j], (i, j)) for i in range(n) for j in range(i + 1, n)]
    return from_terms('partition-' + '-'.join(f'{v:g}' for v in a),
                      'Number partitioning: ' + ', '.join(f'{v:g}' for v in a), n, terms)


def from_text(text, n):
    """An Ising problem typed as a Pauli sum of Z terms, e.g. 'Z0 Z1 - 0.5 Z2 + 1'."""
    from quantumscope.physics.observables import parse
    terms = []
    for coefficient, ops in parse(text, n):
        if any(p != 'Z' for _, p in ops):
            raise ValueError('An annealing problem may only contain Z terms (it must be diagonal); '
                             'X and Y terms belong to the driver')
        terms.append((float(np.real(coefficient)), tuple(q for q, _ in ops)))
    return from_terms('custom', 'Your Ising problem', n, terms)


# ---- the operators, in the sector the anneal can reach --------------------------------------------
@dataclass
class Space:
    """The basis the anneal evolves in: every bitstring, or the symmetric pairs (|x⟩ + |x̄⟩)/√2
    represented by x with qubit 0 = 0."""
    problem: Problem
    representatives: np.ndarray       # bitstrings (as integers)
    driver: object                    # H_d, a sparse matrix in this basis
    energies: np.ndarray              # H_p's diagonal in this basis
    symmetric: bool

    @property
    def dimension(self):
        return len(self.representatives)

    def hamiltonian(self, s):
        import scipy.sparse as sp
        return (1 - s) * self.driver + s * sp.diags(self.energies)

    def start(self):
        """|+…+⟩: the driver's ground state (uniform; it is symmetric)."""
        return np.full(self.dimension, 1 / math.sqrt(self.dimension), complex)

    def probabilities(self, state):
        """{bitstring: probability} over every n-bit string."""
        n = self.problem.n
        p = np.abs(state) ** 2
        out = np.zeros(1 << n)
        if self.symmetric:
            out[self.representatives] = p / 2
            out[self.representatives ^ ((1 << n) - 1)] = p / 2
        else:
            out[self.representatives] = p
        return out

    def success(self, state):
        """The probability of measuring an answer (any lowest-energy bitstring)."""
        best = self.energies.min()
        return float(np.sum(np.abs(state[self.energies <= best + self.problem.tolerance]) ** 2))


def space(problem):
    import scipy.sparse as sp
    n = problem.n
    full = (1 << n) - 1
    if problem.symmetric and n > 1:
        reps = np.arange(1 << (n - 1))                       # qubit 0 (the most significant bit) is 0
        index = {int(x): k for k, x in enumerate(reps)}
        rows, cols = [], []
        for k, x in enumerate(reps):
            for q in range(n):
                y = int(x) ^ (1 << (n - 1 - q))
                y = y if y < (1 << (n - 1)) else y ^ full     # its pair's representative
                rows.append(index[y])
                cols.append(k)
        driver = -sp.csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(len(reps),) * 2)
        return Space(problem, reps, driver, problem.diagonal[reps], True)
    reps = np.arange(1 << n)
    rows = [int(x) ^ (1 << (n - 1 - q)) for x in reps for q in range(n)]
    cols = [int(x) for x in reps for _ in range(n)]
    driver = -sp.csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(len(reps),) * 2)
    return Space(problem, reps, driver, problem.diagonal.copy(), False)


def _lowest(space_, s, k):
    """The k lowest eigenvalues and eigenvectors of H(s) (dense when small, else Lanczos)."""
    H = space_.hamiltonian(s)
    if space_.dimension <= 256 or k >= space_.dimension - 1:
        values, vectors = np.linalg.eigh(H.toarray())
        return values[:k], vectors[:, :k]
    from scipy.sparse.linalg import eigsh
    values, vectors = eigsh(H, k=k, which='SA', tol=1e-10, v0=space_.start().real)
    order = np.argsort(values)
    return values[order], vectors[:, order]


@dataclass
class Spectrum:
    s: np.ndarray
    levels: np.ndarray                # points × k: the lowest energies of H(s), in the reachable sector
    gap: np.ndarray                   # the gap that matters (see `degeneracy`)
    degeneracy: int                   # g: how many sector states end as answers; the gap is E_g − E_0
    minimum_gap: float
    minimum_at: float                 # s at the minimum gap
    adiabatic_time: float             # T* = max over s of |⟨g|∂H/∂s|0⟩| / Δ(s)²
    symmetric: bool


def spectrum(problem, points=101, levels=6):
    """The lowest levels of H(s) for s from 0 to 1, the minimum gap, and the adiabatic time scale."""
    sp_ = space(problem)
    best = sp_.energies.min()
    g = int(np.sum(sp_.energies <= best + problem.tolerance))  # states that end as answers
    if g >= sp_.dimension:
        raise ValueError('Every bitstring is an answer: there is nothing to anneal')
    k = min(sp_.dimension, max(levels, g + 1))
    s_values = np.linspace(0, 1, points)
    out, gaps, speeds = np.zeros((points, k)), np.zeros(points), np.zeros(points)
    dH = sp_.hamiltonian(1) - sp_.hamiltonian(0)               # ∂H/∂s = H_p − H_d
    for i, s in enumerate(s_values):
        values, vectors = _lowest(sp_, s, k)
        out[i] = values
        gaps[i] = values[g] - values[0]
        speeds[i] = abs(np.vdot(vectors[:, g], dH @ vectors[:, 0]))
    m = int(np.argmin(gaps))

    def gap_at(s):
        values, vectors = _lowest(sp_, s, g + 1)
        return values[g] - values[0], abs(np.vdot(vectors[:, g], dH @ vectors[:, 0]))
    # An avoided crossing can be much narrower than the grid: refine the minimum between its neighbours.
    from scipy.optimize import minimize_scalar
    lo, hi = s_values[max(m - 1, 0)], s_values[min(m + 1, points - 1)]
    found = minimize_scalar(lambda s: gap_at(s)[0], bounds=(lo, hi), method='bounded', options=dict(xatol=1e-7))
    minimum_gap, minimum_at = float(gaps[m]), float(s_values[m])
    if found.success and found.fun < minimum_gap:
        minimum_gap, minimum_at = float(found.fun), float(found.x)
    speed = gap_at(minimum_at)[1]
    with np.errstate(divide='ignore'):
        T_star = float(np.max(np.append(speeds / np.maximum(gaps, 1e-12) ** 2, speed / max(minimum_gap, 1e-12) ** 2)))
    return Spectrum(s_values, out, gaps, g, minimum_gap, minimum_at, T_star, sp_.symmetric)


@dataclass
class Anneal:
    T: float
    s: np.ndarray                     # the recorded points
    success: np.ndarray               # P(answer) at each recorded point (in the computational basis)
    ground_overlap: np.ndarray        # |⟨E_0(s)|ψ⟩|²: how adiabatic the evolution has been
    probabilities: np.ndarray         # points × 2^n: P(bitstring) at each recorded point
    final_success: float


def anneal(problem, T, slices=None, record=41, ground=True, cancelled=None):
    """Evolve |+…+⟩ under H(s = t/T) for a time T: the Hamiltonian is held constant over each of
    `slices` short intervals (at its midpoint) and each interval is exponentiated exactly. Records the
    state at `record` points. ground=False skips the instantaneous ground states (faster)."""
    from scipy.sparse.linalg import expm_multiply
    if T <= 0:
        raise ValueError('The anneal time must be positive')
    sp_ = space(problem)
    slices = slices or int(max(200, 20 * T))
    checkpoints = set(np.round(np.linspace(0, slices, record)).astype(int))
    state = sp_.start()
    s_out, succ, overlap, probs = [], [], [], []

    def note(k):
        s = k / slices
        s_out.append(s)
        succ.append(sp_.success(state))
        probs.append(sp_.probabilities(state))
        if ground:
            vector = _lowest(sp_, s, 1)[1][:, 0]
            overlap.append(float(abs(np.vdot(vector, state)) ** 2))
    note(0)
    dt = T / slices
    for k in range(slices):
        if cancelled is not None and k % 50 == 0 and cancelled():
            return None
        state = expm_multiply(-1j * dt * sp_.hamiltonian((k + 0.5) / slices), state)
        if k + 1 in checkpoints:
            note(k + 1)
    return Anneal(T, np.array(s_out), np.array(succ), np.array(overlap) if ground else None, np.array(probs),
                  float(succ[-1]))


def success_curve(problem, times, cancelled=None, progress=None):
    """P(answer) at the end of anneals of each duration T."""
    out = []
    for i, T in enumerate(times):
        result = anneal(problem, T, record=2, ground=False, cancelled=cancelled)
        if result is None:
            return None
        out.append(result.final_success)
        if progress is not None:
            progress(i + 1, len(times))
    return np.array(out)


# ---- the anneal as a circuit (digitized annealing) -------------------------------------------------
def circuit(problem, T, steps):
    """The anneal split into `steps` slices, each a problem step exp(−i·dt·s·H_p) and a driver step
    exp(−i·dt·(1 − s)·H_d) (first-order Trotter): H on every qubit, then per slice RZ (Z terms),
    CX–RZ–CX (ZZ terms; a CX ladder for longer ones) and RX(−2·dt·(1 − s)). QAOA has exactly this
    structure, with the angles free to be optimized instead of fixed by the schedule.
    Returns a list of physics.circuits.Gate."""
    from quantumscope.physics.circuits import Gate
    n, dt = problem.n, T / steps
    gates = [Gate('H', (q,)) for q in range(n)]
    for r in range(steps):
        s = (r + 0.5) / steps
        for coefficient, qubits in problem.terms:
            if not qubits:
                continue                                      # a constant: only a global phase
            angle = 2 * dt * s * coefficient                  # exp(−i a Z…Z) = parity, RZ(2a), parity
            ladder = [Gate('CX', (qubits[k], qubits[k + 1])) for k in range(len(qubits) - 1)]
            gates += ladder + [Gate('RZ', (qubits[-1],), angle)] + ladder[::-1]
        gates += [Gate('RX', (q,), -2 * dt * (1 - s)) for q in range(n)]
    return gates


def circuit_state(problem, T, steps):
    """The final state of circuit(...), from |0…0⟩ (to compare with the exact anneal)."""
    from quantumscope.physics.circuits import apply_gate
    state = np.zeros(1 << problem.n, complex)
    state[0] = 1
    for gate in circuit(problem, T, steps):
        state = apply_gate(state, problem.n, gate)
    return state


PROBLEMS = (('MaxCut: square (4 nodes)', 'maxcut:ring4'), ('MaxCut: square with a diagonal', 'maxcut:diamond'),
            ('MaxCut: pentagon (odd)', 'maxcut:ring5'), ('MaxCut: hexagon', 'maxcut:ring6'),
            ('MaxCut: triangular prism', 'maxcut:prism'), ('Spin glass (frustrated)', 'glass'),
            ('Number partitioning', 'partition'), ('Your Ising problem', 'custom'),
            ('Feature selection (from data)', 'features'))        # v0.9.13: built from a dataset (ml.feature_selection)


def build(key, n=5, seed=0, numbers=(4, 5, 6, 7, 8), text=''):
    """A problem from its key in PROBLEMS and the options that kind uses."""
    if key.startswith('maxcut:'):
        return maxcut(key.split(':', 1)[1])
    if key == 'glass':
        return spin_glass(int(n), int(seed))
    if key == 'partition':
        return partition(numbers)
    if key == 'custom':
        return from_text(text, int(n))
    if key == 'features':
        raise ValueError('Feature selection is built from a dataset: see quantumscope.ml.feature_selection')
    raise ValueError(f'Unknown problem {key!r}')
