"""From a calculator state to the circuit simulator's per-qubit starting states (v0.9.0).

The simulator starts from a product of single-qubit states, each a point (θ, φ) on the Bloch sphere.
A product state converts exactly; an entangled one cannot (each qubit's reduced state is then mixed).
"""
import math

import numpy as np

TOL = 1e-9


def reduced(vector, qubit, n):
    """The density matrix of one qubit of an n-qubit pure state (qubit 0 is the leftmost)."""
    psi = np.asarray(vector, complex).reshape((2,) * n)
    psi = np.moveaxis(psi, qubit, 0).reshape(2, -1)
    return psi @ psi.conj().T


def product_angles(vector):
    """[(θ, φ) per qubit] if the state is a product of single-qubit states, else None.
    Raises ValueError for something that is not a normalized state of 1 to 6 qubits."""
    v = np.asarray(vector, complex).ravel()
    n = len(v).bit_length() - 1
    if len(v) < 2 or 1 << n != len(v) or n > 6:
        raise ValueError('Only states of 1 to 6 qubits can go to the circuit simulator')
    norm = np.linalg.norm(v)
    if abs(norm - 1) > 1e-6:
        raise ValueError(f'The state is not normalized (its length is {norm:.4g}); use normalize(…)')
    v = v / norm
    angles = []
    for q in range(n):
        rho = reduced(v, q, n)
        if abs(np.real(np.trace(rho @ rho)) - 1) > 1e-6:          # mixed: entangled with the others
            return None
        x, y, z = (2 * np.real(rho[0, 1]), 2 * np.imag(rho[1, 0]), np.real(rho[0, 0] - rho[1, 1]))
        theta = math.acos(max(-1.0, min(1.0, z)))
        phi = math.atan2(y, x) % (2 * math.pi) if math.hypot(x, y) > TOL else 0.0
        angles.append((theta, phi))
    return angles


def state_from_angles(angles):
    """The product state ⊗ (cos θ/2 |0⟩ + e^{iφ} sin θ/2 |1⟩), qubit 0 first."""
    out = np.array([1.0 + 0j])
    for theta, phi in angles:
        out = np.kron(out, [math.cos(theta / 2), np.exp(1j * phi) * math.sin(theta / 2)])
    return out
