"""v0.8.1 (17c): a vectorized circuit simulator and adjoint gradients for the circuit optimizer.

Both are checked against independent references: the original per-amplitude loops, the
parameter-shift rule, and numerical derivatives. Results must be identical, only faster.
"""
import math
import time

import numpy as np
import pytest

from quantumscope.editor import variational as V
from quantumscope.editor.circuit_model import CircuitModel
from quantumscope.physics import circuits as C

RNG = np.random.default_rng(2026)


def reference_apply(state, n, gate):
    """The v0.8.0 simulator: one Python loop over the amplitudes per gate (kept as a reference)."""
    name, ids, result = gate.name.upper(), gate.targets, np.array(state, complex, copy=True)
    if name in C.SINGLE:
        mask, u = 1 << (n - 1 - ids[0]), C.unitary(C.Gate(name, ids, gate.angle, gate.phi, gate.lam))
        for i in range(1 << n):
            if not i & mask:
                j = i | mask
                a, b = result[i], result[j]
                result[i], result[j] = u[0, 0] * a + u[0, 1] * b, u[1, 0] * a + u[1, 1] * b
    elif name in C.TRIPLE:
        m1, m2, m3 = (1 << (n - 1 - q) for q in ids)
        for i in range(1 << n):
            if name == 'CCX' and (i & m1) and (i & m2) and not (i & m3):
                j = i | m3
                result[i], result[j] = result[j], result[i]
            elif name == 'CSWAP' and (i & m1) and not (i & m2) and (i & m3):
                j = i ^ m2 ^ m3
                result[i], result[j] = result[j], result[i]
    else:
        m1, m2 = (1 << (n - 1 - q) for q in ids)
        for i in range(1 << n):
            if name == 'CP' and i & m1 and i & m2:
                result[i] *= np.exp(1j * gate.angle)
            elif name == 'CZ' and i & m1 and i & m2:
                result[i] *= -1
            elif name == 'CX' and i & m1 and not i & m2:
                j = i | m2
                result[i], result[j] = result[j], result[i]
            elif name == 'SWAP' and not (i & m1) and i & m2:
                j = i ^ m1 ^ m2
                result[i], result[j] = result[j], result[i]
    return result


def test_every_gate_matches_the_reference_simulator():
    count = 0
    for n in range(1, 7):
        for name in C.ALL:
            k = 3 if name in C.TRIPLE else 2 if name in C.DUAL else 1
            if k > n:
                continue
            for _ in range(4):
                targets = tuple(int(q) for q in RNG.choice(n, k, replace=False))
                gate = C.Gate(name, targets, *RNG.uniform(-4, 4, 3))
                state = RNG.normal(size=2 ** n) + 1j * RNG.normal(size=2 ** n)
                assert np.allclose(C.apply_gate(state, n, gate), reference_apply(state, n, gate), atol=1e-13), gate
                count += 1
    assert count > 300
    with pytest.raises(ValueError):
        C.apply_gate(np.ones(4), 2, C.Gate('CX', (0, 0)))


def test_simulate_column_states_match_a_step_by_step_run():
    m = CircuitModel()
    m.load_library('qaoa', {'graph': 'ring4', 'layers': 2})
    sim = m.simulate()
    state = m.initial_vector()
    by_column = {}
    for c, _, _, g in m._placed():
        by_column.setdefault(c, []).append(g)
    for k, c in enumerate(sim.occupied_columns):
        for g in by_column[c]:
            state = reference_apply(state, m.n, g)
        assert np.allclose(sim.column_states[k + 1], state, atol=1e-12)


@pytest.mark.parametrize('name, fields', [('RX', ['angle']), ('RY', ['angle']), ('RZ', ['angle']), ('P', ['angle']),
                                          ('CP', ['angle']), ('U', ['angle', 'phi', 'lam'])])
def test_gate_derivatives_are_exact(name, fields):
    targets = (0, 1) if name == 'CP' else (0,)
    for _ in range(4):
        values = dict(zip(('angle', 'phi', 'lam'), RNG.uniform(-4, 4, 3)))
        for field in fields:
            up, down, h = dict(values), dict(values), 1e-6
            up[field] += h
            down[field] -= h
            numeric = (C.gate_matrix(C.Gate(name, targets, up['angle'], up['phi'], up['lam'])) -
                       C.gate_matrix(C.Gate(name, targets, down['angle'], down['phi'], down['lam']))) / (2 * h)
            exact = V.gate_derivative(C.Gate(name, targets, values['angle'], values['phi'], values['lam']), field)
            assert np.allclose(exact, numeric, atol=1e-8)


@pytest.mark.parametrize('library, params', [('vqe', {'problem': 'h2', 'layers': 2}), ('vqe', {'problem': 'ising-3', 'layers': 2}),
                                             ('qaoa', {'graph': 'ring6', 'layers': 3}), ('vqls', {'problem': 'standard', 'layers': 2})])
def test_adjoint_gradient_equals_the_parameter_shift_rule(library, params):
    m = CircuitModel()
    m.load_library(library, params)
    ev = V.Evaluator(m)
    assert ev.adjoint
    for _ in range(3):
        x = RNG.uniform(-math.pi, math.pi, len(ev.names))
        energy, grad = ev.energy_and_gradient(x)
        assert energy == pytest.approx(ev.energy(x), abs=1e-12)
        assert np.allclose(grad, ev.shift_gradient(x), atol=1e-10)


def test_every_bindable_gate_with_factors_and_shared_parameters():
    for _ in range(15):
        n = int(RNG.integers(2, 5))
        m = CircuitModel()
        m.set_circuit(n, [])
        for col in range(int(RNG.integers(4, 9))):
            kind = str(RNG.choice(['RX', 'RY', 'RZ', 'P', 'U', 'CP', 'H', 'CX']))
            pair = tuple(int(v) for v in RNG.choice(n, 2, replace=False))
            m.place(kind, pair[0], col, operands=pair if kind in ('CP', 'CX') else None)
        for name in 'abc':
            m.parameters[name] = float(RNG.uniform(-2, 2))
        for (r, c), g in m.gates.items():
            for field in (('angle', 'phi', 'lam') if g.name == 'U' else ('angle',) if g.name in C.PARAMETERIZED else ()):
                m.bindings[(r, c, field)] = (str(RNG.choice(list('abc'))), float(RNG.choice([1.0, -2.0, 0.5])))
        if not m.bindings:
            continue
        m.observable = '0.7 Z0 + 0.4 X0 X1 - 0.3 Y1'
        ev = V.Evaluator(m)
        x = RNG.uniform(-3, 3, len(ev.names))
        assert np.allclose(ev.energy_and_gradient(x)[1], ev.shift_gradient(x), atol=1e-10)


def test_optimization_paths_agree_and_are_fast():
    def run(adjoint):
        m = CircuitModel()
        m.load_library('qaoa', {'graph': 'ring6', 'layers': 3})
        original = V.Evaluator.__init__

        def init(self, model):
            original(self, model)
            self.adjoint = adjoint
        V.Evaluator.__init__ = init
        try:
            start = time.perf_counter()
            history = V.optimize(m, 'BFGS', 200)
            return history, time.perf_counter() - start
        finally:
            V.Evaluator.__init__ = original
    fast, seconds = run(True)
    slow, _ = run(False)
    # The adjoint and parameter-shift gradients agree to about 1e-15, not bit for bit (different
    # order of floating-point operations, and different maths libraries on different machines). Near
    # the optimum that can change when BFGS stops by a step, so: the same path up to rounding, the same
    # result, and step counts within two. A wrong gradient would split the paths within a few steps.
    assert all(abs(a[1] - b[1]) < 1e-6 for a, b in zip(fast, slow))
    assert fast[-1][1] == pytest.approx(slow[-1][1], abs=1e-9) and abs(len(fast) - len(slow)) <= 2
    assert seconds < 3.0, f'{seconds:.1f} s'                                   # v0.8.0: 13.2 s; now ≈ 0.6 s
    m = CircuitModel()
    m.load_library('qaoa', {'graph': 'ring6', 'layers': 3})
    start = time.perf_counter()
    V.best_of(m, 3, 'BFGS', 200, rng=np.random.default_rng(0))
    assert time.perf_counter() - start < 8.0                                   # v0.8.0: about 40 s


def test_noisy_circuits_keep_the_parameter_shift_rule():
    m = CircuitModel()
    m.load_library('vqe', {'problem': 'h2', 'layers': 1})
    from quantumscope.physics.noise import NoiseModel
    m.set_noise_model(NoiseModel(True, single=0.02, two=0.05))
    assert m.noisy
    ev = V.Evaluator(m)
    assert not ev.adjoint
    x = RNG.uniform(-1, 1, len(ev.names))
    h = 1e-5
    numeric = [(ev.energy(x + h * e) - ev.energy(x - h * e)) / (2 * h) for e in np.eye(len(x))]
    assert np.allclose(ev.gradient(x), numeric, atol=1e-6)
