"""v0.9.2: quantum annealing, checked against independent full-space computations."""
import numpy as np
import pytest
from scipy.linalg import expm

from quantumscope.physics import annealing as A


def full_space(problem):
    """H_d and H_p as dense matrices over all 2^n bitstrings (no symmetry used)."""
    n = problem.n
    X, I = np.array([[0, 1], [1, 0]]), np.eye(2)
    Hd = np.zeros((1 << n, 1 << n))
    for q in range(n):
        M = np.array([[1.0]])
        for k in range(n):
            M = np.kron(M, X if k == q else I)
        Hd -= M
    return Hd, np.diag(problem.diagonal)


PROBLEMS = [A.maxcut('ring4'), A.maxcut('ring5'), A.spin_glass(4, 1), A.partition([4, 5, 6, 7, 8])]


@pytest.mark.parametrize('problem', PROBLEMS, ids=lambda p: p.key)
def test_the_symmetric_sector_gives_the_full_space_evolution(problem):
    Hd, Hp = full_space(problem)
    T, slices = 3.0, 200
    psi = np.full(1 << problem.n, (1 << problem.n) ** -0.5, complex)
    for k in range(slices):
        s = (k + 0.5) / slices
        psi = expm(-1j * T / slices * ((1 - s) * Hd + s * Hp)) @ psi
    result = A.anneal(problem, T, slices=slices, record=2, ground=False)
    assert np.allclose(result.probabilities[-1], np.abs(psi) ** 2, atol=1e-12)
    assert result.final_success == pytest.approx(sum(np.abs(psi[int(b, 2)]) ** 2 for b in problem.solutions()))
    levels = A.spectrum(problem, points=3).levels[1]                       # s = 0.5
    full = np.linalg.eigvalsh((Hd + Hp) / 2)
    assert all(np.min(np.abs(full - e)) < 1e-9 for e in levels)          # genuine levels of H(s)


@pytest.mark.parametrize('problem', PROBLEMS, ids=lambda p: p.key)
def test_the_circuit_is_the_exact_trotter_product(problem):
    Hd, Hp = full_space(problem)
    T, steps = 3.0, 6
    psi = np.full(1 << problem.n, (1 << problem.n) ** -0.5, complex)
    for r in range(steps):
        s = (r + 0.5) / steps
        psi = expm(-1j * T / steps * (1 - s) * Hd) @ (expm(-1j * T / steps * s * Hp) @ psi)
    assert abs(np.vdot(A.circuit_state(problem, T, steps), psi)) == pytest.approx(1, abs=1e-12)


def test_limits_convergence_and_the_adiabatic_trend():
    p = A.maxcut('ring4')
    assert A.anneal(p, 0.01, ground=False).final_success == pytest.approx(len(p.solutions()) / 16, abs=1e-3)
    assert A.anneal(p, 30, ground=False).final_success > 0.99                # slow enough: stays in the ground state
    exact = A.anneal(p, 10, record=2, ground=False).probabilities[-1]
    errors = [np.abs(np.abs(A.circuit_state(p, 10, k)) ** 2 - exact).max() for k in (5, 20, 80)]
    assert errors[0] > 0.1 and errors[2] < 0.005                         # Trotter converges to the anneal
    a = A.anneal(p, 10, slices=200, record=2, ground=False).final_success
    b = A.anneal(p, 10, slices=800, record=2, ground=False).final_success
    assert abs(a - b) < 1e-4
    curve = A.success_curve(A.spin_glass(6, 0), [1, 3, 10, 30])
    assert np.all(np.diff(curve) > 0)                                    # slower anneals succeed more often
    record = A.anneal(p, 30, record=11)
    assert record.ground_overlap[0] == pytest.approx(1) and record.ground_overlap[-1] > 0.99


def test_problems_and_spectra():
    glass = A.spin_glass(6, 0)
    energies = np.unique(np.round(glass.diagonal, 9))
    assert len(glass.solutions()) == 1 and energies[1] - energies[0] >= 0.2 and not glass.symmetric
    part = A.partition([4, 5, 6, 7, 8])
    assert part.symmetric and sorted(part.solutions()) == ['00011', '11100'] and part.ground_energy == 0
    sp = A.spectrum(A.maxcut('ring4'), points=41)
    assert sp.symmetric and sp.minimum_gap > 0.5 and 0 < sp.minimum_at < 1 and sp.adiabatic_time > 0
    assert np.all(np.diff(sp.levels, axis=1) >= -1e-9)                    # sorted levels
    custom = A.from_text('Z0 Z1 - 0.5 Z2 + 1', 3)
    assert custom.solutions() == ['010', '100'] and custom.ground_energy == pytest.approx(-0.5)   # by hand
    with pytest.raises(ValueError, match='only contain Z terms'):
        A.from_text('X0 + Z1', 2)
    with pytest.raises(ValueError, match='1 to 10 spins'):
        A.spin_glass(11)
    assert A.anneal(A.maxcut('ring4'), 5, cancelled=lambda: True) is None
