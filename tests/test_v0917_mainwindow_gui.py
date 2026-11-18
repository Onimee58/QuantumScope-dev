"""v0.9.17: the window fits small screens, long runs say when they finish, side-panel groups fold
(QUANTUMSCOPE_GUI_TESTS=1; the whole window, in its own process)."""
import os
import time

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
    w.resize(1366, 700)
    w.show()
    app.processEvents()
    yield w
    w.close()
    app.processEvents()


def settle():
    app = QtWidgets.QApplication.instance()
    for _ in range(5):
        app.processEvents()


def test_the_window_never_needs_more_than_a_small_screen(window):
    """A trained classifier used to make the window at least 770 pixels tall: past the bottom of a
    768-pixel screen on Windows. The areas now scroll instead."""
    for launch in ('_launch_qml_kernel', '_launch_qml_variational', '_launch_qml_datasets', '_launch_annealing'):
        getattr(window, launch)()
        settle()
        hint = window.minimumSizeHint()
        assert hint.height() < 500 and hint.width() < 900, (launch, hint)
    k = window._open_experiments['qml_kernel']
    window._launch_qml_kernel()
    k.train().wait(120)
    settle()
    assert window.minimumSizeHint().height() < 500
    assert window.workspace_scroll.widget() is window.categories


def test_a_long_run_says_when_it_has_finished(window, monkeypatch):
    from quantumscope.gui import background as B
    monkeypatch.setattr(B, 'NOTIFY_AFTER', 0.05)
    k = window._open_experiments.get('qml_kernel') or window._launch_qml_kernel() or window._open_experiments['qml_kernel']
    run = B.Run(lambda report, cancelled: time.sleep(0.1) or 42, owner=k, task='The grid search').start()
    assert run.wait(10) == 42
    assert window.statusBar().currentMessage().startswith('The grid search finished (0 s)')
    quick = B.Run(lambda report, cancelled: 1, owner=k, task='Quick')        # quick runs finish quietly
    monkeypatch.setattr(B, 'NOTIFY_AFTER', 60)
    quick.start().wait(10)
    assert 'Quick' not in window.statusBar().currentMessage()


def test_the_panel_button_is_easy_to_find(window):
    panel = window.hydrogen_panel
    assert panel.button.objectName() == 'panelToggle' and panel.button.height() >= 30
    assert panel.button.text() == '«'


def test_groups_in_side_panels_fold_and_are_remembered(window):
    from PySide6.QtWidgets import QFormLayout, QGroupBox, QLineEdit, QSpinBox, QVBoxLayout, QWidget
    from quantumscope.gui.side_panel import CollapsiblePanel
    window._launch_qml_kernel()
    k = window._open_experiments['qml_kernel']
    groups = {g.title(): g for g in k.findChildren(QGroupBox) if getattr(g, 'fold', None) is not None}
    assert {'Data', 'Kernel and classifier', 'Model'} <= set(groups)
    groups['Data'].setChecked(False)
    settle()
    assert not groups['Data'].fold.isVisible() and k.method.isVisible()
    groups['Data'].setChecked(True)

    def panel():
        content = QWidget()
        group = QGroupBox('Settings')
        form = QFormLayout(group)
        shown, hidden = QLineEdit(), QSpinBox()
        form.addRow('Shown', shown)
        form.addRow('Hidden', hidden)
        form.setRowVisible(hidden, False)                        # hidden on purpose
        QVBoxLayout(content).addWidget(group)
        return CollapsiblePanel(content, 'Test', 'test-v0917'), group, form, hidden
    first, group, form, hidden = panel()
    first.show()
    group.setChecked(False)
    group.setChecked(True)
    settle()
    assert not form.isRowVisible(hidden)                         # unfolding keeps it hidden
    group.setChecked(False)
    again, group2, _, _ = panel()
    assert not group2.isChecked() and not group2.fold.isVisibleTo(group2)   # remembered
    group2.setChecked(True)
    first.close()
    again.close()
