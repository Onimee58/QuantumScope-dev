"""Optional main-window checks for v0.7.1 (QUANTUMSCOPE_GUI_TESTS=1). They build the whole window,
3-D views included (which need OpenGL), so tools/run_gui_tests.sh runs each such file in its own process."""
import os

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


def test_every_plus_menu_entry_opens_in_its_own_area(window):
    for category, tabs in window.workspaces.items():
        for action in window._experiment_menu(window, category).actions():
            if action.isSeparator() or not action.text():
                continue
            action.trigger()
            assert window.categories.currentWidget() is tabs, (category, action.text())


def test_every_tab_closes_to_a_placeholder_and_comes_back_as_it_was(window):
    window._launch_circuits()
    window.circuit_widget.place('H', 0, 0)
    window._launch_double_slit()
    double_slit = window._open_experiments['double_slit']
    for category, tabs in window.workspaces.items():
        while tabs.count() and tabs.widget(0) is not window._placeholders.get(category):
            window._close_workspace_tab(category, 0)
        assert tabs.count() == 1 and tabs.widget(0) is window._placeholders[category]   # never blank
    buttons = {b.text(): b for b in window._placeholders['circuits']._buttons}
    assert {'Gate Circuit Simulator', 'QASM Converter', 'Error-correction explorer'} <= set(buttons)
    buttons['Gate Circuit Simulator'].click()
    circuits = window.workspaces['circuits']
    assert circuits.currentWidget() is window.circuit_widget and (0, 0) in window.circuit_widget.model.gates
    assert circuits.indexOf(window._placeholders['circuits']) < 0
    window._launch_double_slit()
    assert window._open_experiments['double_slit'] is double_slit
    window._show_hydrogen()
    assert window.workspaces['hydrogen'].indexOf(window._hydrogen_explorer) == 0


def test_links_and_loads_reopen_a_closed_circuit_tab(window):
    window._launch_circuits()
    circuits = window.workspaces['circuits']
    window._close_workspace_tab('circuits', circuits.indexOf(window.circuit_widget))
    window.launch_view('circuits')                                # Learn's Try it route
    assert circuits.currentWidget() is window.circuit_widget
    window._close_workspace_tab('circuits', circuits.indexOf(window.circuit_widget))
    from quantumscope.physics.circuits import Gate
    window._load_converted_circuit(1, [Gate('X', (0,))])           # the QASM Converter's route
    assert circuits.currentWidget() is window.circuit_widget


def test_about_opens_the_user_guide(window, monkeypatch):
    from PySide6.QtGui import QDesktopServices
    import quantumscope.gui.main_window as M
    opened = []
    monkeypatch.setattr(QDesktopServices, 'openUrl', staticmethod(lambda url: opened.append(url.toString()) or True))
    assert M.user_guide_path().is_file()
    M.open_user_guide()
    assert opened and opened[-1].endswith('QuantumScope-User-Guide.pdf') and opened[-1].startswith('file:')
    monkeypatch.setattr(M, 'user_guide_path', lambda: M.Path('/nowhere/guide.pdf'))
    M.open_user_guide()
    assert opened[-1] == M.USER_GUIDE_URL                                      # missing: the releases page
