"""v0.9.16: the Run on IBM Quantum hardware… dialog (QUANTUMSCOPE_GUI_TESTS=1)."""
import os

import pytest

if os.environ.get('QUANTUMSCOPE_GUI_TESTS') != '1':
    pytest.skip('GUI tests are opt-in: set QUANTUMSCOPE_GUI_TESTS=1', allow_module_level=True)

QtWidgets = pytest.importorskip('PySide6.QtWidgets')


@pytest.fixture(scope='module')
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


@pytest.fixture
def dialog(app):
    from quantumscope.gui.circuit_workspace import CircuitWorkspace
    from quantumscope.physics.circuits import Gate
    w = CircuitWorkspace()
    w.show_generated_circuit(2, [Gate('H', (0,)), Gate('CX', (0, 1))], '', '')
    d = w.run_on_hardware()
    yield d
    d.close()
    w.close()


def test_the_dialog_shows_the_four_steps_for_this_circuit(dialog):
    assert [g.title()[:2] for g in dialog.groups] == ['1.', '2.', '3.', '4.']
    run = dialog.editors[3].toPlainText()
    assert 'qreg q[2];' in run and 'cx q[0],q[1];' in run and 'MEASURED = [0, 1]' in run


def test_typing_fills_in_the_code_in_place(dialog):
    editor = dialog.editors[1]
    dialog.api_key.setText('K' * 44)
    dialog.crn.setText('crn:v1:test')
    assert dialog.editors[1] is editor and 'K' * 44 in editor.toPlainText() and dialog.warning.text() == ''
    dialog.shots.setValue(2000)
    assert 'SHOTS = 2000' in dialog.editors[3].toPlainText()
    dialog.credentials.setCurrentIndex(dialog.credentials.findData('code'))
    assert len(dialog.editors) == 3 and 'K' * 44 in dialog.editors[2].toPlainText()
    assert 'do not share' in dialog.warning.text()


def test_copy_and_save_never_keep_the_key(dialog, tmp_path):
    from PySide6.QtGui import QGuiApplication
    dialog.api_key.setText('S' * 44)
    dialog.groups[3].findChild(QtWidgets.QPushButton).click()
    assert 'qasm2.loads' in QGuiApplication.clipboard().text()
    path = dialog.save(str(tmp_path / 'run'))
    text = open(path).read()
    assert path.endswith('.py') and 'S' * 44 not in text and 'QiskitRuntimeService()' in text
    settings = os.environ.get('QUANTUMSCOPE_SETTINGS_FILE')
    if settings and os.path.exists(settings):
        assert 'S' * 44 not in open(settings, encoding='utf-8', errors='replace').read()


def test_noise_is_mentioned_and_left_out(app):
    from quantumscope.gui.circuit_workspace import CircuitWorkspace
    from quantumscope.physics.circuits import Gate
    from quantumscope.physics.noise import NoiseModel
    w = CircuitWorkspace()
    w.show_generated_circuit(1, [Gate('H', (0,))], '', '')
    w.model.noise_model = NoiseModel(enabled=True, single=0.05)
    d = w.run_on_hardware()
    assert w.model.noise_model.active and 'noise settings are left out' in d.warning.text()
    assert 'Note: QuantumScope noise settings' in d.editors[3].toPlainText()       # also said in the code
    d.close()
    w.close()
