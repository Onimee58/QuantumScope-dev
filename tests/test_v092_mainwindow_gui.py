"""Optional whole-window checks for quantum annealing (QUANTUMSCOPE_GUI_TESTS=1; own process)."""
import os

import numpy as np
import pytest

if os.environ.get('QUANTUMSCOPE_GUI_TESTS') != '1':
    pytest.skip('GUI tests are opt-in: set QUANTUMSCOPE_GUI_TESTS=1', allow_module_level=True)

QtWidgets = pytest.importorskip('PySide6.QtWidgets')
from gl_support import opengl_app  # noqa: E402


@pytest.fixture(scope='module')
def window():
    app = opengl_app()                       # the window's 3-D views need OpenGL (v0.9.11)
    from quantumscope.gui.main_window import MainWindow
    w = MainWindow()
    w.resize(1400, 900)
    w.show()
    app.processEvents()
    yield w
    w.close()
    app.processEvents()


def _choose(view, key):
    view.problem_box.setCurrentIndex(view.problem_box.findData(key))


def test_annealing_opens_in_the_circuits_area_and_computes(window):
    from quantumscope.physics import annealing as A
    window.launch_view('annealing')
    view = window._open_experiments['annealing']
    assert window.categories.currentWidget() is window.workspaces['circuits']
    _choose(view, 'maxcut:prism')
    view.T.setValue(10)
    view.compute().wait()
    expected = A.anneal(A.maxcut('prism'), 10, record=2, ground=False).final_success
    assert view.result.final_success == pytest.approx(expected, abs=1e-9)
    assert 'Minimum gap' in view.result_label.text() and 'Answers' in view.answers.text()
    assert view.spectrum.minimum_gap > 0
    view.s_slider.setValue(0)                            # at s = 0 every bitstring is equally likely
    assert view.s_label.text() == '0.00'


def test_options_follow_the_problem_and_bad_input_is_explained(window):
    view = window._open_experiments['annealing']
    _choose(view, 'partition')
    assert view.numbers.isEnabled() and not view.text.isEnabled() and not view.seed.isEnabled()
    view.numbers.setText('3, x')
    assert view.compute() is None and 'Numbers' in view.result_label.text()
    _choose(view, 'custom')
    assert view.text.isEnabled() and view.spins.isEnabled()
    view.spins.setValue(3)
    view.text.setText('Z0 Z1 - 0.5 Z2 + 1')
    view.compute().wait()
    assert '010' in view.answers.text() and '100' in view.answers.text()


def test_success_against_time_rises(window):
    view = window._open_experiments['annealing']
    _choose(view, 'maxcut:ring4')
    view.success_curve().wait()
    curve = view.last_curve
    assert curve[-1] > 0.95 and curve[-1] > curve[0]
    assert view.tabs.currentIndex() == 2


def test_the_anneal_opens_as_a_circuit_with_its_energy(window):
    from quantumscope.physics import annealing as A
    view = window._open_experiments['annealing']
    _choose(view, 'maxcut:ring4')
    view.T.setValue(5)
    view.steps.setValue(30)
    workspace = window.circuit_widget
    before = (workspace.model.n, dict(workspace.model.gates), workspace.model.observable)
    view.open_circuit()
    problem = A.maxcut('ring4')
    assert workspace.model.n == 4 and workspace.model.observable == problem.observable
    assert sorted(workspace.model.measurements) == [0, 1, 2, 3]
    state = A.circuit_state(problem, 5, 30)
    energy = float(np.sum(np.abs(state) ** 2 * problem.diagonal))
    assert workspace.model.expectation() == pytest.approx(energy, abs=1e-6)
    assert 'Digitized annealing' in workspace.status.text()
    workspace.model.undo()                               # one undo restores the previous circuit
    assert (workspace.model.n, dict(workspace.model.gates), workspace.model.observable) == before
