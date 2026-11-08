"""v0.8.3 (19c): the Evaluation and Search tabs, and the variational classifier's training controls."""
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


@pytest.fixture
def kernel(app):
    from quantumscope.gui import qml_experiments as Q
    k = Q.KernelExperiment()
    k.resize(1400, 900)
    k.show()
    k.data.source.setCurrentIndex(k.data.source.findData('mnist'))
    k.data.qubits.setValue(4)
    k.data.class_a.setCurrentIndex(k.data.class_a.findText('3'))
    k.data.class_b.setCurrentIndex(k.data.class_b.findText('8'))
    k.feature_map.setCurrentIndex(k.feature_map.findData('angle'))
    k.bandwidth.setValue(0.5)
    k.train().wait()
    app.processEvents()
    return k


def test_evaluation_tab_and_cross_validation(app, kernel):
    from quantumscope.ml import evaluation as E
    k = kernel
    p, r = k.last['prepared'], k.last
    expected = E.metrics(p.y_test, np.where(r['decision_test'] >= 0, 1, -1))
    assert k.evaluation.metrics == expected                                   # the shown metrics are right
    assert k.evaluation.auc == pytest.approx(E.auc_by_ranks(p.y_test, r['decision_test']))
    assert k.evaluation.confusion.item(0, 0).text() == str(expected.tp)
    assert k.evaluation.confusion.horizontalHeaderItem(0).text() == 'predicted 3'
    wait(app, k.evaluation.run_cross_validation())
    assert len(k.evaluation.cv_last.scores) == 5 and '5-fold cross-validation' in k.evaluation.cv_result.text()


def test_search_and_use_best(app, kernel):
    k = kernel
    panel = k.search_panel
    panel.bandwidths.setText('0.25, 0.5')
    panel.strengths.setText('1, 10')
    wait(app, panel.search())
    assert panel.table.rowCount() == 2 * 2 + 2 * 2 * 2 and panel.best_button.isEnabled()   # angle 4, ZZ 8
    best = panel.best.settings
    panel.best_button.click()
    k.run.wait()
    app.processEvents()
    assert k.bandwidth.value() == pytest.approx(best['bandwidth']) and k.strength.value() == pytest.approx(best['strength'])
    assert k.feature_map.currentData() == best['feature_map'] and k.views.currentWidget() is k.evaluation
    panel.bandwidths.setText('zero')
    assert panel.search() is None and panel.status.text().startswith('Bandwidths: use positive numbers')
    panel.bandwidths.setText('0.5')
    panel.reps.setText('1.5')
    assert panel.search() is None and panel.status.text().startswith('Repetitions: use positive whole numbers')
    panel.reps.setText('1, 2')
    k.views.setCurrentWidget(panel)
    assert not k.sample_view.isVisible()                                              # samples only beside the kernel views
    k.views.setCurrentWidget(k.kernel_map)
    assert k.sample_view.isVisible()


def test_variational_training_controls(app):
    from quantumscope.gui import qml_experiments as Q
    v = Q.VariationalExperiment()
    v.resize(1400, 900)
    v.show()
    v.data.source.setCurrentIndex(v.data.source.findData('breast_cancer'))
    v.data.qubits.setValue(4)
    v.method.setCurrentIndex(v.method.findData('BFGS'))
    assert not v.rate.isEnabled() and not v.batch.isEnabled() and not v.patience.isEnabled()
    v.method.setCurrentIndex(v.method.findData('Adam'))
    v.validation_share.setValue(0.25)
    assert v.rate.isEnabled() and v.batch.isEnabled() and v.patience.isEnabled()
    v.steps.setValue(150)
    v.rate.setValue(0.08)
    v.batch.setValue(32)
    v.patience.setValue(10)
    v.loss_box.setCurrentIndex(v.loss_box.findData('hinge'))
    result = v.train().wait()
    app.processEvents()
    assert len(v.val_loss_line.getData()[0]) == len(v._history) > 1                 # the validation curve is drawn
    if result['stopped_early']:
        assert f'kept step {result["best_step"]}' in v.result.text()
    assert v.evaluation.metrics is not None and v.evaluation.metrics.total == len(v.prepared.y_test)
    assert v.model_panel.model.settings['loss'] == 'hinge'
    v.evaluation.folds.setValue(3)
    wait(app, v.evaluation.run_cross_validation())
    assert len(v.evaluation.cv_last.scores) == 3
