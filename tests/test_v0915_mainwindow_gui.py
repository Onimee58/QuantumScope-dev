"""v0.9.15: folding side panels, tabs in their own windows, palettes sized by the font, and the
gradient-descent controls (QUANTUMSCOPE_GUI_TESTS=1; the whole window, in its own process)."""
import os

import pytest

if os.environ.get('QUANTUMSCOPE_GUI_TESTS') != '1':
    pytest.skip('GUI tests are opt-in: set QUANTUMSCOPE_GUI_TESTS=1', allow_module_level=True)

QtWidgets = pytest.importorskip('PySide6.QtWidgets')
from gl_support import opengl_app  # noqa: E402


@pytest.fixture(scope='module')
def window():
    app = opengl_app()
    from quantumscope.gui.main_window import MainWindow
    w = MainWindow()
    w.resize(1400, 880)
    w.show()
    app.processEvents()
    yield w
    w.close()
    app.processEvents()


def settle():
    QtWidgets.QApplication.processEvents()


def test_side_panels_fold_to_a_strip_and_back(window):
    from quantumscope.gui.side_panel import STRIP
    window._select_category('circuits')
    settle()
    panel = window.circuit_widget.side_panel
    splitter = panel.parent()
    before = splitter.sizes()
    panel.set_collapsed(True)
    settle()
    assert panel.width() == STRIP and panel.name.isVisible() and not panel.content.isVisible()
    assert splitter.sizes()[1] > before[1]                                # the circuit gets the room
    assert panel.button.text() == '›'
    panel.name.mouseReleaseEvent(None)                                     # click the name: open again
    settle()
    assert not panel.collapsed and panel.content.isVisible() and splitter.sizes() == before


def test_folded_panels_are_remembered(window):
    from quantumscope.gui.side_panel import CollapsiblePanel
    window.hydrogen_panel.set_collapsed(True)
    again = CollapsiblePanel(QtWidgets.QLabel('x'), 'Hydrogen controls', 'hydrogen')
    assert again.collapsed
    window.hydrogen_panel.set_collapsed(False)
    assert not CollapsiblePanel(QtWidgets.QLabel('x'), 'Hydrogen controls', 'hydrogen').collapsed


def test_a_tab_opens_in_its_own_window_and_docks_back(window):
    window.show_dynamics_3d()
    tabs = window.workspaces['hydrogen']
    dialog = window._open_experiments['dynamics_3d']
    detached = window._detach_tab('hydrogen', tabs.indexOf(dialog))
    settle()
    assert tabs.indexOf(dialog) < 0 and dialog.window() is detached and detached.isVisible()
    detached.resize(500, 900)                                              # any shape
    settle()
    assert detached.width() <= 520
    window.show_dynamics_3d()                                              # opening it again: its window
    assert dialog in window._detached and tabs.indexOf(dialog) < 0
    detached.close()
    settle()
    assert dialog not in window._detached and tabs.indexOf(dialog) >= 0 and tabs.currentWidget() is dialog


def test_the_last_tab_leaves_a_start_page_and_the_window_closes_with_the_app(window):
    window._launch_circuits()
    tabs = window.workspaces['circuits']
    for i in reversed(range(tabs.count())):
        if tabs.widget(i) is not window.circuit_widget:
            window._close_workspace_tab('circuits', i)
    detached = window._detach_tab('circuits', tabs.indexOf(window.circuit_widget))
    assert tabs.count() == 1 and tabs.widget(0) is window._placeholders['circuits']
    window._launch_circuits()                                              # brings its window forward
    assert window.circuit_widget in window._detached
    detached.close()
    settle()
    assert tabs.indexOf(window.circuit_widget) >= 0


def test_palettes_fit_their_names(window):
    from PySide6.QtGui import QFont
    from quantumscope.gui.circuit_workspace import CircuitWorkspace, Palette
    palette = Palette()
    font = QFont(palette.font())
    font.setPointSizeF(font.pointSizeF() * 1.6)                           # as with Windows display scaling
    palette.setFont(font)
    palette.addItems(['M→c', 'Reset'])
    CircuitWorkspace._grid_palette(palette, 2, 92)
    metrics = palette.fontMetrics()
    assert palette.gridSize().height() >= metrics.height() + 16
    assert palette.gridSize().width() >= metrics.horizontalAdvance('Reset') + 12
    assert palette.height() == palette.gridSize().height() + 2 * palette.frameWidth()       # one row, no spare


def test_palette_margins_are_even(window):
    window._launch_circuits()
    QtWidgets.QApplication.processEvents()
    for palette in (window.circuit_widget.palette, window.circuit_widget.classical_palette,
                    window.circuit_widget.noise_palette):
        top_left = palette.mapTo(palette, palette.viewport().pos())
        items = [palette.visualItemRect(palette.item(i)).translated(top_left) for i in range(palette.count())]
        top = min(r.top() for r in items)
        bottom = palette.height() - 1 - max(r.bottom() for r in items)
        left = min(r.left() for r in items)
        right = palette.width() - 1 - max(r.right() for r in items)
        assert abs(top - bottom) <= 1 and abs(left - right) <= 2, (palette.objectName(), top, bottom, left, right)


def test_the_learning_rate_follows_the_optimizer(window):
    window._launch_qml_variational()
    v = window._open_experiments['qml_variational']
    v.method.setCurrentIndex(v.method.findData('BFGS'))
    assert not v.rate.isEnabled() and not v.rate_note.isHidden()
    v.method.setCurrentIndex(v.method.findData('gradient'))
    assert v.rate.isEnabled() and v.batch.isEnabled() and v.rate_note.isHidden()
    v.batch.setValue(16)
    assert v._options()['method'] == 'gradient' and v._options()['batch_size'] == 16
