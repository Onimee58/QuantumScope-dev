"""A variational quantum classifier (NumPy and SciPy, no Qt).

For a data point x (one feature per qubit) the circuit is
    feature map U(x), then `layers` × [RY(θ) on every qubit, then a ring of CNOTs],
and the model's output is f(x) = ⟨Z₀⟩ + b, between −1 and 1 plus a bias b; the predicted class is
sign(f). Training lowers the mean squared error ½·mean((f − y)²) for labels y = ±1, with exact
gradients. The whole training set is simulated at once.

More classes (v0.9.4, MultiClassifier): the same circuit, but r = ⌈log₂ k⌉ readout qubits are
measured and each outcome is a class (outcome c, in binary on q0 … q(r−1), is class c; outcomes
beyond k − 1 are discarded and the rest renormalized). With a learned offset b_c per class,
P(c | x) = p_c e^(b_c) / Σ p_c′ e^(b_c′), trained by cross-entropy. Ten digits need 4 readout qubits.

Gradients (v0.8.1): by default the adjoint method, which needs one forward and one backward pass
however many parameters there are (Jones & Gacon, 2020). The parameter-shift rule, two circuit runs
per parameter as on real hardware, gives the same numbers and stays available (gradient='shift').
"""
import math

import numpy as np

from quantumscope.ml import kernels
from quantumscope.physics.circuits import Gate


EPS = 1e-9


def _mse(out, y):
    return 0.5 * (out - y) ** 2, out - y


def _hinge(out, y):
    margin = y * out
    return np.maximum(0.0, 1 - margin), np.where(margin < 1, -y, 0.0)


def _cross_entropy(out, y):
    p = np.clip((1 + out) / 2, EPS, 1 - EPS)                   # the output as a probability of +1
    t = (1 + y) / 2
    inside = ((1 + out) / 2 > EPS) & ((1 + out) / 2 < 1 - EPS)
    return -(t * np.log(p) + (1 - t) * np.log(1 - p)), np.where(inside, -(t / p - (1 - t) / (1 - p)) / 2, 0.0)


LOSSES = {'mse': _mse, 'hinge': _hinge, 'cross-entropy': _cross_entropy}   # value and ∂/∂output, per sample


class Classifier:
    def __init__(self, qubits, layers=2, feature_map='angle', reps=1, bandwidth=1.0, seed=0, gradient='adjoint',
                 loss='mse'):
        if loss not in LOSSES:
            raise ValueError(f'Unknown loss {loss!r}')
        self.loss_name = loss
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

    def _evolve(self, start, theta):
        """The final states of the trainable circuit for every starting state."""
        states = start.copy()
        for layer in range(self.layers):
            for q in range(self.qubits):
                states = self._ry(states, q, theta[layer * self.qubits + q])
            for gate in self._ring():
                states = self._cx(states, *gate.targets)
        return states

    # ---- the readout: hooks that MultiClassifier replaces -------------------------------------------
    def _z0(self):
        return 1 - 2 * ((np.arange(2 ** self.qubits) >> (self.qubits - 1)) & 1)   # Z on q0

    def _raw(self, states):
        """What is measured: ⟨Z₀⟩ for each state."""
        return (np.abs(states) ** 2) @ self._z0()

    def _head(self, raw, y, bias):
        """From the measured values to the model's output: (loss per sample, ∂loss/∂raw per sample,
        mean ∂loss/∂bias, output). Two classes: output f = ⟨Z₀⟩ + b."""
        out = raw + bias
        values, slope = LOSSES[self.loss_name](out, y)
        return values, slope, float(np.mean(slope)), out

    def _weights(self, slope):
        """The diagonal observable whose expectation's gradient is the loss's (per sample, per basis state)."""
        return slope[:, None] * self._z0()

    def _correct(self, out, y):
        return np.where(out >= 0, 1, -1) == y

    def _unpack(self, v):
        return v[:-1], float(v[-1])

    def _forward(self, start, theta):
        return self._raw(self._evolve(start, theta))

    def _key(self, X):
        X = np.ascontiguousarray(X, float)
        return (X.shape, hash(X.tobytes()), self.feature_map, self.reps, self.bandwidth)

    def _start(self, X):
        """The feature-map states of X, computed once per data set and kept for a few data sets (training
        and validation data alternate every step)."""
        key = self._key(X)
        if not isinstance(self._cache, dict):
            self._cache = {}
        if key not in self._cache:
            if len(self._cache) >= 4:
                self._cache.pop(next(iter(self._cache)))
            self._cache[key] = kernels.states(np.ascontiguousarray(X, float), self.feature_map, self.reps, self.bandwidth)
        return self._cache[key]

    def expectation(self, X, theta=None):
        """The measured values for every row of X: ⟨Z₀⟩ (two classes), or the readout outcomes'
        probabilities (more classes)."""
        theta = self.theta if theta is None else theta
        return self._forward(self._start(X), theta)

    def decision(self, X):
        return self._head(self.expectation(X), np.zeros(len(np.atleast_2d(X))), self.bias)[3]

    def predict(self, X):
        return np.where(self.decision(X) >= 0, 1, -1)

    # ---- training --------------------------------------------------------------------------------
    def loss(self, X, y, theta=None, bias=None):
        theta = self.theta if theta is None else theta
        bias = self.bias if bias is None else bias
        return float(np.mean(self._head(self.expectation(X, theta), np.asarray(y, float), bias)[0]))

    def gradient(self, X, y, theta=None, bias=None, method=None):
        """Exact gradient of the loss, and ∂/∂b. method: 'adjoint' (default) or 'shift'."""
        theta = self.theta if theta is None else theta
        bias = self.bias if bias is None else bias
        if (method or self.gradient_method) == 'adjoint':
            return self._adjoint(X, np.asarray(y, float), theta, bias)
        start = self._start(X)
        _, slope, grad_bias, _ = self._head(self._forward(start, theta), np.asarray(y, float), bias)
        grad = np.zeros(len(theta))
        for k in range(len(theta)):
            shift = np.zeros(len(theta))
            shift[k] = math.pi / 2
            d = (self._forward(start, theta + shift) - self._forward(start, theta - shift)) / 2
            grad[k] = float(np.mean(np.sum((slope * d).reshape(len(d), -1), axis=1)))
        return grad, grad_bias

    def _adjoint(self, X, y, theta, bias):
        """One forward pass, one backward pass. The loss's slope makes a diagonal observable W per sample
        (W = r·Z₀ for two classes); ∂L/∂θₖ = 2 Re⟨Wψ| … ∂Gₖ … ⟩ / N, carried backwards gate by gate;
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
        raw = self._raw(phi)
        _, slope, grad_bias, _ = self._head(raw, y, bias)
        lam = phi * self._weights(slope) / len(y)                            # weighted W|ψ⟩ per sample
        grad = np.zeros(len(theta))
        for kind, where, k in reversed(ops):                                 # backward
            if kind == 'CX':
                phi, lam = self._cx(phi, *where), self._cx(lam, *where)      # CX is its own inverse
                continue
            phi = self._ry(phi, where, -theta[k])                            # the state before this gate
            mu = 0.5 * self._ry(phi.copy(), where, theta[k] + math.pi)       # ∂RY/∂θ applied to it
            grad[k] = 2 * float(np.real(np.sum(lam.conj() * mu)))
            lam = self._ry(lam, where, -theta[k])
        self._last = (np.array(theta, float), np.array(bias, float), raw, self._key(X))   # reused by the report
        return grad, grad_bias

    def _loss_and_gradient(self, X, y, theta, bias):
        """(loss, gradient incl. ∂/∂b) from a single adjoint pass."""
        grad, grad_bias = self._adjoint(X, y, theta, bias)
        return float(np.mean(self._head(self._last[2], y, bias)[0])), np.r_[grad, grad_bias]

    def train(self, X, y, method='BFGS', steps=100, rate=0.1, callback=None, validation=None, patience=0,
              min_delta=1e-4, batch_size=0, seed=0):
        """Lower the loss. callback(step, loss, accuracy) after every step, or callback(step, loss,
        accuracy, (validation loss, validation accuracy)) when validation=(X_val, y_val) is given;
        return False to stop. Returns the history: a list of (step, loss, training accuracy).

        patience: with validation data, stop when the validation loss has not improved by min_delta
        for this many steps, and restore the parameters of the best step (early stopping).
        batch_size: Adam only, each step on a random batch of this many samples (0: all).
        After training, self.validation holds (step, validation loss, accuracy) and self.stopped_early
        says whether early stopping ended it (self.best_step: the step whose parameters were kept)."""
        X, y = np.asarray(X, float), np.asarray(y, float)
        if batch_size and method != 'Adam':
            raise ValueError('Mini-batches need the Adam optimizer (BFGS relies on the full loss)')
        if patience and validation is None:
            raise ValueError('Early stopping needs validation data')
        history, self.validation, self.stopped_early, self.best_step = [], [], False, None
        best = {'loss': np.inf, 'step': 0, 'params': None}
        data_key = self._key(X)

        def score(raw, labels):
            values, _, _, out = self._head(raw, labels, self.bias)
            return float(np.mean(values)), float(np.mean(self._correct(out, labels)))

        def report(theta, bias):
            self.theta = np.array(theta)
            self.bias = np.array(bias, float) if np.ndim(bias) else float(bias)
            last = getattr(self, '_last', None)
            if (last is not None and np.array_equal(last[1], self.bias) and np.array_equal(last[0], self.theta)
                    and last[3] == data_key):                           # the same parameters AND the same data
                raw = last[2]                                            # already computed at this point
            else:
                raw = self.expectation(X)
            entry = (len(history), *score(raw, y))
            history.append(entry)
            extra = ()
            if validation is not None:
                v = score(self.expectation(validation[0]), np.asarray(validation[1], float))
                self.validation.append((entry[0], *v))
                extra = (v,)
                if v[0] < best['loss'] - min_delta:
                    best.update(loss=v[0], step=entry[0], params=(self.theta.copy(), np.copy(self.bias)))
                elif patience and entry[0] - best['step'] >= patience:
                    self.stopped_early = True
            keep_going = callback is None or callback(*entry, *extra) is not False
            return keep_going and not self.stopped_early

        def finish():
            if self.stopped_early and best['params'] is not None:      # back to the best step
                self.theta = best['params'][0].copy()
                self.bias = best['params'][1] if np.ndim(best['params'][1]) else float(best['params'][1])
                self.best_step = best['step']
            return history
        report(self.theta, self.bias)
        if method == 'BFGS':
            from scipy.optimize import minimize
            stop = [False]

            def objective(v):                                            # loss and gradient together
                theta, bias = self._unpack(v)
                if self.gradient_method == 'adjoint':
                    return self._loss_and_gradient(X, y, theta, bias)
                g, gb = self.gradient(X, y, theta, bias)
                return self.loss(X, y, theta, bias), np.r_[g, gb]

            def step(v):
                if not stop[0] and not report(*self._unpack(v)):
                    stop[0] = True
                    raise StopIteration
            try:
                result = minimize(objective, np.r_[self.theta, self.bias], jac=True, method='BFGS',
                                  callback=step, options={'maxiter': int(steps), 'gtol': 1e-6})
                self.theta, self.bias = self._unpack(result.x)
            except StopIteration:
                pass
            return finish()
        if method != 'Adam':
            raise ValueError(f'Unknown method {method!r}')
        rng = np.random.default_rng(seed)
        params = np.r_[self.theta, self.bias]
        m, v = np.zeros(len(params)), np.zeros(len(params))
        for t in range(1, int(steps) + 1):
            rows = rng.choice(len(y), size=min(int(batch_size), len(y)), replace=False) if batch_size else slice(None)
            g, gb = self.gradient(X[rows], y[rows], *self._unpack(params))
            g = np.r_[g, gb]
            m = 0.9 * m + 0.1 * g
            v = 0.999 * v + 0.001 * g * g
            params = params - rate * (m / (1 - 0.9 ** t)) / (np.sqrt(v / (1 - 0.999 ** t)) + 1e-8)
            if not report(*self._unpack(params)):
                break
        return finish()


def readout_qubits(k):
    """Qubits whose outcomes name k classes: ⌈log₂ k⌉ (at least 1)."""
    return max(1, math.ceil(math.log2(k)))


class MultiClassifier(Classifier):
    """k classes from one circuit (v0.9.4): measure the first ⌈log₂ k⌉ qubits; outcome c is class c.
    Labels are 0 … k−1; decision(X) gives P(class | x), one column per class; the loss is cross-entropy."""

    def __init__(self, qubits, classes, layers=2, feature_map='angle', reps=1, bandwidth=1.0, seed=0,
                 gradient='adjoint'):
        super().__init__(qubits, layers, feature_map, reps, bandwidth, seed, gradient, loss='cross-entropy')
        self.k = int(classes)
        self.readout = readout_qubits(self.k)
        if self.k < 2:
            raise ValueError('A classifier needs at least two classes')
        if self.readout > self.qubits:
            raise ValueError(f'{self.k} classes need at least {self.readout} qubits (their outcomes name the '
                             f'classes); this circuit has {self.qubits}')
        self.bias = np.zeros(self.k)

    def outcome_of_basis(self):
        """For every basis state, the readout outcome (its first r bits, q0 most significant)."""
        return np.arange(2 ** self.qubits) >> (self.qubits - self.readout)

    def _raw(self, states):
        """P(outcome) on the readout qubits, for each state: samples × 2^r."""
        probs = np.abs(states) ** 2
        return probs.reshape(len(states), 2 ** self.readout, -1).sum(axis=2)

    def _head(self, raw, y, bias):
        p = np.clip(raw[:, :self.k], EPS, None)                      # outcomes that name a class
        weighted = p * np.exp(np.asarray(bias, float) - np.max(bias))
        total = weighted.sum(axis=1, keepdims=True)
        P = weighted / total                                           # P(class | x)
        y = np.asarray(y).astype(int)
        values = -np.log(P[np.arange(len(y)), y])
        slope = np.zeros_like(raw)                                     # ∂(−log P_y)/∂p_j
        slope[:, :self.k] = (weighted / p) / total
        slope[np.arange(len(y)), y] -= 1.0 / p[np.arange(len(y)), y]
        onehot = np.zeros_like(P)
        onehot[np.arange(len(y)), y] = 1.0
        return values, slope, (P - onehot).mean(axis=0), P

    def _weights(self, slope):
        return slope[:, self.outcome_of_basis()]

    def _correct(self, out, y):
        return np.argmax(out, axis=1) == np.asarray(y).astype(int)

    def _unpack(self, v):
        return v[:-self.k], np.asarray(v[-self.k:], float)

    def decision(self, X):
        """P(class | x): samples × k."""
        return self._head(self.expectation(X), np.zeros(len(np.atleast_2d(X)), int), self.bias)[3]

    def predict(self, X):
        return np.argmax(self.decision(X), axis=1)
