"""v0.8.2 (18b): Save model…, Load model… and Predict on a file… in the Quantum ML classifiers."""
import csv
import os

import numpy as np
import pytest

if os.environ.get('QUANTUMSCOPE_GUI_TESTS') != '1':
    pytest.skip('GUI tests are opt-in: set QUANTUMSCOPE_GUI_TESTS=1', allow_module_level=True)

QtWidgets = pytest.importorskip('PySide6.QtWidgets')


@pytest.fixture(scope='module')
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


@pytest.fixture
def messages(monkeypatch):
    shown = []
    for kind in ('information', 'warning'):
        monkeypatch.setattr(QtWidgets.QMessageBox, kind, staticmethod(lambda *a, **k: shown.append(a[2])))
    return shown


def test_kernel_model_save_load_predict_export(app, tmp_path, messages):
    from quantumscope.gui import qml_experiments as Q
    from quantumscope.ml import datasets as D
    k = Q.KernelExperiment()
    assert not k.model_panel.save_button.isEnabled() and not k.model_panel.predict_button.isEnabled()
    k.data.source.setCurrentIndex(k.data.source.findData('mnist'))
    k.data.qubits.setValue(4)
    k.data.class_a.setCurrentIndex(k.data.class_a.findText('3'))
    k.data.class_b.setCurrentIndex(k.data.class_b.findText('8'))
    k.feature_map.setCurrentIndex(k.feature_map.findData('angle'))
    k.bandwidth.setValue(0.5)
    trained = k.train().wait()
    assert k.model_panel.save_button.isEnabled() and 'Trained just now' in k.model_panel.summary.text()
    path = k.model_panel.save(str(tmp_path / 'digits'))
    assert path.endswith('.npz') and 'Saved as digits.npz' in k.model_panel.summary.text()
    fresh = Q.KernelExperiment()                                         # another window loads it
    fresh.model_panel.load(path)
    assert fresh.bandwidth.value() == pytest.approx(0.5) and fresh.feature_map.currentData() == 'angle'
    assert fresh.data.source.currentData() == 'mnist' and fresh.data.class_a.currentText() == '3'
    assert fresh.train().wait()['test'] == pytest.approx(trained['test'])   # Train rebuilds the same model
    fresh.model_panel.load(path)
    ds = D.load('mnist')
    np.savez(tmp_path / 'new.npz', images=ds.X[1000:1300].reshape(-1, 28, 28), y=ds.y[1000:1300])
    fresh.model_panel.predict_file(str(tmp_path / 'new.npz')).wait()
    dialog = fresh.model_panel.dialog
    known = int(np.isin(ds.y[1000:1300], (3, 8)).sum())
    assert dialog.table.rowCount() == 300 and 'labelled samples of these two classes' in dialog.summary.text()
    assert f'{300 - known} samples belong to other classes' in dialog.summary.text()
    assert 0.7 <= dialog.correct <= 1.0
    rows = list(csv.reader(open(dialog.export(str(tmp_path / 'out')))))
    assert rows[0] == ['sample', 'prediction', 'decision', 'true_class'] and len(rows) == 301
    Q.VariationalExperiment().model_panel.load(path)                     # the wrong experiment
    assert 'open it in the Quantum Kernel Classifier' in messages[-1]
    (tmp_path / 'junk.npz').write_bytes(b'not a model')
    assert fresh.model_panel.load(str(tmp_path / 'junk.npz')) is None and 'could not be loaded' in messages[-1]


def test_variational_model_predicts_a_reordered_csv(app, tmp_path):
    from quantumscope.gui import qml_experiments as Q
    from quantumscope.ml import datasets as D
    v = Q.VariationalExperiment()
    v.data.source.setCurrentIndex(v.data.source.findData('breast_cancer'))
    v.data.qubits.setValue(4)
    v.steps.setValue(30)
    v.train().wait()
    other = Q.VariationalExperiment()
    other.model_panel.load(v.model_panel.save(str(tmp_path / 'bc.npz')))
    assert other.layers.value() == v.layers.value() and other.data.qubits.value() == 4
    bc = D.load('breast_cancer')
    with open(tmp_path / 'new.csv', 'w', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(list(reversed(bc.features)))                      # other order, no labels
        for i in range(0, 569, 9):
            writer.writerow(list(reversed(bc.X[i].tolist())))
    other.model_panel.predict_file(str(tmp_path / 'new.csv')).wait()
    dialog = other.model_panel.dialog
    assert dialog.correct is None and dialog.table.columnCount() == 3 and dialog.table.rowCount() == 64
