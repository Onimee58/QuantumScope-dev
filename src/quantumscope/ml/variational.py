"""A variational quantum classifier (NumPy and SciPy, no Qt).

For a data point x (one feature per qubit) the circuit is
    feature map U(x), then `layers` × [RY(θ) on every qubit, then a ring of CNOTs],
and the model's output is f(x) = ⟨Z₀⟩ + b, between −1 and 1 plus a bias b; the predicted class is
sign(f). Training lowers the mean squared error ½·mean((f − y)²) for labels y = ±1, with exact
gradients. The whole training set is simulated at once.

Gradients (v0.8.1): by default the adjoint method, which needs one forward and one backward pass
however many parameters there are (Jones & Gacon, 2020). The parameter-shift rule, two circuit runs
per parameter as on real hardware, gives the same numbers and stays available (gradient='shift').
"""
import math

import numpy as np

from quantumscope.ml import kernels
from quantumscope.physics.circuits import Gate


class Classifier:
    def __init__(self, qubits, layers=2, feature_map='angle', reps=1, bandwidth=1.0, seed=0, gradient='adjoint'):
        self.qubits, self.layers = int(qubits), int(layers)
        self.gradient_method = gradient
        self._cache = None                                               # (key, feature-map states)
        self.feature_map, self.reps, self.bandwidth = feature_map, reps, bandwidth
        rng = np.random.default_rng(seed)
        self.theta = rng.uniform(-0.1, 0.1, self.layers * self.qubits)    # near the identity
        self.bias = 0.0

    # ---- the circuit -----------------------------------------------------------------------------
    def gates(self, x, theta=None):
        """The full circuit for one data point, as gates for the circuit simulator."""
        theta = self.theta if theta is None else theta
        out = kernels.circuit(x, self.feature_map, self.reps, self.bandwidth)
        for layer in range(self.layers):
            out += [Gate('RY', (q,), float(theta[layer * self.qubits + q])) for q in range(self.qubits)]
            out += self._ring()
        return out

    def _ring(self):
        n = self.qubits
        if n == 1:
            return []
        if n == 2:
            return [Gate('CX', (0, 1))]
        return [Gate('CX', (q, (q + 1) % n)) for q in range(n)]

    # ---- batched simulation ----------------------------------------------------------------------
    def _ry(self, states, qubit, angle):
        """RY on one qubit of every state, in place (new halves computed directly, no extra copies)."""
        n = self.qubits
        c, s = math.cos(angle / 2), math.sin(angle / 2)
        view = states.reshape(len(states), 2 ** qubit, 2, 2 ** (n - qubit - 1))
        zero, one = view[:, :, 0, :], view[:, :, 1, :]
        new_zero = c * zero - s * one
        one *= c
        one += s * zero
        zero[...] = new_zero
        return states

    def _cx(self, states, control, target):
        key = (control, target)
        perms = self.__dict__.setdefault('_perms', {})
        if key not in perms:                                             # the index map never changes
            n = self.qubits
            index = np.arange(2 ** n)
            perms[key] = np.where((index >> (n - 1 - control)) & 1, index ^ (1 << (n - 1 - target)), index)
        return states[:, perms[key]]

    def _forward(self, start, theta):
        states = start.copy()
        for layer in range(self.layers):
            for q in range(self.qubits):
                states = self._ry(states, q, theta[layer * self.qubits + q])
            for gate in self._ring():
                states = self._cx(states, *gate.targets)
        z0 = 1 - 2 * ((np.arange(2 ** self.qubits) >> (self.qubits - 1)) & 1)   # Z on q0
        return (np.abs(states) ** 2) @ z0

    def _start(self, X):
        """The feature-map states of X, computed once per data set (training reuses them every step)."""
        X = np.ascontiguousarray(X, float)
        key = (X.shape, hash(X.tobytes()), self.feature_map, self.reps, self.bandwidth)
        if self._cache is None or self._cache[0] != key:
            self._cache = (key, kernels.states(X, self.feature_map, self.reps, self.bandwidth))
        return self._cache[1]

    def expectation(self, X, theta=None):
        """⟨Z₀⟩ for every row of X."""
        theta = self.theta if theta is None else theta
        return self._forward(self._start(X), theta)

    def decision(self, X):
        return self.expectation(X) + self.bias

    def predict(self, X):
        return np.where(self.decision(X) >= 0, 1, -1)

    # ---- training --------------------------------------------------------------------------------
    def loss(self, X, y, theta=None, bias=None):
        theta = self.theta if theta is None else theta
        bias = self.bias if bias is None else bias
        return float(0.5 * np.mean((self.expectation(X, theta) + bias - y) ** 2))

    def gradient(self, X, y, theta=None, bias=None, method=None):
        """Exact gradient of the loss, and ∂/∂b. method: 'adjoint' (default) or 'shift'."""
        theta = self.theta if theta is None else theta
        bias = self.bias if bias is None else bias
        if (method or self.gradient_method) == 'adjoint':
            return self._adjoint(X, np.asarray(y, float), theta, bias)
        start = self._start(X)
        residual = self._forward(start, theta) + bias - y
        grad = np.zeros(len(theta))
        for k in range(len(theta)):
            shift = np.zeros(len(theta))
            shift[k] = math.pi / 2
            d = (self._forward(start, theta + shift) - self._forward(start, theta - shift)) / 2
            grad[k] = float(np.mean(residual * d))
        return grad, float(np.mean(residual))

    def _adjoint(self, X, y, theta, bias):
        """One forward pass, one backward pass. For f = ⟨ψ|Z₀|ψ⟩ and L = ½ mean((f + b − y)²):
        ∂L/∂θₖ = mean(r · ∂f/∂θₖ) with ∂f/∂θₖ = 2 Re⟨Z₀ψ| … ∂Gₖ … ⟩, carried backwards gate by gate;
        ∂RY(θ)/∂θ = ½ RY(θ + π) exactly."""
        n = self.qubits
        phi = self._start(X).copy()
        ops = []                                                             # the trainable part, in order
        for layer in range(self.layers):
            for q in range(n):
                ops.append(('RY', q, layer * n + q))
            ops += [('CX', gate.targets, None) for gate in self._ring()]
        for kind, where, k in ops:                                           # forward
            phi = self._ry(phi, where, theta[k]) if kind == 'RY' else self._cx(phi, *where)
        z0 = 1 - 2 * ((np.arange(2 ** n) >> (n - 1)) & 1)
        f = (np.abs(phi) ** 2) @ z0
        residual = f + bias - y
        lam = phi * z0 * (residual / len(y))[:, None]                        # weighted Z₀|ψ⟩ per sample
        grad = np.zeros(len(theta))
        for kind, where, k in reversed(ops):                                 # backward
            if kind == 'CX':
                phi, lam = self._cx(phi, *where), self._cx(lam, *where)      # CX is its own inverse
                continue
            phi = self._ry(phi, where, -theta[k])                            # the state before this gate
            mu = 0.5 * self._ry(phi.copy(), where, theta[k] + math.pi)       # ∂RY/∂θ applied to it
            grad[k] = 2 * float(np.real(np.sum(lam.conj() * mu)))
            lam = self._ry(lam, where, -theta[k])
        self._last = (np.array(theta, float), float(bias), f)               # reused by the progress report
        return grad, float(np.mean(residual))

    def _loss_and_gradient(self, X, y, theta, bias):
        """(loss, gradient incl. ∂/∂b) from a single adjoint pass."""
        grad, grad_bias = self._adjoint(X, y, theta, bias)
        f = self._last[2]
        return float(0.5 * np.mean((f + bias - y) ** 2)), np.r_[grad, grad_bias]

    def train(self, X, y, method='BFGS', steps=100, rate=0.1, callback=None):
        """Lower the loss. callback(step, loss, accuracy) after every step; return False to stop.
        Returns the history: a list of (step, loss, training accuracy)."""
        X, y = np.asarray(X, float), np.asarray(y, float)
        history = []

        def report(theta, bias):
            self.theta, self.bias = np.array(theta), float(bias)
            last = getattr(self, '_last', None)
            if last is not None and last[1] == self.bias and np.array_equal(last[0], self.theta):
                f = last[2]                                              # already computed at this point
            else:
                f = self.expectation(X)
            out = f + self.bias
            entry = (len(history), float(0.5 * np.mean((out - y) ** 2)), float(np.mean(np.where(out >= 0, 1, -1) == y)))
            history.append(entry)
            return callback is None or callback(*entry) is not False
        report(self.theta, self.bias)
        if method == 'BFGS':
            from scipy.optimize import minimize
            stop = [False]

            def objective(v):                                            # loss and gradient together
                if self.gradient_method == 'adjoint':
                    return self._loss_and_gradient(X, y, v[:-1], v[-1])
                g, gb = self.gradient(X, y, v[:-1], v[-1])
                return self.loss(X, y, v[:-1], v[-1]), np.r_[g, gb]

            def step(v):
                if not stop[0] and not report(v[:-1], v[-1]):
                    stop[0] = True
                    raise StopIteration
            try:
                result = minimize(objective, np.r_[self.theta, self.bias], jac=True, method='BFGS',
                                  callback=step, options={'maxiter': int(steps), 'gtol': 1e-6})
                self.theta, self.bias = result.x[:-1], float(result.x[-1])
            except StopIteration:
                pass
            return history
        if method != 'Adam':
            raise ValueError(f'Unknown method {method!r}')
        m, v = np.zeros(len(self.theta) + 1), np.zeros(len(self.theta) + 1)
        params = np.r_[self.theta, self.bias]
        for t in range(1, int(steps) + 1):
            g, gb = self.gradient(X, y, params[:-1], params[-1])
            g = np.r_[g, gb]
            m = 0.9 * m + 0.1 * g
            v = 0.999 * v + 0.001 * g * g
            params = params - rate * (m / (1 - 0.9 ** t)) / (np.sqrt(v / (1 - 0.999 ** t)) + 1e-8)
            if not report(params[:-1], params[-1]):
                break
        return history
