"""Shared settings for pyqtgraph charts.

pyqtgraph's right-click menu has a "Plot Options" submenu (FFT, log scales, derivatives,
downsampling, …) meant for raw signal plots. Its transforms crash on scatter and bar items
(for example "Power Spectrum (FFT)": 'ScatterPlotItem' object has no attribute 'setFftMode'),
and none of them suits QuantumScope's charts. tidy() removes that submenu and keeps the rest of
the menu: View All, the axis options, the mouse mode and Export….
"""


def tidy(plot):
    """Remove "Plot Options" from a PlotWidget's (or PlotItem's) right-click menu; returns it."""
    item = plot.getPlotItem() if hasattr(plot, 'getPlotItem') else plot
    item.setMenuEnabled(enableMenu=False, enableViewBoxMenu=True)
    return plot
