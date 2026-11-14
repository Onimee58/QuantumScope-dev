"""Optional checks of the Hydrogen Dynamics windows (QUANTUMSCOPE_GUI_TESTS=1).

The 3D checks draw in the real OpenGL view (v0.9.11), so they need a display; tools/run_gui_tests.sh
starts a virtual one when there is none.
"""
import os
import warnings

import numpy as np
import pytest

if os.environ.get('QUANTUMSCOPE_GUI_TESTS') != '1':
    pytest.skip('GUI tests are opt-in: set QUANTUMSCOPE_GUI_TESTS=1', allow_module_level=True)

QtWidgets = pytest.importorskip('PySide6.QtWidgets')
warnings.filterwarnings('ignore')


@pytest.fixture(scope='module')
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


@pytest.fixture
def dialog3d(app):
    from gl_support import opengl_app
    opengl_app()
    import quantumscope.gui.dynamics_3d_dialog as module
    dlg = module.HydrogenDynamics3DDialog()
    dlg.show()
    dlg.npoints.setValue(48)
    dlg._rebuild_later.flush()
    app.processEvents()
    yield dlg
    dlg.close()


def test_reset_camera_restores_the_isometric_view(dialog3d):
    p = dialog3d.plotter
    iso = p.direction()
    p.orbit(30, -12)
    assert not np.allclose(p.direction(), iso)
    dialog3d.reset_camera.click()
    assert np.allclose(p.direction(), iso) and np.allclose(iso, np.ones(3) / np.sqrt(3))
    assert np.allclose(p.camera()['center'], 0, atol=1e-9)


@pytest.mark.parametrize('view,axis', [('xy', [0, 0, 1]), ('xz', [0, -1, 0]), ('yz', [1, 0, 0])])
def test_standard_views(dialog3d, view, axis):
    dialog3d.view_buttons[view].click()
    assert np.allclose(dialog3d.plotter.direction(), axis, atol=1e-9)


def test_playback_and_appearance_changes_reuse_the_scene(dialog3d, app):
    volume, data = dialog3d.scene._volume, dialog3d.scene._aa
    assert volume is not None and dialog3d.plotter.named['cloud'] == [volume]
    dialog3d.slider.setValue(500)
    assert dialog3d.scene._volume is volume                       # playback replaces the data in place
    dialog3d.opacity.setValue(3.0)
    assert dialog3d.scene._aa is data          # no re-sampling for appearance
    dialog3d.render_mode.setCurrentIndex(1)
    assert 'surface' in dialog3d.plotter.named and 'cloud' not in dialog3d.plotter.named
    camera = dialog3d.plotter.camera()
    dialog3d.slider.setValue(700)
    assert dialog3d.plotter.camera() == camera                    # playback keeps the user's view


def test_exports(dialog3d, app, tmp_path, monkeypatch):
    from PIL import Image
    from PySide6.QtWidgets import QFileDialog
    png, gif = tmp_path / 'frame.png', tmp_path / 'beat.gif'
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *a, **k: (str(png), ''))
    dialog3d.export_png.click()
    image = np.asarray(Image.open(png).convert('RGB'))
    assert image.shape[:2] == (dialog3d.plotter.height(), dialog3d.plotter.width())
    assert (image.reshape(-1, 3) != image[0, 0]).any(axis=1).mean() > 0.001    # something was drawn
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *a, **k: (str(gif), ''))
    dialog3d.gif_frames.setValue(12)
    dialog3d.export_gif.click()
    with Image.open(gif) as animation:
        assert animation.n_frames == 12


def test_quick_values_and_fit(dialog3d):
    dialog3d.a.setCurrentIndex(0)
    dialog3d.b.setCurrentIndex(8)              # 1s + 4p
    dialog3d._rebuild_later.flush()
    assert 'clips' in dialog3d.info.text()
    dialog3d.halfwidth.parentWidget().action_button.click()
    dialog3d._rebuild_later.flush()
    assert dialog3d.halfwidth.value() == 44.0 and 'clips' not in dialog3d.info.text()
    dialog3d.prob.parentWidget().quick_buttons['25'].click()
    dialog3d._rebuild_later.flush()
    assert dialog3d.model.probability_first == pytest.approx(0.25)
    assert dialog3d.npoints.parentWidget().quick_buttons['Max'].toolTip().endswith('160')


def test_2d_dialog_controls(app):
    from quantumscope.gui.dynamics_dialog import HydrogenDynamicsDialog
    d = HydrogenDynamicsDialog()
    d.plane.setCurrentIndex(2)
    d._rebuild_later.flush()
    assert (d.plot.getAxis('bottom').labelText, d.plot.getAxis('left').labelText) == ('y', 'z')
    raw = d.current_density.copy()
    d.contrast.setCurrentText('Logarithmic')
    assert np.array_equal(d.current_density, raw)        # display only
    d.resolution.parentWidget().quick_buttons['Max'].click()
    d._rebuild_later.flush()
    assert d.current_density.shape == (400, 400)
    d.plot.getViewBox().scaleBy((0.2, 0.2))
    d.reset_view.click()
    span = d.plot.getViewBox().viewRange()[0]
    assert span[1] - span[0] > 1.9 * d.extent.value()
    d.close()
