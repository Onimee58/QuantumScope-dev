"""Optional whole-window checks for the many-class Variational Classifier (QUANTUMSCOPE_GUI_TESTS=1; own process)."""
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
    w.resize(1400, 900)
    w.show()
    yield w
    module.QtInteractor = original


def test_three_species_with_one_circuit_and_the_circuit_in_the_simulator(window):
    from quantumscope.gui import qml_experiments as Q
    from quantumscope.ml import evaluation as E, variational as V
    w = window
    w._launch_qml_variational()
    v = w._open_experiments['qml_variational']
    v.data.source.setCurrentIndex(v.data.source.findData('iris'))
    v.data.qubits.setValue(4)
    v.loss_box.setCurrentIndex(v.loss_box.findData('hinge'))
    v.data.class_a.setCurrentIndex(v.data.class_a.findData(Q.ALL))
    assert v.loss_box.currentData() == 'cross-entropy' and not v.loss_box.isEnabled()   # the only loss for many classes
    v.data.class_a.setCurrentIndex(v.data.class_a.findText('setosa'))
    assert v.loss_box.currentData() == 'hinge' and v.loss_box.isEnabled()               # the student's choice comes back
    v.data.class_a.setCurrentIndex(v.data.class_a.findData(Q.ALL))
    v.layers.setValue(3)
    v.steps.setValue(120)
    v.train().wait()
    w.repaint()
    p = v.prepared
    assert p.k == 3 and isinstance(v.model, V.MultiClassifier) and '3 classes, one outcome per class' in v.data.summary.text()
    assert v.last['test'] >= 0.85 and 'read from 2 qubits' in v.result.text()
    assert v.evaluation.shown_confusion.shape == (3, 3)
    expected = E.multi_metrics(p.y_test, v.model.predict(p.X_test), 3)
    assert v.evaluation.metrics.confusion.tolist() == expected.confusion.tolist()
    assert v.model_panel.model.k == 3 and 'read from 2 qubits, one outcome per class' in v.model_panel.summary.text()
    x = v.open_in_circuit()
    circuit = w.circuit_widget
    assert w.categories.currentWidget() is w.workspaces['circuits'] and circuit.n == 4
    assert sorted(circuit.model.measurements) == [0, 1] and 'Measure q0…q1' in circuit.status.text()
    state = circuit.model.simulate().column_states[-1]
    outcomes = (np.abs(state.reshape(4, 4)) ** 2).sum(axis=1)          # q0 q1: the class's outcome
    assert np.allclose(outcomes, v.model.expectation(x[None])[0], atol=1e-10)


def test_too_few_qubits_for_the_classes_are_explained(window):
    from quantumscope.gui import qml_experiments as Q
    v = window._open_experiments['qml_variational']
    v.data.source.setCurrentIndex(v.data.source.findData('digits'))
    v.data.qubits.setValue(3)
    v.data.class_a.setCurrentIndex(v.data.class_a.findData(Q.ALL))
    assert v.train() is None and 'use at least 4 qubits' in v.result.text()


def test_v095_report_button_news_bar_and_about(window, monkeypatch):
    from quantumscope.gui import preferences as prefs
    from quantumscope.gui import report_dialog as R
    from quantumscope.gui.main_window import AboutDialog
    tools = {b.toolTip(): b for b in window.findChildren(QtWidgets.QToolButton)}
    assert 'Report a problem' in tools
    opened = []
    monkeypatch.setattr(R.ReportDialog, 'exec', lambda self: opened.append(self))
    tools['Report a problem'].click()
    assert opened and opened[0].info()['Area'] and 'Open tab' in opened[0].info()
    about = AboutDialog(window)
    about.report_button.click()
    assert len(opened) == 2
    prefs._settings().remove('news/check')
    assert window.start_news() is None and window.news_bar.isVisible()          # asks; reads nothing yet
    window.news_bar.decline.click()
    assert not window.news_bar.isVisible()
    prefs._settings().remove('news/check')


def test_v096_meter_and_hydrogen_memory_check(window, monkeypatch):
    from quantumscope.gui import resource_monitor as RM
    w = window
    assert w.resource_monitor.label in w.statusBar().findChildren(QtWidgets.QLabel)
    assert w.resource_monitor.tick().total > 0 and w.resource_monitor.label.text().startswith(('QuantumScope', '⚠'))
    asked = []
    monkeypatch.setattr(RM, 'confirm_memory', lambda parent, needed, what, sample=None: asked.append((needed, what)) or False)
    w._memory_accepted = set()
    density = w.density
    w.resolution.setValue(160)
    w.refresh()
    assert asked and asked[-1][1].startswith('A 160³ grid') and w.density is density      # not redrawn
    assert 'Not drawn' in w.statusBar().currentMessage()
    monkeypatch.setattr(RM, 'confirm_memory', lambda parent, needed, what, sample=None: asked.append(what) or True)
    w.resolution.setValue(48)
    w.refresh()
    assert w.density.shape == (48, 48, 48)
