"""v0.8.2 (18c): the kernel classifier's kernel map, interactive kernel matrix and sample viewer."""
import os

import pytest

if os.environ.get('QUANTUMSCOPE_GUI_TESTS') != '1':
    pytest.skip('GUI tests are opt-in: set QUANTUMSCOPE_GUI_TESTS=1', allow_module_level=True)

QtWidgets = pytest.importorskip('PySide6.QtWidgets')


@pytest.fixture(scope='module')
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


class Click:
    def __init__(self, pos):
        self._pos = pos

    def scenePos(self):
        return self._pos


def trained(app, name='mnist', a='4', b='9', **extra):
    from quantumscope.gui import qml_experiments as Q
    k = Q.KernelExperiment()
    k.resize(1500, 950)
    k.show()
    k.data.source.setCurrentIndex(k.data.source.findData(name))
    k.data.qubits.setValue(extra.get('qubits', 4))
    if a:
        k.data.class_a.setCurrentIndex(k.data.class_a.findText(a))
        k.data.class_b.setCurrentIndex(k.data.class_b.findText(b))
    k.feature_map.setCurrentIndex(k.feature_map.findData(extra.get('map', 'angle')))
    k.bandwidth.setValue(extra.get('bandwidth', 0.5))
    k.reps.setValue(1)
    k.train().wait()
    app.processEvents()
    return k


def test_kernel_matrix_cells_hover_and_click(app):
    from PySide6.QtCore import QPointF
    from quantumscope.ml import kernels as K
    k = trained(app)
    p = k.last['prepared']
    exact = K.kernel(p.X_train, kind='angle', bandwidth=0.5)
    vb = k.heatmap.getPlotItem().vb
    for x, y in ((3, 40), (100, 7), (55, 55)):
        a, b, value = k._heat_cell(vb.mapViewToScene(QPointF(x + 0.5, y + 0.5)))
        assert value == pytest.approx(exact[a, b], abs=1e-12)                    # the right samples, the right K
    k._heat_hover(vb.mapViewToScene(QPointF(10.5, 120.5)))
    assert k.heatmap.toolTip().startswith('K = ') and 'Click to see both' in k.heatmap.toolTip()
    k._heat_click(Click(vb.mapViewToScene(QPointF(10.5, 120.5))))
    entries = k.sample_view.entries
    assert len(entries) == 2 and all(e.get('image') is not None for e in entries)  # MNIST: the two images
    assert k.sample_view.title.text().startswith('Kernel value K = ')
    assert k._heat_cell(vb.mapViewToScene(QPointF(-50, -50))) is None              # outside: nothing


def test_kernel_map_points_and_layout(app):
    k = trained(app)
    title = k.kernel_map.getPlotItem().titleLabel.text
    assert 'of the kernel' in title and k.last['map_train'].shape == (len(k.last['prepared'].y_train), 2)
    spots = [item for item in k.kernel_map.getPlotItem().items if hasattr(item, 'points') and len(item.points())]
    assert all(point.data() is not None for item in spots for point in item.points())   # every point clickable
    which, index = spots[-1].points()[0].data()                                      # (the last layer: mistakes)
    k._show_points([spots[-1].points()[0]])
    heading = k.sample_view.entries[0]['heading']
    assert heading == f'{"Training" if which == "train" else "Test"} sample {index + 1}'
    assert k.regions.height() > k.splitter.sizes()[1]                             # regions keep the larger share
    tabular = trained(app, 'breast_cancer', None, None)
    tabular._show_points([[i for i in tabular.kernel_map.getPlotItem().items
                           if hasattr(i, 'points') and len(i.points())][0].points()[0]])
    lines = tabular.sample_view.entries[0]['lines']
    assert 'image' not in tabular.sample_view.entries[0] and any(':' in line for line in lines)   # raw values


def test_kernel_map_flags_concentration(app):
    k = trained(app, 'wine', None, None, qubits=6, map='zz', bandwidth=1.0)
    assert k.last['off'] < 0.05 and 'kernel concentration' in k.kernel_map.getPlotItem().titleLabel.text
