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

    def __init__(self, model, shots=0, rng=None):
        if not model.observable:
            raise ValueError('Set an observable first (for example a Hamiltonian).')
        if not model.parameters:
            raise ValueError('The circuit has no parameters to optimize.')
        self.model = copy.deepcopy(model)
        self.names = list(model.parameters)
        self.terms = parse(model.observable, model.n)
        self.calls = 0
        self.shots = int(shots)                                    # 0: exact; else per Pauli term (v0.9.1)
        self.rng = rng if rng is not None else np.random.default_rng()
        # The adjoint method needs the exact state, which hardware never gives: with shots, gradients
        # come from the parameter-shift rule on the sampled energies, as on a real device.
        self.adjoint = not model.noisy and not self.shots          # pure states: one forward + one backward pass
        self._last = None                                          # (values, energy) of the latest evaluation

    @property
    def measured_terms(self):
        """The Pauli terms that need measuring (a constant term does not)."""
        return sum(1 for _, ops in self.terms if ops)

    def _sampled(self, state):
        """⟨H⟩ estimated from `shots` measurements of each Pauli term: each outcome is ±1, with
        P(+1) = (1 + ⟨P⟩)/2, so the count of +1 outcomes is binomial."""
        total = 0.0
        for coefficient, ops in self.terms:
            if not ops:
                total += coefficient
                continue
            mean = min(1.0, max(-1.0, expectation(state, self.model.n, [(1.0, ops)])))
            plus = self.rng.binomial(self.shots, (1 + mean) / 2)
            total += coefficient * (2 * plus / self.shots - 1)
        return float(total)

    def _final_state(self, values):
        m = self.model
        m.parameters = dict(zip(self.names, map(float, values)))
        m._apply_bindings()
        return m.simulate_noisy(store=False)[1][-1] if m.noisy else m.simulate().column_states[-1]

    def observe(self, values):
        """⟨H⟩ as a measurement would give it (sampled with shots), for the chart only: not counted,
        never seen by the optimizer. SPSA uses it, since its two probes do not measure ⟨H⟩ at its point."""
        state = self._final_state(values)
        return self._sampled(state) if self.shots else expectation(state, self.model.n, self.terms)

    def true_energy(self, values):
        """The exact ⟨H⟩, for display only: not counted, never seen by the optimizer."""
        return expectation(self._final_state(values), self.model.n, self.terms)

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
        energy = self._sampled(state) if self.shots else expectation(state, m.n, self.terms)
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

    def state_derivatives(self, values):
        """(|ψ⟩, D) with D[i] = ∂|ψ⟩/∂(parameter i), exactly: each bound gate's derivative matrix in
        place of the gate, times its factor (noiseless circuits only)."""
        if self.model.noisy:
            raise ValueError('The quantum natural gradient needs a noiseless circuit (pure states)')
        m, n = self.model, self.model.n
        m.parameters = dict(zip(self.names, map(float, values)))
        m._apply_bindings()
        bound = {}
        for (r, c, field), (name, factor) in m.bindings.items():
            bound.setdefault((r, c), []).append((field, name, factor))
        ops = [(g, bound.get((r, c)) if m.gates.get((r, c)) is g else None) for c, r, _, g in m._placed()]
        before, psi = [], m.initial_vector()
        for g, _ in ops:
            before.append(psi)
            psi = apply_gate(psi, n, g)
        index = {name: i for i, name in enumerate(self.names)}
        D = np.zeros((len(self.names), len(psi)), complex)
        for k, (g, fields) in enumerate(ops):
            for field, name, factor in fields or ():
                if name not in index:
                    continue
                d = apply_matrix(before[k], n, gate_derivative(g, field), g.targets)
                for later, _ in ops[k + 1:]:
                    d = apply_gate(d, n, later)
                D[index[name]] += factor * d
        return psi, D

    def metric(self, values):
        """The Fubini–Study metric g_ij = Re(⟨∂iψ|∂jψ⟩ − ⟨∂iψ|ψ⟩⟨ψ|∂jψ⟩): how far the state moves
        when the parameters move (the quantum geometric tensor's real part)."""
        psi, D = self.state_derivatives(values)
        overlaps = D.conj() @ psi
        return np.real(D.conj() @ D.T - np.outer(overlaps, overlaps.conj()))

    def frequencies(self):
        """For each parameter, the largest frequency K of ⟨H⟩ as a function of it, or None if ⟨H⟩ is
        not a trigonometric polynomial in it (a factor that is not a whole number). Every bindable
        gate is exp(−iθG) with G's eigenvalues one apart, so each gate adds |factor|."""
        K = {name: 0 for name in self.names}
        for _, (name, factor) in self.model.bindings.items():
            if name not in K or K[name] is None:
                continue
            if abs(factor - round(factor)) > 1e-12:
                K[name] = None
            else:
                K[name] += abs(int(round(factor)))
        return [K[name] for name in self.names]

    def exact_minimum(self):
        return ground_energy(self.model.n, self.terms) if self.model.n <= 10 else None


class History(list):
    """[(values, energy), …] of the steps taken, with the number of circuit evaluations used."""
    evaluations = 0


METHODS = ('BFGS', 'gradient', 'Adam', 'SPSA', 'Rotosolve', 'QNG', 'annealing', 'COBYLA', 'Nelder-Mead')


def optimize(model, method='BFGS', steps=100, rate=0.2, callback=None, tolerance=1e-7, start=None, shots=0,
             seed=None):
    """Minimize ⟨observable⟩ over the model's parameters.

    method: 'BFGS' (quasi-Newton, exact gradients), 'gradient' (plain descent), 'Adam' (momentum and
    adaptive steps), 'SPSA' (two circuit runs per step, whatever the number of parameters),
    'Rotosolve' (each parameter set to its exact minimum in turn), 'QNG' (the quantum natural
    gradient), 'annealing' (simulated annealing), 'COBYLA' or 'Nelder-Mead' (gradient-free, scipy).
    shots: 0 for exact energies, else each Pauli term is estimated from this many measurements (the
    optimizer then sees noisy energies, as on hardware). seed makes random methods repeatable.
    callback(iteration, values, energy) may return False to stop. Returns the history
    [(values, energy), …] of what the optimizer saw, starting with the current parameters;
    history.true holds the exact energy of every recorded point, and history.evaluations and
    history.shots_used the cost.
    """
    if method not in METHODS:
        raise ValueError(f'Unknown method {method!r}')
    rng = np.random.default_rng(seed)
    ev = Evaluator(model, shots=shots, rng=rng)
    if method == 'Rotosolve' and None in ev.frequencies():
        bad = [n for n, k in zip(ev.names, ev.frequencies()) if k is None]
        raise ValueError(f'Rotosolve needs whole-number factors; {", ".join(bad)} has a fractional one')
    values = np.array([model.parameters[n] for n in ev.names] if start is None else start, float)
    history = History([(values.copy(), ev.energy(values))])
    try:
        return _optimize(ev, values, history, method, steps, rate, callback, tolerance, rng)
    finally:
        history.evaluations = ev.calls
        history.shots_used = ev.calls * ev.shots * ev.measured_terms
        history.true = [ev.true_energy(v) for v, _ in history]


def _record(history, callback, values, energy):
    history.append((np.array(values, float), float(energy)))
    return callback is None or callback(len(history) - 1, values, energy) is not False


def _adam(ev, values, history, steps, rate, callback, tolerance):
    """Adam: a running mean of the gradient (momentum) and of its square (a step size per parameter)."""
    m, v = np.zeros_like(values), np.zeros_like(values)
    for t in range(1, steps + 1):
        energy, grad = ev.energy_and_gradient(values)
        if t > 1 and not _record(history, callback, values, energy):
            return history
        if not ev.shots and np.linalg.norm(grad) < tolerance:
            return history
        m = 0.9 * m + 0.1 * grad
        v = 0.999 * v + 0.001 * grad * grad
        values = values - rate * (m / (1 - 0.9 ** t)) / (np.sqrt(v / (1 - 0.999 ** t)) + 1e-8)
    _record(history, callback, values, ev.energy(values))
    return history


def _spsa(ev, values, history, steps, rate, callback, rng):
    """SPSA (Spall): move every parameter at once by ±c along a random direction Δ; the two energies
    give a gradient estimate along Δ. Two circuit runs per step, however many parameters. Gains
    a_k = a/(k + 1 + A)^0.602 and c_k = c/(k + 1)^0.101; a is calibrated so that the first steps
    move the parameters by about `rate`. The recorded energies come from Evaluator.observe (for the chart, not counted):
    SPSA itself only measures its two probes."""
    p = len(values)
    c, A = 0.15 if ev.shots else 0.1, 0.1 * steps
    probes = []
    for _ in range(5):                                         # calibration (counted as evaluations)
        delta = rng.choice((-1.0, 1.0), p)
        probes.append(abs(ev.energy(values + c * delta) - ev.energy(values - c * delta)) / (2 * c))
    a = rate * (A + 1) ** 0.602 / max(float(np.mean(probes)), 1e-8)
    for k in range(steps):
        ak, ck = a / (k + 1 + A) ** 0.602, c / (k + 1) ** 0.101
        delta = rng.choice((-1.0, 1.0), p)
        plus, minus = ev.energy(values + ck * delta), ev.energy(values - ck * delta)
        values = values - ak * (plus - minus) / (2 * ck) * delta
        # The probes' mean is biased by the curvature, so the chart gets its own (uncounted) measurement.
        if not _record(history, callback, values, ev.observe(values)):
            return history
    return history


def _rotosolve(ev, values, history, steps, callback, tolerance):
    """Rotosolve (Ostaszewski et al.; Nakanishi et al.): with the others fixed, ⟨H⟩ is a trigonometric
    polynomial of degree K in each parameter (K = 1 for a parameter driving one rotation), fixed by
    2K + 1 energies. Each parameter is set in turn to that polynomial's minimum; no learning rate."""
    from scipy.optimize import minimize_scalar
    degrees = ev.frequencies()
    energy = history[-1][1]
    for sweep in range(steps):
        start_energy = energy
        for i, K in enumerate(degrees):
            if K == 0:
                continue
            points = values[i] + 2 * np.pi * np.arange(2 * K + 1) / (2 * K + 1)
            samples = []
            for k, x in enumerate(points):
                trial = values.copy()
                trial[i] = x
                samples.append(energy if k == 0 else ev.energy(trial))
            coeffs = np.fft.rfft(samples) / (2 * K + 1)       # E(x) = Σ_k |c_k| cos(k(x − x0) + arg)
            k = np.arange(K + 1)

            def curve(x, coeffs=coeffs, x0=points[0], k=k):
                weights = np.where(k == 0, 1.0, 2.0)
                return float(np.sum(weights * np.real(coeffs * np.exp(1j * k * (x - x0)))))
            grid = values[i] + np.linspace(-np.pi, np.pi, 64 * K, endpoint=False)
            best = grid[int(np.argmin([curve(x) for x in grid]))]
            step = np.pi / (32 * K)
            best = minimize_scalar(curve, bounds=(best - step, best + step), method='bounded',
                                   options={'xatol': 1e-10}).x
            values = values.copy()
            values[i] = (best + np.pi) % (2 * np.pi) - np.pi if K == 1 else best
            energy = curve(best) if not ev.shots else ev.energy(values)
            if not _record(history, callback, values, energy) or len(history) - 1 >= steps:
                return history                                 # steps: parameter updates, as elsewhere
        if not ev.shots and start_energy - energy < tolerance:
            break
    return history


def _qng(ev, values, history, steps, rate, callback, tolerance):
    """The quantum natural gradient (Stokes et al.): step along g⁻¹∇⟨H⟩, where g is the Fubini–Study
    metric, so that each step changes the quantum state by a similar amount whichever parameters
    move. A small regularization keeps g invertible. Exact energies: a backtracking line search,
    as for gradient descent; with shots, fixed steps."""
    energy = history[-1][1]
    # With shots the gradient is noisy, and g⁻¹ amplifies noise along directions the state barely
    # depends on: a stronger regularization and a smaller step keep it stable (standard practice).
    regularization = 0.05 if ev.shots else 1e-3
    if ev.shots:
        rate = min(rate, 0.05)
    for _ in range(steps):
        grad = ev.gradient(values)
        if not ev.shots and np.linalg.norm(grad) < tolerance:
            break
        g = ev.metric(values)
        direction = np.linalg.solve(g + regularization * np.eye(len(values)), grad)
        if ev.shots:
            values = values - rate * direction
            energy = ev.energy(values)
        else:
            for _ in range(30):
                trial = values - rate * direction
                trial_energy = ev.energy(trial)
                if trial_energy <= energy:
                    break
                rate *= 0.5
            else:
                break
            improvement = energy - trial_energy
            values, energy = trial, trial_energy
            rate = min(rate * 1.2, 2.0)
        if not _record(history, callback, values, energy):
            break
        if not ev.shots and improvement < tolerance * 1e-2:
            break
    return history


def _annealing(ev, values, history, steps, rate, callback, rng):
    """Simulated annealing: random moves, always accepted downhill and uphill with probability
    exp(−ΔE/T), while the temperature T falls geometrically. Uphill moves let it leave local
    minima. The walk is recorded (uphill moves included); it ends at the best point found."""
    energy = history[-1][1]
    trials = [abs(ev.energy(values + rng.normal(0, rate, len(values))) - energy) for _ in range(5)]
    t0 = max(float(np.mean(trials)), 1e-6)                     # calibration (counted)
    t_end = t0 * 1e-3
    best_values, best_energy = values.copy(), energy
    for k in range(steps):
        temperature = t0 * (t_end / t0) ** (k / max(1, steps - 1))
        width = 2 * rate * math.sqrt(temperature / t0) + 0.02
        trial = values + rng.normal(0, width, len(values))
        trial_energy = ev.energy(trial)
        if trial_energy <= energy or rng.random() < math.exp(-(trial_energy - energy) / temperature):
            values, energy = trial, trial_energy
            if energy < best_energy:
                best_values, best_energy = values.copy(), energy
            if not _record(history, callback, values, energy):
                return history
    if not np.array_equal(best_values, history[-1][0]):
        _record(history, callback, best_values, best_energy)
    return history


def _optimize(ev, values, history, method, steps, rate, callback, tolerance, rng=None):
    if callback is not None and callback(0, values, history[0][1]) is False:
        return history
    rng = rng if rng is not None else np.random.default_rng()
    if method == 'Adam':
        return _adam(ev, values, history, steps, min(rate, 0.1), callback, tolerance)
    if method == 'SPSA':
        return _spsa(ev, values, history, steps, rate, callback, rng)
    if method == 'Rotosolve':
        return _rotosolve(ev, values, history, steps, callback, tolerance)
    if method == 'QNG':
        return _qng(ev, values, history, steps, rate, callback, tolerance)
    if method == 'annealing':
        return _annealing(ev, values, history, steps, rate, callback, rng)
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


def best_of(model, starts, method='BFGS', steps=100, rng=None, callback=None, on_start=None, shots=0):
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
        history = optimize(model, method, steps, callback=relay, start=start, shots=shots,
                           seed=int(rng.integers(2 ** 32)))
        finals.append(history[-1][1])
        if best is None or history[-1][1] < best[-1][1] - 1e-12:
            best, best_index = history, k
        if stopped[0]:
            break
    return best, best_index, finals
