"""v0.9.3: many classes in the Quantum ML experiments (QUANTUMSCOPE_GUI_TESTS=1)."""
import os

import numpy as np
import pytest

if os.environ.get('QUANTUMSCOPE_GUI_TESTS') != '1':
    pytest.skip('GUI tests are opt-in: set QUANTUMSCOPE_GUI_TESTS=1', allow_module_level=True)

QtWidgets = pytest.importorskip('PySide6.QtWidgets')


@pytest.fixture(scope='module')
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def wait(app, run):
    while run.running():
        app.processEvents()
    app.processEvents()


def trained(app, name='iris', qubits=4, method='svm', bandwidth=1.0):
    from quantumscope.gui import qml_experiments as Q
    k = Q.KernelExperiment()
    k.resize(1500, 950)
    k.show()
    k.data.source.setCurrentIndex(k.data.source.findData(name))
    k.data.qubits.setValue(qubits)
    k.data.class_a.setCurrentIndex(k.data.class_a.findData(Q.ALL))
    k.feature_map.setCurrentIndex(k.feature_map.findData('angle'))
    k.bandwidth.setValue(bandwidth)
    k.method.setCurrentIndex(k.method.findData(method))
    k.train().wait()
    app.processEvents()
    return k


def test_all_classes_in_the_kernel_classifier(app):
    from quantumscope.ml import evaluation as E, kernels as K
    k = trained(app, 'iris')
    p, r = k.last['prepared'], k.last
    assert p.k == 3 and not k.data.class_b.isVisible() and '3 classes, one-vs-rest' in k.data.summary.text()
    assert isinstance(r['model'], K.OneVsRest) and r['decision_test'].shape == (len(p.y_test), 3)
    assert r['test'] >= 0.85 and '3 one-vs-rest classifiers' in k.result.text()
    assert r['f'].shape[-1] == 3                                        # one value per class on the plane
    m = E.multi_metrics(p.y_test, r['decision_test'].argmax(axis=1), 3)
    ev = k.evaluation
    assert ev.metrics.confusion.tolist() == m.confusion.tolist() and ev.shown_confusion.shape == (3, 3)
    assert ev.confusion_plot.isVisibleTo(ev) and not ev.confusion.isVisibleTo(ev)        # a picture, not a table
    assert ev.shown_names == ['setosa', 'versicolor', 'virginica']
    assert 'balanced accuracy' in ev.summary.text() and 'macro F1' in ev.summary.text()
    assert ev.auc == pytest.approx(np.mean([c[2] for c in E.roc_by_class(p.y_test, r['decision_test']).values()]))
    wait(app, ev.run_cross_validation())
    assert len(ev.cv_last.scores) == 5 and ev.cv_last.mean > 0.8
    entry = k.sample_entry('test', 0)                                   # the sample viewer names the winner
    assert entry['lines'][0].startswith('true class ') and 'confidence' in entry['lines'][2]
    assert k.model_panel.model.k == 3 and '3 classes' in k.model_panel.summary.text()


def test_the_pair_choice_still_works_and_switches_back(app):
    from quantumscope.gui import qml_experiments as Q
    k = trained(app, 'iris')
    k.data.class_a.setCurrentIndex(k.data.class_a.findText('versicolor'))
    k.data.class_b.setCurrentIndex(k.data.class_b.findText('virginica'))
    assert k.data.class_b.isVisible()
    k.train().wait()
    app.processEvents()
    p = k.last['prepared']
    assert p.k == 2 and p.classes == ('versicolor', 'virginica') and k.evaluation.confusion.rowCount() == 2
    assert k.evaluation.confusion.isVisibleTo(k.evaluation) and not k.evaluation.confusion_plot.isVisibleTo(k.evaluation)
    assert k.evaluation.confusion.horizontalHeaderItem(0).text() == 'predicted versicolor'
    assert Q.palette(2)[0] == (1, Q.CLASS_COLOURS[0])


def test_ten_digits_search_and_saved_model(app, tmp_path):
    from quantumscope.ml import models as M
    k = trained(app, 'digits', qubits=6)
    p = k.last['prepared']
    assert p.k == 10 and k.last['test'] >= 0.7 and k.evaluation.shown_confusion.sum() == len(p.y_test)
    panel = k.search_panel
    panel.zz.setChecked(False)
    panel.bandwidths.setText('0.5, 1')
    panel.strengths.setText('1')
    wait(app, panel.search())
    assert panel.table.rowCount() == 2 and panel.best.mean > 0.6
    path = k.model_panel.model.save(str(tmp_path / 'digits'))
    loaded = M.load(path)
    names, _ = loaded.predict(k.data.dataset.X[p.test_rows])
    assert names == [p.classes[c] for c in k.last['predicted']]


def test_the_datasets_tab_prepares_all_classes_for_the_kernel_classifier(app):
    from quantumscope.gui import qml_experiments as Q
    d = Q.DatasetsExperiment()
    d.show()
    d.source.setCurrentIndex(d.source.findData('penguins'))
    d.class_a.setCurrentIndex(d.class_a.findData(Q.ALL))
    assert not d.class_b.isVisible() and 'one-vs-rest' in d.findings.text()
    prepared = d.prepare()
    assert prepared.k == 3 and Q.STORE.prepared is prepared and 'Both classifiers can now use it' in d.steps.text()
    kernel = Q.KernelExperiment()
    kernel.data.source.setCurrentIndex(kernel.data.source.findData('store'))
    kernel.train().wait()
    app.processEvents()
    assert kernel.last['prepared'].k == 3 and kernel.last['test'] >= 0.85
    d.class_a.setCurrentIndex(d.class_a.findText('Adelie (152)'))           # back to a pair
    assert d.class_b.isVisible() and d.prepare().k == 2
    assert d.class_a.findData(Q.ALL) == 0


def test_the_3d_view_with_many_classes(app, monkeypatch):
    pytest.importorskip('pyvista')
    import quantumscope.gui.decision3d as D3
    from test_v082_views_gui import OffscreenInteractor
    monkeypatch.setattr(D3, 'make_plotter', lambda parent: OffscreenInteractor(parent))
    k = trained(app, 'seeds', qubits=4)
    view = k.view3d
    k.top_tabs.setCurrentIndex(1)
    app.processEvents()
    view.run.wait()
    app.processEvents()
    g = view.geometry
    assert g['f'].shape == (30, 30, 30, 3) and not view.show_margins.isEnabled()
    assert any(name.startswith('region') for name in view.plotter.actors)            # a surface per class region
    view.axes_box.setCurrentIndex(view.axes_box.findData('separating'))
    view.run.wait()
    app.processEvents()
    assert 'class spread 1' in view.caption.text()
