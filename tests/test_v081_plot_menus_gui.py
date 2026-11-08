"""v0.8.1: chart right-click menus. pyqtgraph's "Plot Options" (FFT, log, derivative, …) crashed on
scatter plots ('ScatterPlotItem' object has no attribute 'setFftMode'); every chart now hides it and
keeps View All, the axis options and Export…."""
import os
import re

import pytest

ROOT = os.path.join(os.path.dirname(__file__), '..', 'src', 'quantumscope')


def test_every_chart_in_the_source_is_tidied():
    for folder, _, files in os.walk(ROOT):
        for name in files:
            if name.endswith('.py'):
                text = open(os.path.join(folder, name), encoding='utf-8').read()
                for line in text.splitlines():
                    if 'pg.PlotWidget(' in line:
                        assert 'tidy(' in line, f'{name}: {line.strip()}'


if os.environ.get('QUANTUMSCOPE_GUI_TESTS') != '1':
    pytest.skip('GUI tests are opt-in: set QUANTUMSCOPE_GUI_TESTS=1', allow_module_level=True)

QtWidgets = pytest.importorskip('PySide6.QtWidgets')


@pytest.fixture(scope='module')
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def _plot_items(widget):
    import pyqtgraph as pg
    return [w.getPlotItem() for w in widget.findChildren(pg.PlotWidget)]


def _check(items):
    assert items
    for item in items:
        assert item.getContextMenus(None) is None                      # no "Plot Options" (FFT, log, …)
        menu = item.getViewBox().menu                                  # but View All and Export… remain
        assert item.getViewBox().menuEnabled() and menu is not None
        assert any('View All' in a.text() for a in menu.actions())


def test_quantum_ml_and_vqls_charts(app):
    from quantumscope.gui import qml_experiments as Q
    from quantumscope.gui.circuit_workspace import CircuitWorkspace
    v = Q.VariationalExperiment()
    v.data.source.setCurrentIndex(v.data.source.findData('moons'))
    v.steps.setValue(5)
    v.train()                                                          # scatter plots now on the chart
    for widget in (Q.DatasetsExperiment(), Q.KernelExperiment(), v):
        _check(_plot_items(widget))
    w = CircuitWorkspace()
    w.load_library('vqls', {'problem': 'single', 'layers': 1})
    _check(_plot_items(w.show_vqls_solution()))


def test_physics_charts(app):
    from quantumscope.gui.double_slit_dialog import DoubleSlitDialog
    from quantumscope.gui.entanglement_experiment import EntanglementDialog
    for dialog in (DoubleSlitDialog(), EntanglementDialog()):
        _check(_plot_items(dialog))
