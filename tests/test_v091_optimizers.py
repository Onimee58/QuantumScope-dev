"""v0.9.1: optimizing with shot noise, and Adam, SPSA, Rotosolve, the quantum natural gradient and
simulated annealing for the circuit optimizer."""
import numpy as np
import pytest

from quantumscope.editor import variational as V
from quantumscope.editor.circuit_model import CircuitModel


def model(library='vqe', **params):
    m = CircuitModel()
    m.load_library(library, params or {'problem': 'h2', 'layers': 2})
    return m


def test_state_derivatives_and_metric_are_exact():
    rng = np.random.default_rng(5)
    for m in (model(), model('qaoa', graph='ring4', layers=2)):
        ev = V.Evaluator(m)
        x = rng.uniform(-2, 2, len(ev.names))
        psi, D = ev.state_derivatives(x)
        h = 1e-6
        for i in range(len(x)):
            e = np.eye(len(x))[i] * h
            numeric = (ev.state_derivatives(x + e)[0] - ev.state_derivatives(x - e)[0]) / (2 * h)
            assert np.allclose(numeric, D[i], atol=1e-8)
        g = ev.metric(x)
        assert np.allclose(g, g.T) and np.linalg.eigvalsh(g).min() > -1e-10           # symmetric, PSD
        d = rng.normal(size=len(x))
        d /= np.linalg.norm(d)
        eps = 1e-4                                       # 1 − |⟨ψ(x)|ψ(x + εd)⟩|² ≈ ε² dᵀgd
        assert (1 - abs(np.vdot(psi, ev.state_derivatives(x + eps * d)[0])) ** 2) / eps ** 2 == pytest.approx(d @ g @ d, abs=1e-3)
    one = CircuitModel()
    one.set_circuit(1, [])
    one.place('RY', 0, 0)
    one.parameters['t'] = 0.3
    one.bindings[(0, 0, 'angle')] = ('t', 1.0)
    one.observable = 'Z0'
    assert V.Evaluator(one).metric([0.3])[0, 0] == pytest.approx(0.25)                # theory: 1/4


def test_shot_noise_is_unbiased_and_shrinks_with_shots():
    m = model()
    x = np.random.default_rng(1).uniform(-1, 1, len(m.parameters))
    exact = V.Evaluator(m).energy(x)
    spreads = []
    for shots in (100, 10000):
        ev = V.Evaluator(m, shots=shots, rng=np.random.default_rng(2))
        samples = [ev.energy(x) for _ in range(300)]
        assert abs(np.mean(samples) - exact) < 4 * np.std(samples) / np.sqrt(300)
        spreads.append(np.std(samples))
        assert not ev.adjoint                            # hardware has no adjoint trick
    assert spreads[0] / spreads[1] == pytest.approx(10, rel=0.3)                       # 1/√shots
    assert ev.true_energy(x) == pytest.approx(exact) and V.Evaluator(m).measured_terms == ev.measured_terms


@pytest.mark.parametrize('method', ['Adam', 'Rotosolve', 'QNG', 'BFGS', 'gradient'])
def test_exact_methods_reach_the_ground_state(method):
    for m in (model(), model('qaoa', graph='ring4', layers=2)):
        exact = V.Evaluator(m).exact_minimum()
        h = V.optimize(m, method, 200, seed=0)
        assert h.true[-1] == pytest.approx(exact, abs=1e-3), method
        assert h.true[-1] <= h.true[0] + 1e-12 and len(h.true) == len(h)


def test_with_shots_spsa_is_cheap_and_simplex_methods_struggle():
    m = model('qaoa', graph='ring4', layers=2)
    exact = V.Evaluator(m).exact_minimum()
    spsa = V.optimize(m, 'SPSA', 150, shots=1000, seed=3)
    assert spsa.true[-1] - exact < 0.02 and spsa.evaluations <= 2 * 150 + 15             # 2 runs per step
    assert spsa.shots_used == spsa.evaluations * 1000 * V.Evaluator(m).measured_terms
    simplex = [V.optimize(m, 'Nelder-Mead', 150, shots=1000, seed=s).true[-1] - exact for s in range(3)]
    assert np.mean(simplex) > 0.3                        # noise breaks the simplex
    for method in ('QNG', 'Rotosolve', 'Adam'):
        assert V.optimize(m, method, 150, shots=1000, seed=1).true[-1] - exact < 0.02, method


def test_rotosolve_fits_exactly_and_counts_updates_as_steps():
    m = model('vqe', problem='ising-3', layers=2)
    h = V.optimize(m, 'Rotosolve', 40, seed=0)
    assert len(h) - 1 == 40                              # steps are parameter updates
    assert all(b[1] <= a[1] + 1e-12 for a, b in zip(h, h[1:]))                       # never uphill (exact)
    for (_, recorded), true in zip(h, h.true):
        assert recorded == pytest.approx(true, abs=1e-12)                              # the fit is the energy
    m.bindings[next(iter(m.bindings))] = (list(m.parameters)[0], 0.5)
    with pytest.raises(ValueError, match='whole-number factors'):
        V.optimize(m, 'Rotosolve', 10)


def test_annealing_accepts_uphill_moves_and_ends_at_its_best():
    m = model('qaoa', graph='ring4', layers=2)
    h = V.optimize(m, 'annealing', 300, seed=4)
    energies = [e for _, e in h]
    assert any(b > a for a, b in zip(energies, energies[1:]))                        # it climbs, sometimes
    assert energies[-1] == min(energies) and energies[-1] < energies[0]


def test_random_methods_are_repeatable_and_best_of_passes_shots():
    m = model()
    for method in ('SPSA', 'annealing'):
        a, b = V.optimize(m, method, 30, shots=500, seed=7), V.optimize(m, method, 30, shots=500, seed=7)
        assert [e for _, e in a] == [e for _, e in b]
    history, _, finals = V.best_of(m, 2, 'SPSA', 30, rng=np.random.default_rng(0), shots=500)
    assert len(finals) == 2 and history.shots_used > 0
    with pytest.raises(ValueError, match='Unknown method'):
        V.optimize(m, 'Newton', 5)


def test_the_measured_curve_is_an_unbiased_measurement_for_every_method():
    """The chart's thin line is a shot measurement of ⟨H⟩ at each point, for every method. (SPSA's own
    probes are biased by the curvature, 0.2 on this example, so it gets a separate, uncounted one.)"""
    m = model('qaoa', graph='ring4', layers=2)
    for method in ('SPSA', 'Adam', 'annealing'):
        h = V.optimize(m, method, 150, shots=1000, seed=3)
        errors = np.array([e for _, e in h][1:]) - np.array(h.true[1:])
        assert abs(errors.mean()) < 4 * errors.std() / np.sqrt(len(errors)) + 1e-3, method
    spsa = V.optimize(m, 'SPSA', 150, shots=1000, seed=3)
    assert spsa.evaluations == 1 + 10 + 2 * 150                                        # display not counted
