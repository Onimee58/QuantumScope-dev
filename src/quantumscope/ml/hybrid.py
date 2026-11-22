"""Hybrid quantum–classical neural networks (v1.1.0), in NumPy.

A network is a list of layers, each with a forward pass and a backward pass (backpropagation written
out, so every number can be shown and checked): dense, 1-D and 2-D convolution, max and average
pooling, global average pooling, dropout, batch normalisation, flatten, activations, and quantum
layers. A quantum layer takes q numbers, writes them into q qubits as rotation angles, applies
trainable rotations and entangling gates, and returns the q expectation values ⟨Z⟩. Its gradients,
with respect to its weights and to its inputs (so training reaches the classical layers before it),
come from the adjoint method: one backward sweep through the circuit, however many parameters
(Jones & Gacon, 2020). The last layer is always a dense layer with one output per class, trained
with softmax cross-entropy and Adam.

Shapes: a sample is a vector (features,), a sequence (length, channels) or an image
(height, width, channels); a batch adds a first axis. Convolutions are matrix multiplications, one
per kernel position, which run in NumPy's compiled linear algebra.

The classical twin of a network replaces each quantum layer by a dense layer of the same width
(tanh), for an honest comparison. No Qt here.
"""
import math
import time
from dataclasses import dataclass, field

import numpy as np

MAX_QUBITS = 8
ACTIVATIONS = ('linear', 'relu', 'leaky_relu', 'tanh', 'sigmoid', 'gelu')
LAYERS = {                      # type: (name shown, default settings)
    'dense': ('Dense', {'units': 16, 'activation': 'relu'}),
    'conv1d': ('Conv1D', {'filters': 8, 'kernel': 3, 'stride': 1, 'padding': 'valid', 'activation': 'relu'}),
    'conv2d': ('Conv2D', {'filters': 8, 'kernel': 3, 'stride': 1, 'padding': 'valid', 'activation': 'relu'}),
    'maxpool1d': ('MaxPool1D', {'size': 2}),
    'avgpool1d': ('AvgPool1D', {'size': 2}),
    'maxpool2d': ('MaxPool2D', {'size': 2}),
    'avgpool2d': ('AvgPool2D', {'size': 2}),
    'globalavg': ('GlobalAveragePooling', {}),
    'dropout': ('Dropout', {'rate': 0.2}),
    'batchnorm': ('BatchNorm', {}),
    'flatten': ('Flatten', {}),
    'activation': ('Activation', {'activation': 'relu'}),
    'quantum': ('Quantum layer', {'qubits': 4, 'layers': 2, 'entanglement': 'ring', 'scale': math.pi}),
}


class ShapeError(ValueError):
    """A layer does not fit the shape it receives; the message says what to change."""


# ---- activations ---------------------------------------------------------------------------------
def _act(name, z):
    if name == 'relu':
        return np.maximum(z, 0)
    if name == 'leaky_relu':
        return np.where(z > 0, z, 0.01 * z)
    if name == 'tanh':
        return np.tanh(z)
    if name == 'sigmoid':
        return 1 / (1 + np.exp(-np.clip(z, -60, 60)))
    if name == 'gelu':
        return 0.5 * z * (1 + np.tanh(0.7978845608028654 * (z + 0.044715 * z ** 3)))
    return z


def _act_grad(name, z):
    if name == 'relu':
        return (z > 0).astype(z.dtype)
    if name == 'leaky_relu':
        return np.where(z > 0, 1.0, 0.01)
    if name == 'tanh':
        return 1 - np.tanh(z) ** 2
    if name == 'sigmoid':
        s = 1 / (1 + np.exp(-np.clip(z, -60, 60)))
        return s * (1 - s)
    if name == 'gelu':
        u = 0.7978845608028654 * (z + 0.044715 * z ** 3)
        t = np.tanh(u)
        return 0.5 * (1 + t) + 0.5 * z * (1 - t ** 2) * 0.7978845608028654 * (1 + 3 * 0.044715 * z ** 2)
    return np.ones_like(z)


# ---- layers --------------------------------------------------------------------------------------
class Layer:
    kind = ''
    quantum = False

    def __init__(self, **settings):
        self.settings = dict(LAYERS[self.kind][1], **settings)
        self.params, self.grads = {}, {}

    def build(self, shape, rng):
        """Make the parameters for an input of `shape` (one sample); returns the output shape."""
        return shape

    def forward(self, x, training=False):
        return x

    def backward(self, g):
        return g

    @property
    def size(self):
        return int(sum(p.size for p in self.params.values()))

    def short(self):
        """A compact description, for lists: 'Conv2D 8 × 3×3, same, relu'."""
        s, name = self.settings, LAYERS[self.kind][0]
        act = f", {s['activation'].replace('_', ' ')}" if s.get('activation', 'linear') != 'linear' else ''
        if self.kind == 'dense':
            return f"Dense {s['units']}{act}"
        if self.kind in ('conv1d', 'conv2d'):
            k = f"{s['kernel']}×{s['kernel']}" if self.kind == 'conv2d' else f"kernel {s['kernel']}"
            stride = f", stride {s['stride']}" if int(s['stride']) != 1 else ''
            return f"{name} {s['filters']} × {k}, {s['padding']}{stride}{act}"
        if 'size' in s:
            return f"{name} {s['size']}"
        if self.kind == 'dropout':
            return f"Dropout {float(s['rate']):g}"
        if self.kind == 'activation':
            return f"Activation {s['activation'].replace('_', ' ')}"
        return name

    def describe(self):
        name = LAYERS[self.kind][0]
        shown = ', '.join(f'{k} {v:g}' if isinstance(v, float) else f'{k} {v}' for k, v in self.settings.items()
                          if not (k == 'scale'))
        return f'{name} ({shown})' if shown else name


class _Activated(Layer):
    def _activate(self, z):
        self._z = z
        return _act(self.settings.get('activation', 'linear'), z)

    def _deactivate(self, g):
        return g * _act_grad(self.settings.get('activation', 'linear'), self._z)


class Dense(_Activated):
    kind = 'dense'

    def build(self, shape, rng):
        if len(shape) != 1:
            raise ShapeError(f'Dense needs a vector, but receives {_shape(shape)}: add Flatten or global average '
                             'pooling before it')
        n, units = shape[0], int(self.settings['units'])
        limit = math.sqrt(6 / (n + units))
        self.params = {'W': rng.uniform(-limit, limit, (n, units)), 'b': np.zeros(units)}
        return (units,)

    def forward(self, x, training=False):
        self._x = x
        return self._activate(x @ self.params['W'] + self.params['b'])

    def backward(self, g):
        g = self._deactivate(g)
        self.grads = {'W': self._x.T @ g, 'b': g.sum(0)}
        return g @ self.params['W'].T


class Conv2D(_Activated):
    kind = 'conv2d'

    def build(self, shape, rng):
        if len(shape) != 3:
            raise ShapeError(f'Conv2D needs an image (height × width × channels), but receives {_shape(shape)}')
        h, w, c = shape
        k, s, f = int(self.settings['kernel']), int(self.settings['stride']), int(self.settings['filters'])
        self.pad = (k - 1) // 2 if self.settings['padding'] == 'same' else 0
        ho, wo = (h + 2 * self.pad - k) // s + 1, (w + 2 * self.pad - k) // s + 1
        if ho < 1 or wo < 1:
            raise ShapeError(f'Conv2D with a {k}×{k} kernel does not fit a {h}×{w} image: use a smaller kernel, '
                             'padding "same", or less pooling before it')
        limit = math.sqrt(6 / (k * k * c + k * k * f))
        self.params = {'W': rng.uniform(-limit, limit, (k, k, c, f)), 'b': np.zeros(f)}
        self.out = (ho, wo)
        return (ho, wo, f)

    def forward(self, x, training=False):
        p = self.pad
        if p:
            x = np.pad(x, ((0, 0), (p, p), (p, p), (0, 0)))
        self._x = x
        k, s = self.params['W'].shape[0], int(self.settings['stride'])
        ho, wo = self.out
        z = np.zeros((x.shape[0], ho, wo, self.params['W'].shape[3]))
        for i in range(k):
            for j in range(k):
                z += x[:, i:i + s * ho:s, j:j + s * wo:s, :] @ self.params['W'][i, j]
        return self._activate(z + self.params['b'])

    def backward(self, g):
        g = self._deactivate(g)
        x, W = self._x, self.params['W']
        k, s = W.shape[0], int(self.settings['stride'])
        ho, wo = self.out
        dW, dx = np.zeros_like(W), np.zeros_like(x)
        flat = g.reshape(-1, g.shape[-1])
        for i in range(k):
            for j in range(k):
                patch = x[:, i:i + s * ho:s, j:j + s * wo:s, :]
                dW[i, j] = patch.reshape(-1, patch.shape[-1]).T @ flat
                dx[:, i:i + s * ho:s, j:j + s * wo:s, :] += g @ W[i, j].T
        self.grads = {'W': dW, 'b': flat.sum(0)}
        p = self.pad
        return dx[:, p:-p, p:-p, :] if p else dx


class Conv1D(_Activated):
    kind = 'conv1d'

    def build(self, shape, rng):
        if len(shape) != 2:
            raise ShapeError(f'Conv1D needs a sequence (length × channels), but receives {_shape(shape)}')
        n, c = shape
        k, s, f = int(self.settings['kernel']), int(self.settings['stride']), int(self.settings['filters'])
        self.pad = (k - 1) // 2 if self.settings['padding'] == 'same' else 0
        lo = (n + 2 * self.pad - k) // s + 1
        if lo < 1:
            raise ShapeError(f'Conv1D with kernel {k} does not fit a sequence of length {n}: use a smaller kernel '
                             'or padding "same"')
        limit = math.sqrt(6 / (k * c + k * f))
        self.params = {'W': rng.uniform(-limit, limit, (k, c, f)), 'b': np.zeros(f)}
        self.out = lo
        return (lo, f)

    def forward(self, x, training=False):
        p = self.pad
        if p:
            x = np.pad(x, ((0, 0), (p, p), (0, 0)))
        self._x = x
        k, s, lo = self.params['W'].shape[0], int(self.settings['stride']), self.out
        z = np.zeros((x.shape[0], lo, self.params['W'].shape[2]))
        for i in range(k):
            z += x[:, i:i + s * lo:s, :] @ self.params['W'][i]
        return self._activate(z + self.params['b'])

    def backward(self, g):
        g = self._deactivate(g)
        x, W = self._x, self.params['W']
        k, s, lo = W.shape[0], int(self.settings['stride']), self.out
        dW, dx = np.zeros_like(W), np.zeros_like(x)
        flat = g.reshape(-1, g.shape[-1])
        for i in range(k):
            patch = x[:, i:i + s * lo:s, :]
            dW[i] = patch.reshape(-1, patch.shape[-1]).T @ flat
            dx[:, i:i + s * lo:s, :] += g @ W[i].T
        self.grads = {'W': dW, 'b': flat.sum(0)}
        p = self.pad
        return dx[:, p:-p, :] if p else dx


class _Pool(Layer):
    dims = 2
    mode = 'max'

    def build(self, shape, rng):
        if len(shape) != self.dims + 1:
            what = 'an image (height × width × channels)' if self.dims == 2 else 'a sequence (length × channels)'
            raise ShapeError(f'{LAYERS[self.kind][0]} needs {what}, but receives {_shape(shape)}')
        size = int(self.settings['size'])
        out = tuple(n // size for n in shape[:-1])
        if min(out) < 1:
            raise ShapeError(f'{LAYERS[self.kind][0]} of size {size} is larger than its input {_shape(shape)}')
        self.out = out
        return out + (shape[-1],)

    def forward(self, x, training=False):
        size = int(self.settings['size'])
        self._shape = x.shape
        if self.dims == 2:
            ho, wo = self.out
            v = x[:, :ho * size, :wo * size, :].reshape(x.shape[0], ho, size, wo, size, x.shape[-1])
            axes = (2, 4)
        else:
            lo, = self.out
            v = x[:, :lo * size, :].reshape(x.shape[0], lo, size, x.shape[-1])
            axes = (2,)
        if self.mode == 'avg':
            return v.mean(axis=axes)
        out = v.max(axis=axes)
        self._mask = v == np.expand_dims(out, axes)
        self._mask = self._mask / self._mask.sum(axis=axes, keepdims=True)    # ties share the gradient
        return out

    def backward(self, g):
        size = int(self.settings['size'])
        dx = np.zeros(self._shape)
        if self.dims == 2:
            ho, wo = self.out
            spread = np.expand_dims(g, (2, 4))
            block = self._mask * spread if self.mode == 'max' else np.broadcast_to(spread / size ** 2,
                                                                                   (g.shape[0], ho, size, wo, size, g.shape[-1]))
            dx[:, :ho * size, :wo * size, :] = block.reshape(g.shape[0], ho * size, wo * size, g.shape[-1])
        else:
            lo, = self.out
            spread = np.expand_dims(g, 2)
            block = self._mask * spread if self.mode == 'max' else np.broadcast_to(spread / size,
                                                                                   (g.shape[0], lo, size, g.shape[-1]))
            dx[:, :lo * size, :] = block.reshape(g.shape[0], lo * size, g.shape[-1])
        return dx


class MaxPool2D(_Pool):
    kind, dims, mode = 'maxpool2d', 2, 'max'


class AvgPool2D(_Pool):
    kind, dims, mode = 'avgpool2d', 2, 'avg'


class MaxPool1D(_Pool):
    kind, dims, mode = 'maxpool1d', 1, 'max'


class AvgPool1D(_Pool):
    kind, dims, mode = 'avgpool1d', 1, 'avg'


class GlobalAverage(Layer):
    kind = 'globalavg'

    def build(self, shape, rng):
        if len(shape) < 2:
            raise ShapeError('Global average pooling needs an image or a sequence, but receives a vector')
        return (shape[-1],)

    def forward(self, x, training=False):
        self._shape = x.shape
        return x.mean(axis=tuple(range(1, x.ndim - 1)))

    def backward(self, g):
        n = int(np.prod(self._shape[1:-1]))
        return np.broadcast_to(g.reshape((g.shape[0],) + (1,) * (len(self._shape) - 2) + (g.shape[-1],)) / n,
                               self._shape).copy()


class Dropout(Layer):
    kind = 'dropout'

    def build(self, shape, rng):
        rate = float(self.settings['rate'])
        if not 0 <= rate < 1:
            raise ShapeError('Dropout rate must be at least 0 and below 1')
        self.rng = rng
        return shape

    def forward(self, x, training=False):
        rate = float(self.settings['rate'])
        if not training or rate == 0:
            self._mask = None
            return x
        self._mask = (self.rng.random(x.shape) >= rate) / (1 - rate)
        return x * self._mask

    def backward(self, g):
        return g if self._mask is None else g * self._mask


class BatchNorm(Layer):
    kind = 'batchnorm'
    momentum, eps = 0.9, 1e-5

    def build(self, shape, rng):
        c = shape[-1]
        self.params = {'gamma': np.ones(c), 'beta': np.zeros(c)}
        self.mean, self.var = np.zeros(c), np.ones(c)
        return shape

    def forward(self, x, training=False):
        axes = tuple(range(x.ndim - 1))
        if training:
            mean, var = x.mean(axes), x.var(axes)
            self.mean = self.momentum * self.mean + (1 - self.momentum) * mean
            self.var = self.momentum * self.var + (1 - self.momentum) * var
        else:
            mean, var = self.mean, self.var
        self._inv = 1 / np.sqrt(var + self.eps)
        self._xhat = (x - mean) * self._inv
        self._training = training
        return self.params['gamma'] * self._xhat + self.params['beta']

    def backward(self, g):
        axes = tuple(range(g.ndim - 1))
        self.grads = {'gamma': (g * self._xhat).sum(axes), 'beta': g.sum(axes)}
        gx = g * self.params['gamma']
        if not self._training:
            return gx * self._inv
        m = g.size / g.shape[-1]
        return self._inv / m * (m * gx - gx.sum(axes) - self._xhat * (gx * self._xhat).sum(axes))


class Flatten(Layer):
    kind = 'flatten'

    def build(self, shape, rng):
        return (int(np.prod(shape)),)

    def forward(self, x, training=False):
        self._shape = x.shape
        return x.reshape(x.shape[0], -1)

    def backward(self, g):
        return g.reshape(self._shape)


class Activation(_Activated):
    kind = 'activation'

    def forward(self, x, training=False):
        return self._activate(x)

    def backward(self, g):
        return self._deactivate(g)


class Quantum(Layer):
    """q numbers in → RY(scale·x) on each qubit → `layers` × (RY, RZ on every qubit, then CNOTs) →
    ⟨Z⟩ of each qubit out. Batched statevector simulation; adjoint gradients."""
    kind = 'quantum'
    quantum = True

    def build(self, shape, rng):
        q = int(self.settings['qubits'])
        if not 1 <= q <= MAX_QUBITS:
            raise ShapeError(f'A quantum layer has 1 to {MAX_QUBITS} qubits')
        if len(shape) != 1 or shape[0] != q:
            got = _shape(shape)
            raise ShapeError(f'A {q}-qubit layer needs {q} numbers in (one angle per qubit), but receives {got}: '
                             f'put a Dense layer with {q} units (tanh) before it'
                             + (', after Flatten' if len(shape) > 1 else ''))
        L = int(self.settings['layers'])
        self.q = q
        self.params = {'theta': rng.uniform(0, 2 * math.pi, (L, q, 2))}
        dim = 2 ** q
        index = np.arange(dim)
        self.bits = [(index >> (q - 1 - k)) & 1 for k in range(q)]           # qubit 0 = leftmost bit
        self.z = np.array([1 - 2 * b for b in self.bits], float)             # ⟨Z_k⟩ signs, (q, dim)
        pairs = {'ring': [(k, (k + 1) % q) for k in range(q)] if q > 2 else [(0, 1)] if q == 2 else [],
                 'line': [(k, k + 1) for k in range(q - 1)], 'none': []}[self.settings['entanglement']]
        self.cnots = [np.where(self.bits[c] == 1, index ^ (1 << (q - 1 - t)), index) for c, t in pairs]
        return (q,)

    def describe(self):
        s = self.settings
        return f"Quantum layer ({s['qubits']} qubits, {s['layers']} layers, {s['entanglement']} entanglement)"

    def short(self):
        s = self.settings
        return f"Quantum {s['qubits']} qubits × {s['layers']} layers, {s['entanglement']}"

    # gates on a batch of states (B, 2**q)
    def _one(self, state, k, m):
        """Apply 2×2 matrices m — (2, 2) for all, or (B, 2, 2) per sample — on qubit k."""
        B = state.shape[0]
        v = state.reshape(B, 2 ** k, 2, 2 ** (self.q - k - 1))
        if m.ndim == 2:
            v = np.einsum('ij,bajc->baic', m, v)
        else:
            v = np.einsum('bij,bajc->baic', m, v)
        return v.reshape(B, -1)

    @staticmethod
    def _ry(a):
        c, s = np.cos(a / 2), np.sin(a / 2)
        return np.array([[c, -s], [s, c]]) if np.ndim(a) == 0 else np.stack([np.stack([c, -s], -1),
                                                                             np.stack([s, c], -1)], -2)

    @staticmethod
    def _dry(a):
        c, s = np.cos(a / 2), np.sin(a / 2)
        return 0.5 * (np.array([[-s, -c], [c, -s]]) if np.ndim(a) == 0 else
                      np.stack([np.stack([-s, -c], -1), np.stack([c, -s], -1)], -2))

    @staticmethod
    def _rz(a):
        return np.array([[np.exp(-0.5j * a), 0], [0, np.exp(0.5j * a)]])

    @staticmethod
    def _drz(a):
        return np.array([[-0.5j * np.exp(-0.5j * a), 0], [0, 0.5j * np.exp(0.5j * a)]])

    def _gates(self, angles):
        """The circuit as a list: (kind, qubit, which) — which is the input column or (layer, qubit, 0/1)."""
        gates = [('ry_in', k, k) for k in range(self.q)]
        for l in range(self.params['theta'].shape[0]):
            for k in range(self.q):
                gates.append(('ry', k, (l, k, 0)))
                gates.append(('rz', k, (l, k, 1)))
            gates.extend(('cx', c, None) for c in range(len(self.cnots)))
        return gates

    def _apply(self, state, gate, angles, inverse=False):
        kind, k, which = gate
        sign = -1 if inverse else 1
        if kind == 'cx':
            return state[:, self.cnots[k]]
        if kind == 'ry_in':
            return self._one(state, k, self._ry(sign * angles[:, which]))
        a = sign * self.params['theta'][which]
        return self._one(state, k, self._ry(a) if kind == 'ry' else self._rz(a))

    def forward(self, x, training=False):
        angles = float(self.settings['scale']) * x
        B = x.shape[0]
        state = np.zeros((B, 2 ** self.q), complex)
        state[:, 0] = 1
        for gate in self._gates(angles):
            state = self._apply(state, gate, angles)
        self._angles, self._state = angles, state
        return (np.abs(state) ** 2) @ self.z.T

    def backward(self, g):
        angles, gates = self._angles, self._gates(self._angles)
        phi = self._state
        lam = (g @ self.z) * phi                                  # (Σ g_k Z_k) |ψ⟩, per sample
        d_theta = np.zeros_like(self.params['theta'])
        d_angles = np.zeros_like(angles)
        for gate in reversed(gates):
            kind, k, which = gate
            phi = self._apply(phi, gate, angles, inverse=True)
            if kind == 'ry_in':
                dphi = self._one(phi, k, self._dry(angles[:, which]))
                d_angles[:, which] = 2 * np.real(np.sum(np.conj(lam) * dphi, axis=1))
            elif kind in ('ry', 'rz'):
                a = self.params['theta'][which]
                dphi = self._one(phi, k, self._dry(a) if kind == 'ry' else self._drz(a))
                d_theta[which] = 2 * np.real(np.sum(np.conj(lam) * dphi))
            lam = self._apply(lam, gate, angles, inverse=True)
        self.grads = {'theta': d_theta}
        return d_angles * float(self.settings['scale'])


KINDS = {cls.kind: cls for cls in (Dense, Conv1D, Conv2D, MaxPool1D, AvgPool1D, MaxPool2D, AvgPool2D,
                                   GlobalAverage, Dropout, BatchNorm, Flatten, Activation, Quantum)}


def _shape(shape):
    return '×'.join(str(n) for n in shape) if len(shape) > 1 else f'{shape[0]} numbers'


def make_layer(spec):
    spec = dict(spec)
    return KINDS[spec.pop('type')](**spec)


# ---- the network ---------------------------------------------------------------------------------
def softmax(z):
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


@dataclass
class History:
    loss: list = field(default_factory=list)
    accuracy: list = field(default_factory=list)
    val_loss: list = field(default_factory=list)
    val_accuracy: list = field(default_factory=list)
    seconds: float = 0.0
    stopped: bool = False


class Network:
    """A list of layer specs (dicts with 'type' and settings), then the output layer (one unit per
    class). Raises ShapeError, naming the layer, when a layer does not fit."""

    def __init__(self, input_shape, specs, classes, seed=0):
        self.input_shape, self.specs, self.classes = tuple(input_shape), [dict(s) for s in specs], int(classes)
        self.rng = np.random.default_rng(seed)
        self.layers, self.shapes = [], [self.input_shape]
        shape = self.input_shape
        for n, spec in enumerate(self.specs, 1):
            layer = make_layer(spec)
            try:
                shape = layer.build(shape, self.rng)
            except ShapeError as exc:
                raise ShapeError(f'Layer {n}, {LAYERS[layer.kind][0]}: {exc}') from None
            self.layers.append(layer)
            self.shapes.append(shape)
        if len(shape) != 1:
            raise ShapeError(f'The output layer needs a vector, but the last layer gives {_shape(shape)}: '
                             'end with Flatten or global average pooling')
        self.output = Dense(units=self.classes, activation='linear')
        self.output.build(shape, self.rng)
        self.shapes.append((self.classes,))
        self.adam = {}

    @property
    def all_layers(self):
        return self.layers + [self.output]

    def counts(self):
        """(classical parameters, quantum parameters)."""
        quantum = sum(l.size for l in self.layers if l.quantum)
        return sum(l.size for l in self.all_layers) - quantum, quantum

    def summary(self):
        """One line per layer: what it is, its output shape and its parameters."""
        rows = [('Input', self.input_shape, 0)]
        rows += [(l.describe(), s, l.size) for l, s in zip(self.layers, self.shapes[1:])]
        rows.append((f'Output (dense, {self.classes} classes, softmax)', (self.classes,), self.output.size))
        return rows

    def forward(self, x, training=False):
        for layer in self.all_layers:
            x = layer.forward(x, training)
        return x

    def predict_proba(self, X, batch=256):
        return np.vstack([softmax(self.forward(X[i:i + batch])) for i in range(0, len(X), batch)])

    def predict(self, X):
        return self.predict_proba(X).argmax(1)

    def loss_and_backward(self, X, y, training=True):
        """Mean cross-entropy, and the gradients in each layer's .grads."""
        logits = self.forward(X, training)
        p = softmax(logits)
        n = len(y)
        loss = -np.mean(np.log(p[np.arange(n), y] + 1e-12))
        g = p.copy()
        g[np.arange(n), y] -= 1
        g /= n
        for layer in reversed(self.all_layers):
            g = layer.backward(g)
        return loss, p

    def step(self, lr, beta1=0.9, beta2=0.999, eps=1e-8):
        for i, layer in enumerate(self.all_layers):
            for name, value in layer.params.items():
                grad = layer.grads.get(name)
                if grad is None:
                    continue
                m, v, t = self.adam.get((i, name), (np.zeros_like(value), np.zeros_like(value), 0))
                t += 1
                m = beta1 * m + (1 - beta1) * grad
                v = beta2 * v + (1 - beta2) * grad ** 2
                value -= lr * (m / (1 - beta1 ** t)) / (np.sqrt(v / (1 - beta2 ** t)) + eps)
                self.adam[(i, name)] = (m, v, t)

    def fit(self, X, y, X_val=None, y_val=None, epochs=10, batch=32, lr=0.01, progress=None, cancelled=None):
        """Train with Adam on shuffled mini-batches. progress(epoch, history) after each epoch;
        cancelled() is checked between batches. Returns a History."""
        history, start = History(), time.time()
        n = len(y)
        for epoch in range(1, int(epochs) + 1):
            order = self.rng.permutation(n)
            total, right = 0.0, 0
            for i in range(0, n, int(batch)):
                if cancelled is not None and cancelled():
                    history.stopped = True
                    history.seconds = time.time() - start
                    return history
                idx = order[i:i + int(batch)]
                loss, p = self.loss_and_backward(X[idx], y[idx])
                self.step(lr)
                total += loss * len(idx)
                right += int((p.argmax(1) == y[idx]).sum())
            history.loss.append(total / n)
            history.accuracy.append(right / n)
            if X_val is not None and len(X_val):
                vl, va = self.evaluate(X_val, y_val)
                history.val_loss.append(vl)
                history.val_accuracy.append(va)
            history.seconds = time.time() - start
            if progress is not None:
                progress(epoch, history)
        return history

    def evaluate(self, X, y):
        p = self.predict_proba(X)
        return float(-np.mean(np.log(p[np.arange(len(y)), y] + 1e-12))), float((p.argmax(1) == y).mean())


def twin_specs(specs):
    """The classical twin: every quantum layer replaced by a dense layer of the same width (tanh)."""
    return [{'type': 'dense', 'units': int(s.get('qubits', LAYERS['quantum'][1]['qubits'])), 'activation': 'tanh'}
            if s['type'] == 'quantum' else dict(s) for s in specs]


def preset(name, input_shape, qubits=4):
    """Ready-made networks to start from."""
    image, sequence = len(input_shape) == 3, len(input_shape) == 2
    q = qubits
    to_qubits = [{'type': 'dense', 'units': q, 'activation': 'tanh'},
                 {'type': 'quantum', 'qubits': q, 'layers': 2, 'entanglement': 'ring', 'scale': math.pi}]
    if name == 'cnn':
        if image:
            return [{'type': 'conv2d', 'filters': 8, 'kernel': 3, 'stride': 1, 'padding': 'same', 'activation': 'relu'},
                    {'type': 'maxpool2d', 'size': 2}, {'type': 'flatten'},
                    {'type': 'dense', 'units': 32, 'activation': 'relu'}, {'type': 'dropout', 'rate': 0.2}] + to_qubits
        if sequence:
            return [{'type': 'conv1d', 'filters': 8, 'kernel': 3, 'stride': 1, 'padding': 'same', 'activation': 'relu'},
                    {'type': 'maxpool1d', 'size': 2}, {'type': 'flatten'},
                    {'type': 'dense', 'units': 16, 'activation': 'relu'}] + to_qubits
    if name == 'quantum_only':
        return ([{'type': 'flatten'}] if len(input_shape) > 1 else []) + to_qubits
    return ([{'type': 'flatten'}] if len(input_shape) > 1 else []) + \
        [{'type': 'dense', 'units': 16, 'activation': 'relu'}] + to_qubits      # 'dense'


PRESETS = (('cnn', 'Small CNN → quantum layer'), ('dense', 'Dense → quantum layer'),
           ('quantum_only', 'Quantum layer alone (after one dense layer)'))


# ---- data ----------------------------------------------------------------------------------------
@dataclass
class Data:
    X_train: np.ndarray
    y_train: np.ndarray
    X_test: np.ndarray
    y_test: np.ndarray
    classes: list
    input_shape: tuple
    note: str = ''


def prepare(dataset, *, shape='auto', per_class=None, test_fraction=0.25, seed=0):
    """Training and test data for a network, from a datasets.Dataset: images keep their shape
    (height, width, 1) and are scaled to [0, 1]; other data are features, standardised with the
    training data's mean and spread (shape 'sequence' gives (features, 1), for Conv1D). Missing
    values become the training mean. Stratified split; per_class caps the samples of each class."""
    rng = np.random.default_rng(seed)
    X, y = np.asarray(dataset.X, float), np.asarray(dataset.y, int)
    keep = []
    for c in range(len(dataset.classes)):
        idx = np.flatnonzero(y == c)
        rng.shuffle(idx)
        keep.append(idx[:per_class] if per_class else idx)
    train, test = [], []
    for idx in keep:
        cut = max(1, int(round(len(idx) * (1 - test_fraction)))) if len(idx) > 1 else len(idx)
        train.extend(idx[:cut])
        test.extend(idx[cut:])
    train, test = np.array(train, int), np.array(test, int)
    rng.shuffle(train)
    is_image = dataset.image_shape is not None and shape in ('auto', 'image')
    if is_image:
        top = np.nanmax(X) or 1.0
        X = np.nan_to_num(X / top)
        h, w = dataset.image_shape[:2]
        X = X.reshape(len(X), h, w, -1)
        note = f'images {h}×{w}, scaled to [0, 1]'
    else:
        mean = np.nanmean(X[train], 0)
        X = np.where(np.isnan(X), mean, X)
        spread = X[train].std(0)
        spread[spread == 0] = 1
        X = (X - mean) / spread
        if shape == 'sequence':
            X = X[:, :, None]
            note = f'a sequence of {X.shape[1]} values, standardised'
        else:
            note = f'{X.shape[1]} features, standardised'
    return Data(X[train], y[train], X[test], y[test], list(dataset.classes), X.shape[1:], note)


def confusion(y_true, y_pred, k):
    m = np.zeros((k, k), int)
    np.add.at(m, (y_true, y_pred), 1)
    return m
