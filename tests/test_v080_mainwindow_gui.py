"""Optional whole-window checks for the Quantum ML area (QUANTUMSCOPE_GUI_TESTS=1; own process)."""
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
    w.show()
    app.processEvents()
    yield w
    w.close()
    app.processEvents()


def test_quantum_ml_area_and_trained_circuit_in_the_simulator(window):
    w = window
    titles = [w.categories.tabText(i).strip() for i in range(w.categories.count())]
    assert any(t.endswith('Quantum ML') for t in titles) and 'qml' in w.workspaces   # (Math follows, v0.9.0)
    start = w.workspaces['qml']
    assert start.count() == 1 and start.tabText(0) == 'Start'                    # opens on its Start page
    w._launch_qml_variational()
    v = w._open_experiments['qml_variational']
    assert w.workspaces['qml'].indexOf(v) >= 0
    v.data.source.setCurrentIndex(v.data.source.findData('moons'))
    v.steps.setValue(20)
    v.train().wait()
    x = v.open_in_circuit()
    circuit = w.circuit_widget
    assert w.categories.currentWidget() is w.workspaces['circuits'] and circuit.n == 2
    assert float(circuit.model.expectation()) == pytest.approx(float(v.model.expectation(x[None])[0]), abs=1e-10)
    for view in ('qml_datasets', 'qml_kernel', 'qml_variational'):
        w.launch_view(view)                                                       # Try it link names
        assert w.categories.currentWidget() is w.workspaces['qml']
