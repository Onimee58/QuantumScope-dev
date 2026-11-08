"""v0.9.0 (20c): the Math tab and its Quantum Calculator (QUANTUMSCOPE_GUI_TESTS=1; own process)."""
import os

import numpy as np
import pytest

if os.environ.get('QUANTUMSCOPE_GUI_TESTS') != '1':
    pytest.skip('GUI tests are opt-in: set QUANTUMSCOPE_GUI_TESTS=1', allow_module_level=True)

QtWidgets = pytest.importorskip('PySide6.QtWidgets')
pv = pytest.importorskip('pyvista')
pv.OFF_SCREEN = True


class OffscreenInteractor(QtWidgets.QWidget):
    def __init__(self, parent=None, *a, **k):
        super().__init__(parent)
        self.__dict__['_p'] = pv.Plotter(off_screen=True, window_size=(300, 300))

    def __getattr__(self, name):
        return getattr(self.__dict__['_p'], name)

    def render(self, *a, **k):
        return self.__dict__['_p'].render()


@pytest.fixture(scope='module')
def window():
    QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    import quantumscope.gui.main_window as module
    original = module.QtInteractor
    module.QtInteractor = OffscreenInteractor
    w = module.MainWindow()
    w.show()
    yield w
    module.QtInteractor = original


def evaluate(view, text):
    run = view.set_expression(text, evaluate=True)
    app = QtWidgets.QApplication.instance()
    while run.running():
        app.processEvents()
    app.processEvents()
    return view


def test_math_area_and_calculator(window):
    w = window
    titles = [w.categories.tabText(i).strip() for i in range(w.categories.count())]
    assert titles[-1].endswith('Math') and w.workspaces['math'].tabText(0) == 'Start'
    assert [b.text() for b in w._placeholders['math']._buttons] == ['Quantum Calculator']
    view = w._launch_calculator()
    assert w.categories.currentWidget() is w.workspaces['math']
    evaluate(view, 'CNOT (H ⊗ I)|00⟩')
    assert view.answer.text() == '(1/√2)|00⟩ + (1/√2)|11⟩'
    assert view.matrix.rowCount() == 4 and view.matrix.verticalHeaderItem(3).text() == '|11⟩'
    assert view.steps.count() == 3 and view.history.count() >= 1
    view.digits_button.click()
    while view.run.running():
        QtWidgets.QApplication.instance().processEvents()
    QtWidgets.QApplication.instance().processEvents()
    assert view.calculator.mode == 'digits' and view.answer.text() == '(1/√2)|00⟩ + (1/√2)|11⟩'
    view.exact_button.click()
    while view.run.running():
        QtWidgets.QApplication.instance().processEvents()


def test_errors_named_values_bloch_and_palette(window):
    view = window._launch_calculator()
    view.input.setText('H|0')
    run = view.evaluate()
    while run.running():
        QtWidgets.QApplication.instance().processEvents()
    QtWidgets.QApplication.instance().processEvents()
    assert 'closing ⟩' in view.error.text() and view.input.cursorPosition() == 1         # cursor at the problem
    evaluate(view, 'ψ = (|0⟩ + i|1⟩)/sqrt(2)')
    assert view.answer.text().startswith('ψ = ') and np.allclose(view.bloch.vector, [0, 1, 0])
    assert any(view.variables.item(k).text().startswith('ψ = ') for k in range(view.variables.count()))
    evaluate(view, 'Id(2)/2')
    assert np.allclose(view.bloch.vector, [0, 0, 0])                                     # mixed: the centre
    evaluate(view, 'eig(Y)')
    assert view.answer.text().count('λ = ') == 2 and view.matrix.rowCount() == 0
    view.input.setText('')
    [b for b in view.palette_buttons if b.text() == 'eig'][0].click()
    [b for b in view.palette_buttons if b.text() == '|0⟩'][0].click()
    assert view.input.text() == 'eig(|0⟩)' and view.input.cursorPosition() == len('eig(|0⟩')


def test_send_to_circuit_simulator(window):
    w = window
    view = w._launch_calculator()
    evaluate(view, '(RY(0.7)|0⟩) ⊗ |+⟩')
    state = np.array(view.result.value.evalf(), complex).ravel()
    view.send_button.click()
    model = w.circuit_widget.model
    assert view.send_note.text().startswith('Sent') and model.n == 2
    assert abs(np.vdot(model.initial_vector(), state)) == pytest.approx(1, abs=1e-12)     # exactly that state
    assert w.categories.currentWidget() is w.workspaces['circuits']
    w.circuit_widget.undo()                                                                # undoable
    assert abs(np.vdot(model.initial_vector(), state)) < 1 - 1e-6
    w._launch_calculator()
    evaluate(view, 'CNOT (H ⊗ I)|00⟩')
    view.send_button.click()
    assert 'entangled' in view.send_note.text()
    evaluate(view, 'H')
    assert not view.send_button.isEnabled()                                                # an operator: nothing to send


def test_lesson_links_open_the_calculator(window):
    w = window
    w.launch_view('calculator')
    assert w.categories.currentWidget() is w.workspaces['math']
    run = w.open_calculator('pauli(SWAP)')
    while run.running():
        QtWidgets.QApplication.instance().processEvents()
    QtWidgets.QApplication.instance().processEvents()
    assert w._open_experiments['calculator'].answer.text() == '1/2 II + 1/2 XX + 1/2 YY + 1/2 ZZ'
