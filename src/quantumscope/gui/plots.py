"""Shared settings for pyqtgraph charts.

pyqtgraph's right-click menu has two parts that do not suit QuantumScope:
  - "Plot Options" (FFT, log scales, derivatives, …), meant for raw signal plots; its transforms
    crash on scatter and bar items ('ScatterPlotItem' object has no attribute 'setFftMode');
  - "Export…", a small generic dialog whose SVG and Matplotlib formats fail on these charts.
tidy() removes both and adds three plain actions that work on every chart: Save image… (PNG or
JPEG, at twice the screen resolution), Copy image, and Save data (CSV)…. View All, the axis
options and the mouse mode stay.
"""
from PySide6.QtWidgets import QApplication, QFileDialog


def tidy(plot):
    """Clean up a PlotWidget's right-click menu (see the module note); returns the widget."""
    item = plot.getPlotItem() if hasattr(plot, 'getPlotItem') else plot
    item.setMenuEnabled(enableMenu=False, enableViewBoxMenu=True)    # no "Plot Options"
    scene = plot.scene() if hasattr(plot, 'scene') else item.scene()
    if scene is not None:
        scene.contextMenu = []                                          # no generic "Export…"
    menu = item.getViewBox().menu
    if menu is not None and not getattr(menu, '_quantumscope_saving', False):
        menu.addSeparator()
        menu.addAction('Save image…', lambda: save_image(item))
        menu.addAction('Copy image', lambda: copy_image(item))
        menu.addAction('Save data (CSV)…', lambda: save_data(item))
        menu._quantumscope_saving = True
    return plot


def _image_exporter(item):
    from pyqtgraph.exporters import ImageExporter
    exporter = ImageExporter(item)
    exporter.parameters()['width'] = int(max(1, item.sceneBoundingRect().width()) * 2)   # crisp: 2×
    return exporter


def save_image(item, path=None):
    """Save the chart as PNG (or JPEG); returns the file name, or None if cancelled."""
    if path is None:
        path, _ = QFileDialog.getSaveFileName(None, 'Save image', 'chart.png', 'PNG image (*.png);;JPEG image (*.jpg)')
        if not path:
            return None
    if not path.lower().endswith(('.png', '.jpg', '.jpeg')):
        path += '.png'
    _image_exporter(item).export(fileName=path)
    return path


def copy_image(item):
    """Put the chart on the clipboard as an image."""
    _image_exporter(item).export(copy=True)
    return QApplication.clipboard().image()


def save_data(item, path=None):
    """Save the plotted numbers as CSV; returns the file name, or None if cancelled."""
    from pyqtgraph.exporters import CSVExporter
    if path is None:
        path, _ = QFileDialog.getSaveFileName(None, 'Save data', 'chart.csv', 'CSV file (*.csv)')
        if not path:
            return None
    if not path.lower().endswith('.csv'):
        path += '.csv'
    CSVExporter(item).export(fileName=path)
    return path
