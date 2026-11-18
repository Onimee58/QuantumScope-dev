"""v0.9.18: graphs in their own windows, dots on tabs with news, and search (QUANTUMSCOPE_GUI_TESTS=1;
the whole window, in its own process)."""
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
    w.resize(1366, 720)
    w.show()
    app.processEvents()
    yield w
    w.close()
    app.processEvents()


def settle():
    app = QtWidgets.QApplication.instance()
    for _ in range(5):
        app.processEvents()


def test_a_graph_opens_in_its_own_window_and_comes_back(window):
    from quantumscope.gui import pop_out
    window._launch_qml_kernel()
    k = window._open_experiments['qml_kernel']
    k.views.setCurrentWidget(k.kernel_map)
    k.heatmap.pop_out_button.click()
    settle()
    graph = pop_out.OPEN[-1]
    assert graph.widget is k.heatmap and graph.isVisible() and k.heatmap.window() is graph
    assert isinstance(k.views.widget(0), pop_out.Placeholder) and k.views.tabText(0) == 'Kernel matrix'
    assert k.views.currentWidget() is k.kernel_map                      # the tab in view stays in view
    k.train().wait(120)                                                  # it keeps updating where it is
    settle()
    assert k.heatmap.window() is graph
    graph.close()
    settle()
    assert k.views.widget(0) is k.heatmap and not pop_out.OPEN and k.heatmap.pop_out_button.isVisibleTo(k.heatmap)


def test_graphs_in_layouts_and_splitters_too(window):
    from quantumscope.gui import pop_out
    window._launch_qml_variational()
    v = window._open_experiments['qml_variational']
    home = v.regions.parentWidget()
    pop_out.pop_out(v.regions, 'Decision regions')
    settle()
    assert v.regions.window() is pop_out.OPEN[-1] and v.findChildren(pop_out.Placeholder)
    pop_out.close_all()
    settle()
    assert v.regions.parentWidget() is home and not v.findChildren(pop_out.Placeholder)


def test_closing_the_experiment_closes_its_graph_windows(window):
    from quantumscope.gui import pop_out
    window._launch_qml_kernel()
    k = window._open_experiments['qml_kernel']
    pop_out.pop_out(k.kernel_map, 'Kernel map')
    tabs = window.workspaces['qml']
    window._close_workspace_tab('qml', tabs.indexOf(k))
    settle()
    assert not pop_out.OPEN and k.views.widget(1) is k.kernel_map
    window._launch_qml_kernel()


def test_new_data_puts_a_dot_on_the_classifiers_tab(window):
    window._launch_qml_kernel()
    k = window._open_experiments['qml_kernel']
    k.data.source.setCurrentIndex(k.data.source.findData('store'))
    window._launch_qml_datasets()
    d = window._open_experiments['qml_datasets']
    d.prepare()
    settle()
    assert window.has_dot(k)
    window._launch_qml_kernel()                                          # looked at: the dot goes
    assert not window.has_dot(k)
    d.prepare()                                                          # in view: no dot needed
    assert not window.has_dot(k)


def test_a_run_that_ends_elsewhere_marks_its_tab_and_area(window, monkeypatch):
    from quantumscope.gui import background as B
    monkeypatch.setattr(B, 'NOTIFY_AFTER', 0.05)
    window._launch_annealing()
    a = window._open_experiments['annealing']
    window._launch_circuits()
    B.Run(lambda report, cancelled: time.sleep(0.1), owner=a, task='The anneal').start().wait(10)
    settle()
    assert window.has_dot(a)
    circuits = window.categories.indexOf(window.workspaces['circuits'])
    assert window.categories.currentIndex() == circuits
    window._launch_qml_kernel()
    qml_area = window.categories.tabBar()
    window._launch_annealing()
    assert not window.has_dot(a) and qml_area is not None


def test_search_finds_experiments_by_topic(window):
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    box = window.search_box
    window._launch_circuits()
    QTest.keyClicks(box, 'qubo')
    settle()
    assert window.search.completionCount() == 1 and 'Quantum annealing' in window.search.currentCompletion() or \
        window.search.completionModel().index(0, 0).data().startswith('Quantum annealing')
    QTest.keyClick(box, Qt.Key.Key_Return)
    settle()
    assert window.workspaces['circuits'].currentWidget() is window._open_experiments['annealing']
    assert box.text() == ''
    box.setText('')
    QTest.keyClicks(box, 'bell')
    settle()
    shown = [window.search.completionModel().index(i, 0).data() for i in range(window.search.completionCount())]
    assert any(s.startswith('Quantum Entanglement') for s in shown)
    box.clear()
