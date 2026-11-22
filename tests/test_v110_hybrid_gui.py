"""v1.1.0: the Hybrid QNN experiment: build a network layer by layer, train it with its classical
twin (QUANTUMSCOPE_GUI_TESTS=1)."""
import os

import pytest

if os.environ.get('QUANTUMSCOPE_GUI_TESTS') != '1':
    pytest.skip('GUI tests are opt-in: set QUANTUMSCOPE_GUI_TESTS=1', allow_module_level=True)

QtWidgets = pytest.importorskip('PySide6.QtWidgets')


@pytest.fixture(scope='module')
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


@pytest.fixture
def view(app):
    from quantumscope.gui.hybrid_view import HybridExperiment
    v = HybridExperiment()
    v.per_class.setValue(15)
    yield v
    v.close()


def test_it_starts_with_a_small_cnn_on_digits(view):
    assert view.source.currentData() == 'digits' and view.data.input_shape == (8, 8, 1)
    assert [s['type'] for s in view.specs][-1] == 'quantum' and view.train_button.isEnabled()
    assert view.layer_list.item(0).text().startswith('1. Conv2D 8 × 3×3, same, relu  →  8×8×8')
    assert view.layer_list.item(view.layer_list.count() - 1).text().startswith('Output: dense, 10 classes')
    assert '16 quantum parameters' in view.check_label.text()
    assert view.summary.rowCount() == len(view.specs) + 2


def test_layers_are_added_moved_changed_and_checked(view):
    n = len(view.specs)
    view.layer_list.setCurrentRow(n - 1)                              # after the quantum layer
    view.add_layer('dense')
    assert len(view.specs) == n + 1 and view.specs[-1]['type'] == 'dense' and view.train_button.isEnabled()
    view.move_layer(-1)                                               # now between Dense(4) and the quantum layer
    assert view.specs[-2]['type'] == 'dense' and view.specs[-1]['type'] == 'quantum'
    assert not view.train_button.isEnabled() and 'Dense layer with 4 units' in view.check_label.text()
    view.remove_layer()
    assert view.train_button.isEnabled()
    view.layer_list.setCurrentRow(len(view.specs) - 1)                 # the quantum layer's settings
    labels = [view.layer_form.itemAt(r, QtWidgets.QFormLayout.ItemRole.LabelRole).widget().text()
              for r in range(view.layer_form.rowCount())]
    assert labels == ['Qubits', 'Quantum layers', 'Entanglement', 'Angle scale']
    editor = view.layer_form.itemAt(0, QtWidgets.QFormLayout.ItemRole.FieldRole).widget()
    editor.setValue(3)
    editor.editingFinished.emit()
    assert view.specs[-1]['qubits'] == 3 and not view.train_button.isEnabled()   # Dense(4) no longer fits
    view.use('dense')
    assert view.train_button.isEnabled()


def test_training_the_network_and_its_twin(view):
    view.epochs.setValue(3)
    run = view.train()
    assert run is not None and not view.train_button.isEnabled() and view.stop_button.isEnabled()
    done = run.wait(120)
    for _ in range(20):
        QtWidgets.QApplication.processEvents()
    assert set(done) == {'hybrid', 'twin'} and view.train_button.isEnabled()
    text = view.results.text()
    assert 'Hybrid network' in text and 'Classical twin' in text and '+ 0 quantum parameters' in text
    assert len(view.lines[('hybrid', 'loss')].getData()[0]) == 3
    assert done['twin'][0].counts()[1] == 0


def test_features_as_a_sequence_and_your_own_file(view, tmp_path):
    view.source.setCurrentIndex(view.source.findData('wine'))
    view.input_as.setCurrentIndex(view.input_as.findData('sequence'))
    assert view.data.input_shape == (13, 1)
    view.use('cnn')
    assert view.specs[0]['type'] == 'conv1d' and view.train_button.isEnabled()
    path = tmp_path / 'mine.npz'
    import numpy as np
    np.savez(path, X=np.random.default_rng(0).normal(size=(40, 5)), y=np.repeat([0, 1], 20))
    view.input_as.setCurrentIndex(view.input_as.findData('features'))
    view.import_file(str(path))
    assert view.source.currentText() == 'Your file: mine.npz' and view.data.input_shape == (5,)
    view.use('dense')
    assert view.train_button.isEnabled()


def test_many_classes_and_too_little_memory_are_handled(view, monkeypatch):
    """v1.1.1: hundreds of classes once filled the confusion matrix with thousands of labels, and a
    network too big for the computer's memory could get QuantumScope stopped by the system."""
    import numpy as np
    from PySide6.QtWidgets import QMessageBox
    from quantumscope.ml.datasets import Dataset
    rng = np.random.default_rng(0)
    view.input_as.setCurrentIndex(view.input_as.findData('features'))
    view.imported = view.dataset = Dataset('many.npz', rng.normal(size=(600, 6)), rng.integers(0, 300, 600),
                                           [f'f{i}' for i in range(6)], [str(i) for i in range(300)], '')
    view._prepare()
    assert 'too few to learn from' in view.data_label.text()
    view.use('dense')
    view.epochs.setValue(1)
    view.twin.setChecked(False)
    view.train().wait(60)
    for _ in range(10):
        QtWidgets.QApplication.processEvents()
    texts = [i for i in view.confusion_plot.items() if type(i).__name__ == 'TextItem']
    assert not texts and '300 classes' in view.confusion_plot.plotItem.titleLabel.text
    import psutil
    monkeypatch.setattr(psutil, 'virtual_memory', lambda: type('M', (), {'available': 1000})())
    asked = []
    monkeypatch.setattr(QMessageBox, 'warning', lambda *a, **k: asked.append(a[2]) or QMessageBox.StandardButton.Cancel)
    assert view.train() is None and 'GB free' in asked[0] and view.run is None
