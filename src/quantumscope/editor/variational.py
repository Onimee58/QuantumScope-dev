"""Optimizing circuit parameters (Qt-free): energies, parameter-shift gradients, landscapes.

Every gate a parameter is bound to (RX, RY, RZ, P, CP and U angles) has a generator with
eigenvalue gap 1, so the exact parameter-shift rule applies to each occurrence:
    ∂E/∂g = [E(g + π/2) − E(g − π/2)] / 2,
and a parameter's gradient is the sum over its gates, each times its factor.

v0.8.1: for noiseless circuits the gradient comes from the adjoint method instead (Jones & Gacon,
2020): one forward pass and one backward pass give every derivative at once, where the shift rule
needs two full circuit runs per bound gate (72 for the 6-qubit, 3-layer QAOA example). Each bound
gate's exact matrix derivative is used (gate_derivative). Noisy and dynamic circuits, simulated
with density matrices, keep the parameter-shift rule. Both give the same numbers.
"""
import copy
import math

import numpy as np

from quantumscope.physics.circuits import Gate, apply_gate, apply_matrix, gate_matrix
from quantumscope.physics.observables import _apply_term, expectation, ground_energy, parse


def gate_derivative(gate, field):
    """∂U/∂field for a parameterized gate (exact): RX, RY, RZ, P, CP (field 'angle') and U ('angle',
    'phi', 'lam'). The matrix acts on the gate's own targets, like gate_matrix."""
    name, a = gate.name.upper(), gate.angle
    if name in ('RX', 'RY', 'RZ') and field == 'angle':
        pauli = {'RX': np.array([[0, 1], [1, 0]]), 'RY': np.array([[0, -1j], [1j, 0]]),
                 'RZ': np.diag([1, -1])}[name]
        return -0.5j * pauli @ gate_matrix(gate)                  # U = exp(−iθP/2)
    if name == 'P' and field == 'angle':
        return np.diag([0, 1j * np.exp(1j * a)])
    if name == 'CP' and field == 'angle':
        return np.diag([0, 0, 0, 1j * np.exp(1j * a)])
    if name == 'U':
        c, s, ep, el = math.cos(a / 2), math.sin(a / 2), np.exp(1j * gate.phi), np.exp(1j * gate.lam)
        if field == 'angle':
            return 0.5 * np.array([[-s, -el * c], [ep * c, -ep * el * s]])
        if field == 'phi':
            return np.array([[0, 0], [1j * ep * s, 1j * ep * el * c]])
        if field == 'lam':
            return np.array([[0, -1j * el * s], [0, 1j * ep * el * c]])
    raise ValueError(f'No derivative for {gate.name} with respect to {field}')


class Evaluator:
    """Fast ⟨H⟩ for a model at different parameter values, without touching the model."""

    def __init__(self, model):
        if not model.observable:
            raise ValueError('Set an observable first (for example a Hamiltonian).')
        if not model.parameters:
            raise ValueError('The circuit has no parameters to optimize.')
        self.model = copy.deepcopy(model)
        self.names = list(model.parameters)
        self.terms = parse(model.observable, model.n)
        self.calls = 0
        self.adjoint = not model.noisy                             # pure states: one forward + one backward pass
        self._last = None                                          # (values, energy) of the latest evaluation

    def energy(self, values, shift=None):
        """⟨H⟩ at the given parameter values; shift=(key, field, δ) moves one gate angle only."""
        m = self.model
        m.parameters = dict(zip(self.names, map(float, values)))
        m._apply_bindings()
        if shift is not None:
            (r, c, field), delta = shift
            g = m.gates[(r, c)]
            fields = {'angle': g.angle, 'phi': g.phi, 'lam': g.lam}
            fields[field] += delta
            m.gates[(r, c)] = Gate(g.name, g.targets, fields['angle'], fields['phi'], fields['lam'])
        self.calls += 1
        state = m.simulate_noisy(store=False)[1][-1] if m.noisy else m.simulate().column_states[-1]
        energy = expectation(state, m.n, self.terms)
        if shift is None:
            self._last = (np.array(values, float), energy)
        return energy

    def last_energy(self, values):
        """The energy at `values` if it was just computed, else None (saves a circuit run)."""
        if self._last is not None and np.array_equal(self._last[0], np.asarray(values, float)):
            return self._last[1]
        return None

    def energy_and_gradient(self, values):
        """(⟨H⟩, gradient) together: one forward and one backward pass for noiseless circuits."""
        if not self.adjoint:
            return self.energy(values), self.gradient(values)
        m, n = self.model, self.model.n
        m.parameters = dict(zip(self.names, map(float, values)))
        m._apply_bindings()
        bound = {}                                                 # (row, col) → [(field, name, factor)]
        for (r, c, field), (name, factor) in m.bindings.items():
            bound.setdefault((r, c), []).append((field, name, factor))
        ops = []
        for c, r, _, g in m._placed():
            ops.append((g, bound.get((r, c)) if m.gates.get((r, c)) is g else None))
        psi = m.initial_vector()
        for g, _ in ops:                                           # forward
            psi = apply_gate(psi, n, g)
        lam = sum(coef * _apply_term(psi, n, term) for coef, term in self.terms)   # H|ψ⟩
        energy = float(np.real(np.vdot(psi, lam)))
        index = {name: i for i, name in enumerate(self.names)}
        grad = np.zeros(len(self.names))
        for g, fields in reversed(ops):                            # backward
            inverse = gate_matrix(g).conj().T
            psi = apply_matrix(psi, n, inverse, g.targets)         # the state before this gate
            for field, name, factor in fields or ():
                if name in index:
                    d = apply_matrix(psi, n, gate_derivative(g, field), g.targets)
                    grad[index[name]] += factor * 2 * float(np.real(np.vdot(lam, d)))
            lam = apply_matrix(lam, n, inverse, g.targets)
        self.calls += 2                                            # a forward and a backward pass
        self._last = (np.array(values, float), energy)
        return energy, grad

    def gradient(self, values):
        """Exact gradient: the adjoint method for noiseless circuits, else the parameter-shift rule."""
        if self.adjoint:
            return self.energy_and_gradient(values)[1]
        return self.shift_gradient(values)

    def shift_gradient(self, values):
        """Exact gradient by the parameter-shift rule (two circuit runs per bound gate)."""
        grad = np.zeros(len(self.names))
        index = {name: i for i, name in enumerate(self.names)}
        for key, (name, factor) in self.model.bindings.items():
            if name not in index:
                continue
            plus = self.energy(values, (key, math.pi / 2))
            minus = self.energy(values, (key, -math.pi / 2))
            grad[index[name]] += factor * (plus - minus) / 2
        return grad

    def exact_minimum(self):
        return ground_energy(self.model.n, self.terms) if self.model.n <= 10 else None


class History(list):
    """[(values, energy), …] of the steps taken, with the number of circuit evaluations used."""
    evaluations = 0


def optimize(model, method='BFGS', steps=100, rate=0.2, callback=None, tolerance=1e-7, start=None):
    """Minimize ⟨observable⟩ over the model's parameters.

    method: 'BFGS' (quasi-Newton with exact parameter-shift gradients), 'gradient' (plain descent
    with parameter-shift gradients), 'COBYLA' or 'Nelder-Mead' (gradient-free, from scipy).
    callback(iteration, values, energy) may return False to stop. Returns the history
    [(values, energy), …], starting with the current parameters.
    """
    ev = Evaluator(model)
    values = np.array([model.parameters[n] for n in ev.names] if start is None else start, float)
    history = History([(values.copy(), ev.energy(values))])
    try:
        return _optimize(ev, values, history, method, steps, rate, callback, tolerance)
    finally:
        history.evaluations = ev.calls


def _optimize(ev, values, history, method, steps, rate, callback, tolerance):
    if callback is not None and callback(0, values, history[0][1]) is False:
        return history
    if method == 'gradient':
        # Gradient descent with a backtracking line search: a step that would raise ⟨H⟩ is
        # rejected and the step size halved; after a success it grows a little. A fixed step
        # overshoots when gradients are large (e.g. QAOA on bigger graphs) and oscillates.
        energy = history[0][1]
        for it in range(1, steps + 1):
            grad = ev.gradient(values)
            if np.linalg.norm(grad) < tolerance:
                break
            for _ in range(30):
                trial = values - rate * grad
                trial_energy = ev.energy(trial)
                if trial_energy <= energy:
                    break
                rate *= 0.5
            else:
                break                                              # no downhill step exists at this scale
            improvement = energy - trial_energy
            values, energy = trial, trial_energy
            rate = min(rate * 1.2, 2.0)
            history.append((values.copy(), energy))
            if callback is not None and callback(it, values, energy) is False:
                break
            if improvement < tolerance * 1e-2:
                break
        return history
    from scipy.optimize import minimize

    class Stop(Exception):
        pass

    def tracked(x):
        # Gradient-free methods try many probe points; only improvements are steps actually taken,
        # so the path and the curve show the trajectory (evaluations are counted separately).
        energy = ev.energy(x)
        if energy < history[-1][1] - 1e-15:
            history.append((np.array(x, float), energy))
            if callback is not None and callback(len(history) - 1, x, energy) is False:
                raise Stop
        elif callback is not None and ev.calls % 25 == 0 and callback(len(history) - 1, history[-1][0], history[-1][1]) is False:
            raise Stop
        return energy
    try:
        if method == 'BFGS':                                   # one recorded point per iteration
            def each(x):
                energy = ev.last_energy(x)
                if energy is None:
                    energy = ev.energy(x)
                history.append((np.array(x, float), energy))
                if callback is not None and callback(len(history) - 1, x, energy) is False:
                    raise Stop
            minimize(ev.energy_and_gradient, values, jac=True, method='BFGS', callback=each,
                     options={'maxiter': steps, 'gtol': 1e-8})
        else:
            options = ({'maxiter': steps, 'rhobeg': 0.5} if method == 'COBYLA'
                       else {'maxiter': steps, 'xatol': 1e-6, 'fatol': 1e-9})
            minimize(tracked, values, method=method, options=options)
    except Stop:
        pass
    return history


def landscape(model, first, second=None, points=41, span=math.pi):
    """⟨H⟩ over one parameter (a curve) or two (a grid), others held at their current values.

    Returns (xs, energies) or (xs, ys, grid) with grid[i][j] at (xs[j], ys[i])."""
    ev = Evaluator(model)
    base = np.array([model.parameters[n] for n in ev.names], float)
    i1 = ev.names.index(first)
    xs = np.linspace(-span, span, points)
    if second is None:
        out = []
        for x in xs:
            v = base.copy()
            v[i1] = x
            out.append(ev.energy(v))
        return xs, np.array(out)
    i2 = ev.names.index(second)
    grid = np.zeros((points, points))
    for i, y in enumerate(xs):
        for j, x in enumerate(xs):
            v = base.copy()
            v[i1], v[i2] = x, y
            grid[i, j] = ev.energy(v)
    return xs, xs.copy(), grid


def wrap_safely(model, values):
    """Map parameters into [−π, π) where that cannot change the circuit's results: every gate a
    parameter drives has a whole-number factor, so shifting it by 2π changes each angle by a
    multiple of 2π (at most a global sign). Other parameters are returned unchanged."""
    names = list(model.parameters)
    factors = {name: [] for name in names}
    for _, (name, factor) in model.bindings.items():
        if name in factors:
            factors[name].append(factor)
    out = []
    for name, value in zip(names, values):
        whole = all(abs(f - round(f)) < 1e-12 for f in factors[name])
        out.append(float((value + math.pi) % (2 * math.pi) - math.pi) if whole else float(value))
    return out


def best_of(model, starts, method='BFGS', steps=100, rng=None, callback=None, on_start=None):
    """Optimize from the current parameters and from starts − 1 random ones in [−π, π); keep the best.

    on_start(k, starts) is told when start k (0-based) begins; callback is passed through to each
    run and may return False to stop everything. Returns (best history, its start index,
    final energy of every start). The model itself is never changed.
    """
    rng = rng or np.random.default_rng()
    names = list(model.parameters)
    finals, best, best_index, stopped = [], None, 0, [False]

    def relay(iteration, values, energy):
        if callback is not None and callback(iteration, values, energy) is False:
            stopped[0] = True
            return False
        return True
    for k in range(max(1, int(starts))):
        if on_start is not None:
            on_start(k, starts)
        start = None if k == 0 else rng.uniform(-math.pi, math.pi, len(names))
        history = optimize(model, method, steps, callback=relay, start=start)
        finals.append(history[-1][1])
        if best is None or history[-1][1] < best[-1][1] - 1e-12:
            best, best_index = history, k
        if stopped[0]:
            break
    return best, best_index, finals
