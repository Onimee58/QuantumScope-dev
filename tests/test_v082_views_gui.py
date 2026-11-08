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
    if extra.get('method'):
        k.method.setCurrentIndex(k.method.findData(extra['method']))
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
    assert k.top_tabs.height() > k.splitter.sizes()[1]                            # regions keep the larger share
    tabular = trained(app, 'breast_cancer', None, None)
    tabular._show_points([[i for i in tabular.kernel_map.getPlotItem().items
                           if hasattr(i, 'points') and len(i.points())][0].points()[0]])
    lines = tabular.sample_view.entries[0]['lines']
    assert 'image' not in tabular.sample_view.entries[0] and any(':' in line for line in lines)   # raw values


def test_kernel_map_flags_concentration(app):
    k = trained(app, 'wine', None, None, qubits=6, map='zz', bandwidth=1.0)
    assert k.last['off'] < 0.05 and 'kernel concentration' in k.kernel_map.getPlotItem().titleLabel.text


class OffscreenInteractor(QtWidgets.QWidget):
    """An off-screen stand-in for pyvistaqt.QtInteractor."""
    def __init__(self, parent=None, *a, **k):
        import pyvista as pv
        super().__init__(parent)
        self.__dict__['_p'] = pv.Plotter(off_screen=True, window_size=(600, 420))

    def __getattr__(self, name):
        return getattr(self.__dict__['_p'], name)

    def render(self, *a, **k):
        return self.__dict__['_p'].render()

    def enable_point_picking(self, *a, **k):
        self.__dict__['picking'] = k.get('callback')


def test_the_3d_view(app, tmp_path, monkeypatch):
    pytest.importorskip('pyvista')
    import quantumscope.gui.decision3d as D3
    monkeypatch.setattr(D3, 'make_plotter', lambda parent: OffscreenInteractor(parent))
    k = trained(app, 'mnist', '3', '8')
    view = k.view3d
    assert view.geometry is None                                              # nothing until the tab opens
    k.top_tabs.setCurrentIndex(1)
    app.processEvents()
    view.run.wait()
    app.processEvents()
    g = view.geometry
    assert g['f'].shape == (30, 30, 30) and 'agrees with the classifier on' in view.caption.text()
    view.plotter.__dict__['picking'](g['P_test'][4])                          # click a test point
    assert k.sample_view.entries[0]['heading'] == 'Test sample 5'
    for name in ('Front', 'Top', 'Side', 'Isometric', 'Reset'):
        view.preset(name)
    view.show_margins.setChecked(True)                                         # an SVM: margins allowed
    assert view.show_margins.isEnabled()
    assert os.path.getsize(view.save_image(str(tmp_path / 'view'))) > 1000
    assert os.path.getsize(view.save_gif(str(tmp_path / 'turn'), frames=4)) > 1000
    view.axes_box.setCurrentIndex(view.axes_box.findData('separating'))
    view.run.wait()
    app.processEvents()
    assert 'class separation' in view.caption.text()
    flat = trained(app, 'circles', None, None, qubits=2)                       # two features: no 3-D
    flat.top_tabs.setCurrentIndex(1)
    app.processEvents()
    assert 'at least 3 features' in flat.view3d.caption.text()
    ridge = trained(app, 'mnist', '0', '1', method='ridge')
    ridge.top_tabs.setCurrentIndex(1)
    app.processEvents()
    assert not ridge.view3d.show_margins.isEnabled()                           # margins are an SVM idea
