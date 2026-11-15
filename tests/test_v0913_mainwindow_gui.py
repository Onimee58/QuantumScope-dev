"""v0.9.13: choosing features by annealing, between Quantum annealing and the Datasets tab
(QUANTUMSCOPE_GUI_TESTS=1; the whole window, in its own process)."""
import os
import time

import pytest

if os.environ.get('QUANTUMSCOPE_GUI_TESTS') != '1':
    pytest.skip('GUI tests are opt-in: set QUANTUMSCOPE_GUI_TESTS=1', allow_module_level=True)

QtWidgets = pytest.importorskip('PySide6.QtWidgets')
from gl_support import opengl_app  # noqa: E402
from test_v0913_feature_selection import MEAN  # noqa: E402


@pytest.fixture(scope='module')
def window():
    app = opengl_app()
    from quantumscope.gui.main_window import MainWindow
    w = MainWindow()
    w.resize(1480, 920)
    w.show()
    app.processEvents()
    yield w
    w.close()
    app.processEvents()


def settle(widget, button, seconds=120):
    app = QtWidgets.QApplication.instance()
    start = time.time()
    while not button.isEnabled() and time.time() - start < seconds:
        app.processEvents()
        time.sleep(0.02)
    app.processEvents()
    assert button.isEnabled(), 'the background run did not finish'


@pytest.fixture(scope='module')
def annealed(window):
    window._launch_annealing()
    a = window._open_experiments['annealing']
    a.problem_box.setCurrentIndex(a.problem_box.findData('features'))
    assert a.task is not None and a.task.source == 'breast_cancer'
    a.set_candidates(MEAN)
    a.keep.setValue(3)
    a.T.setValue(20)
    a.compute()
    settle(a, a.compute_button)
    return a


def test_other_problems_hide_the_feature_options(window):
    window._launch_annealing()
    a = window._open_experiments['annealing']
    a.problem_box.setCurrentIndex(a.problem_box.findData('maxcut:ring6'))
    assert not a.tabs.isTabVisible(3) and not a.problem_form.isRowVisible(a.candidates)
    a.problem_box.setCurrentIndex(a.problem_box.findData('features'))
    assert a.tabs.isTabVisible(3) and a.problem_form.isRowVisible(a.candidates)


def test_the_candidates_are_ranked_and_capped(window):
    window._launch_annealing()
    a = window._open_experiments['annealing']
    a.problem_box.setCurrentIndex(a.problem_box.findData('features'))
    from PySide6.QtCore import Qt
    first = a.candidates.item(0).text()
    assert first.startswith('worst concave points')                      # the most relevant first
    assert len(a._ticked()) == 10
    a.candidates.item(15).setCheckState(Qt.CheckState.Checked)            # an eleventh: refused
    assert len(a._ticked()) == 10 and 'At most 10' in a.feature_note.text()


def test_an_anneal_chooses_and_compares(annealed):
    a = annealed
    assert a.chosen_names() == ['mean texture', 'mean perimeter', 'mean concave points']
    assert a.reads.rank == 1 and a.use_button.isEnabled()
    text = a.comparison.text()
    for method in ('Annealed', 'Most relevant alone (greedy)', 'PCA (3 components of all 30)', 'All 10 candidates'):
        assert method in text
    assert 'best of all 120' in text and '100 reads' in a.result_label.text()


def test_use_the_features_in_the_datasets_tab_and_the_classifiers(window, annealed):
    from quantumscope.gui.qml_experiments import STORE
    annealed.use_features()
    d = window._open_experiments['qml_datasets']
    assert d.selection['names'] == ['mean texture', 'mean perimeter', 'mean concave points']
    assert STORE.prepared.features == d.selection['names'] and STORE.recipe.select == tuple(d.selection['names'])
    assert not d.components.isEnabled() and 'Chosen by annealing' in d.selection_label.text()
    window._launch_qml_kernel()
    k = window._open_experiments['qml_kernel']
    k.data.source.setCurrentIndex(k.data.source.findData('store'))
    assert 'chosen by annealing: mean texture' in k.data.summary.text()


def test_the_datasets_tab_sends_its_data_to_annealing(window):
    window._launch_qml_datasets()
    d = window._open_experiments['qml_datasets']
    task = d.choose_by_annealing()
    a = window._open_experiments['annealing']
    assert task is a.task and a.task.source == 'datasets' and a.data_box.currentData() == 'store'
    assert a.problem_box.currentData() == 'features' and a.keep.value() == 3


def test_chosen_features_are_set_aside_when_the_split_changes(window):
    d = window._open_experiments['qml_datasets']
    d.use_features(window._open_experiments['annealing'].task, ['mean texture', 'mean area'])
    assert d.selection is not None
    d.test_fraction.setValue(0.3)
    d.prepare()
    assert d.selection is None and 'set aside' in d.selection_label.text() and d.components.isEnabled()
    d.use_features(window._open_experiments['annealing'].task, ['mean texture', 'mean area'])
    d.clear_selection.click()
    assert d.selection is None and d.components.isEnabled()
