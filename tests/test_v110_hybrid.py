"""v1.1.0: hybrid quantum–classical networks in NumPy: every layer's backward pass agrees with
numerical differentiation, the quantum layer agrees with the simulator, and training learns."""
import math

import numpy as np
import pytest

from quantumscope.ml import hybrid as H


def numeric_check(input_shape, specs, classes=3, n=5, seed=1, tol=1e-5):
    """Compare every gradient (parameters and input) with central differences of the loss."""
    net = H.Network(input_shape, specs, classes, seed=seed)
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n,) + tuple(input_shape))
    y = rng.integers(0, classes, n)
    # the input gradient: run backward and keep what reaches the first layer
    logits = net.forward(X, training=True)
    p = H.softmax(logits)
    g = p.copy()
    g[np.arange(n), y] -= 1
    g /= n
    for layer in reversed(net.all_layers):
        g = layer.backward(g)
    analytic_x = g
    analytic = {(i, k): v.copy() for i, l in enumerate(net.all_layers) for k, v in l.grads.items()}

    def loss():
        q = H.softmax(net.forward(X, training=True))
        return -np.mean(np.log(q[np.arange(n), y] + 1e-12))
    eps = 1e-6
    for (i, k), grad in analytic.items():
        value = net.all_layers[i].params[k]
        flat = value.reshape(-1)
        for j in rng.choice(flat.size, size=min(flat.size, 6), replace=False):
            old = flat[j]
            flat[j] = old + eps
            up = loss()
            flat[j] = old - eps
            down = loss()
            flat[j] = old
            assert grad.reshape(-1)[j] == pytest.approx((up - down) / (2 * eps), abs=tol), (i, k, j)
    flat = X.reshape(-1)
    for j in rng.choice(flat.size, size=min(flat.size, 6), replace=False):
        old = flat[j]
        flat[j] = old + eps
        up = loss()
        flat[j] = old - eps
        down = loss()
        flat[j] = old
        assert analytic_x.reshape(-1)[j] == pytest.approx((up - down) / (2 * eps), abs=tol), ('input', j)


@pytest.mark.parametrize('activation', H.ACTIVATIONS)
def test_dense_and_activations(activation):
    numeric_check((4,), [{'type': 'dense', 'units': 5, 'activation': activation}])


@pytest.mark.parametrize('padding, stride', [('valid', 1), ('same', 1), ('valid', 2)])
def test_conv2d(padding, stride):
    numeric_check((6, 6, 2), [{'type': 'conv2d', 'filters': 3, 'kernel': 3, 'stride': stride, 'padding': padding,
                               'activation': 'tanh'}, {'type': 'flatten'}])


@pytest.mark.parametrize('padding, stride', [('valid', 1), ('same', 2)])
def test_conv1d(padding, stride):
    numeric_check((9, 2), [{'type': 'conv1d', 'filters': 3, 'kernel': 3, 'stride': stride, 'padding': padding,
                            'activation': 'gelu'}, {'type': 'flatten'}])


@pytest.mark.parametrize('kind, shape', [('maxpool2d', (5, 6, 2)), ('avgpool2d', (5, 6, 2)),
                                         ('maxpool1d', (7, 2)), ('avgpool1d', (7, 2))])
def test_pooling(kind, shape):
    numeric_check(shape, [{'type': kind, 'size': 2}, {'type': 'flatten'}])


def test_global_average_batchnorm_dropout_and_activation_layers():
    numeric_check((4, 4, 3), [{'type': 'batchnorm'}, {'type': 'activation', 'activation': 'sigmoid'},
                              {'type': 'globalavg'}])
    numeric_check((6,), [{'type': 'dense', 'units': 4, 'activation': 'relu'}, {'type': 'batchnorm'}])
    net = H.Network((10,), [{'type': 'dropout', 'rate': 0.5}], 2)
    x = np.ones((4, 10))
    assert np.array_equal(net.layers[0].forward(x), x)                  # no dropout outside training
    kept = net.layers[0].forward(x, training=True)
    assert set(np.unique(kept)) <= {0.0, 2.0}                             # the rest scaled up


@pytest.mark.parametrize('entanglement', ['ring', 'line', 'none'])
def test_quantum_layer_gradients(entanglement):
    numeric_check((3,), [{'type': 'dense', 'units': 3, 'activation': 'tanh'},
                         {'type': 'quantum', 'qubits': 3, 'layers': 2, 'entanglement': entanglement}], tol=1e-6)


def test_the_quantum_layer_matches_the_circuit_simulator():
    """⟨Z⟩ from the layer equals a direct statevector simulation of the same circuit."""
    net = H.Network((2,), [{'type': 'quantum', 'qubits': 2, 'layers': 1, 'entanglement': 'ring', 'scale': 1.0}], 2)
    layer = net.layers[0]
    theta = layer.params['theta']
    x = np.array([[0.3, -1.1]])
    out = layer.forward(x)

    def ry(a):
        return np.array([[np.cos(a / 2), -np.sin(a / 2)], [np.sin(a / 2), np.cos(a / 2)]])

    def rz(a):
        return np.diag([np.exp(-0.5j * a), np.exp(0.5j * a)])
    state = np.kron(ry(0.3) @ [1, 0], ry(-1.1) @ [1, 0])
    state = np.kron(rz(theta[0, 0, 1]) @ ry(theta[0, 0, 0]), rz(theta[0, 1, 1]) @ ry(theta[0, 1, 0])) @ state
    cx = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]])
    state = cx @ state                                                   # qubit 0 controls qubit 1
    probs = np.abs(state) ** 2
    z0 = probs @ [1, 1, -1, -1]
    z1 = probs @ [1, -1, 1, -1]
    assert out[0] == pytest.approx([z0, z1], abs=1e-12)


def test_shapes_and_mistakes_are_explained():
    net = H.Network((28, 28, 1), H.preset('cnn', (28, 28, 1)), 10)
    assert net.shapes[1] == (28, 28, 8) and net.shapes[2] == (14, 14, 8) and net.shapes[-1] == (10,)
    classical, quantum = net.counts()
    assert quantum == 4 * 2 * 2 and classical > 0
    with pytest.raises(H.ShapeError, match='Layer 2, Quantum layer.*Dense layer with 4 units'):
        H.Network((8,), [{'type': 'dense', 'units': 6}, {'type': 'quantum', 'qubits': 4}], 2)
    with pytest.raises(H.ShapeError, match='Layer 1, Conv2D.*image'):
        H.Network((8,), [{'type': 'conv2d'}], 2)
    with pytest.raises(H.ShapeError, match='Dense needs a vector.*Flatten'):
        H.Network((8, 8, 1), [{'type': 'dense'}], 2)
    with pytest.raises(H.ShapeError, match='output layer needs a vector'):
        H.Network((8, 8, 1), [{'type': 'conv2d'}], 2)


def test_the_twin_swaps_quantum_layers_for_dense_ones():
    specs = H.preset('dense', (5,))
    twin = H.twin_specs(specs)
    assert [s['type'] for s in twin] == ['dense', 'dense', 'dense'] and twin[-1] == {'type': 'dense', 'units': 4,
                                                                                       'activation': 'tanh'}
    assert H.Network((5,), twin, 2).counts()[1] == 0


def test_a_hybrid_network_learns():
    from quantumscope.ml import datasets as D
    data = H.prepare(D.load('iris'), test_fraction=0.3, seed=0)
    assert data.input_shape == (4,) and abs(data.X_train.mean()) < 0.2
    net = H.Network(data.input_shape, H.preset('dense', data.input_shape, qubits=3), 3, seed=0)
    seen = []
    history = net.fit(data.X_train, data.y_train, data.X_test, data.y_test, epochs=30, batch=16, lr=0.03,
                      progress=lambda e, h: seen.append(e))
    assert seen == list(range(1, 31)) and history.loss[-1] < history.loss[0]
    assert history.val_accuracy[-1] >= 0.8
    stop = net.fit(data.X_train, data.y_train, epochs=5, cancelled=lambda: True)
    assert stop.stopped and not stop.loss


def test_images_keep_their_shape():
    from quantumscope.ml import datasets as D
    data = H.prepare(D.load('digits'), per_class=20, seed=1)
    assert data.input_shape == (8, 8, 1) and data.X_train.max() <= 1 and len(data.y_train) + len(data.y_test) == 200
    seq = H.prepare(D.load('wine'), shape='sequence')
    assert seq.input_shape == (13, 1)
    assert H.confusion(np.array([0, 1, 1]), np.array([0, 1, 0]), 2).tolist() == [[1, 0], [1, 1]]
    assert math.isclose(H.LAYERS['quantum'][1]['scale'], math.pi)
