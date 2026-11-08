"""v0.8.1: chart right-click menus. pyqtgraph's "Plot Options" (FFT, log, derivative, …) crashed on
scatter plots ('ScatterPlotItem' object has no attribute 'setFftMode'), and its Export dialog opened
squashed with formats that fail (SVG, Matplotlib). Every chart now offers View All, the axis options,
Save image…, Copy image and Save data (CSV)…."""
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
        assert item.scene().contextMenu == []                          # no generic "Export…" dialog
        menu = item.getViewBox().menu
        assert item.getViewBox().menuEnabled() and menu is not None
        texts = [a.text() for a in menu.actions()]
        for wanted in ('View All', 'Save image…', 'Copy image', 'Save data (CSV)…'):
            assert wanted in texts, (wanted, texts)
        assert texts.count('Save image…') == 1                         # added once, even if tidied again


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


def test_save_image_copy_image_and_save_data(app, tmp_path):
    from PySide6.QtGui import QImage
    from quantumscope.gui import plots
    from quantumscope.gui import qml_experiments as Q
    v = Q.VariationalExperiment()
    v.resize(1000, 700)
    v.show()
    v.data.source.setCurrentIndex(v.data.source.findData('moons'))
    v.steps.setValue(5)
    v.train()
    app.processEvents()
    plots.tidy(v.regions)                                              # tidying twice is harmless
    for plot in (v.regions, v.curve):                                  # an image with scatter, and lines
        item = plot.getPlotItem()
        image = QImage(plots.save_image(item, str(tmp_path / 'chart')))
        assert image.width() >= 1.9 * item.sceneBoundingRect().width()   # twice the screen resolution
        assert plots.copy_image(item).width() == image.width()
        csv = plots.save_data(item, str(tmp_path / 'chart'))
        assert csv.endswith('.csv') and open(csv).readline().count(',') >= 1


def test_physics_charts(app):
    from quantumscope.gui.double_slit_dialog import DoubleSlitDialog
    from quantumscope.gui.entanglement_experiment import EntanglementDialog
    for dialog in (DoubleSlitDialog(), EntanglementDialog()):
        _check(_plot_items(dialog))
