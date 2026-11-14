"""v0.9.11: the Hydrogen Explorer's OpenGL views in the whole window (QUANTUMSCOPE_GUI_TESTS=1; own process)."""
import os

import numpy as np
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
    w.resize(1400, 900)
    w.show()
    app.processEvents()
    yield w
    w.close()
    app.processEvents()


def state(w, n, l, m, mode):
    w.n.setValue(n)
    w.l.setCurrentIndex(w.l.findData(l))
    w.m.setCurrentIndex(w.m.findData(m))
    w.mode.setCurrentText(mode)
    w.resolution.setValue(64)
    w.refresh()
    QtWidgets.QApplication.processEvents()


@pytest.mark.parametrize('mode,names', [('Density cloud', {'cloud', 'nucleus'}),
                                        ('Probability enclosure', {'enclosure', 'nucleus'}),
                                        ('Real(psi)', {'positive lobes', 'negative lobes', 'nucleus'})])
def test_each_representation_draws(window, mode, names):
    state(window, 3, 2, 0, mode)
    assert set(window.plotter.named) == names
    assert 'Render complete' in window.statusBar().currentMessage()
    image = window.plotter.rgb()
    assert (np.abs(image.astype(int) - (16, 24, 32)).sum(axis=-1) > 30).mean() > 0.02


def test_phase_colouring_and_the_imaginary_part_of_a_real_state(window):
    window.phase_color.setChecked(True)
    state(window, 2, 1, 1, 'Probability enclosure')
    assert window.plotter._bar is not None and window.plotter._bar[3] == 'phase (rad)'
    window.phase_color.setChecked(False)
    window.basis.setCurrentText('Real cosine')
    state(window, 2, 1, 1, 'Imag(psi)')
    assert any('zero' in text for text, _ in window.plotter._texts)
    window.basis.setCurrentText('Complex Y(l,m)')


def test_camera_views_and_magnification(window):
    state(window, 2, 1, 0, 'Probability enclosure')
    window.camera_view.setCurrentText('+Z')
    assert np.allclose(window.plotter.direction(), (0, 0, 1), atol=1e-9)
    near = window.plotter.camera()['distance']
    window.zoom_factor.setValue(window.zoom_factor.value() / 2)
    assert window.plotter.camera()['distance'] == pytest.approx(2 * near)
    window._reset_camera()
    assert window.camera_view.currentText() == 'Perspective'
    assert np.allclose(window.plotter.direction(), np.array([1, -1, .85]) / np.sqrt(2 + .85 ** 2))


def test_the_comparison_view_follows_the_primary(window):
    window.compare_enable.setChecked(True)
    window.sync_cameras.setChecked(True)
    state(window, 3, 1, 0, 'Density cloud')
    assert window.compare_panel.isVisible() and 'cloud' in window.compare_plotter.named
    window.plotter.orbit(40, 10)
    assert window.compare_plotter.camera() == window.plotter.camera()
    window.compare_plotter.orbit(-15, 0)
    assert window.plotter.camera() == window.compare_plotter.camera()       # both ways
    window.sync_cameras.setChecked(False)
    window.plotter.orbit(30, 0)
    assert window.compare_plotter.camera() != window.plotter.camera()
    window.compare_enable.setChecked(False)
    window.refresh()


def test_png_export_and_graphics_information(window, tmp_path, monkeypatch):
    from PySide6.QtGui import QImage
    from PySide6.QtWidgets import QFileDialog
    state(window, 2, 1, 0, 'Density cloud')
    target = tmp_path / 'orbital.png'
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *a, **k: (str(target), ''))
    window.export_scale.setValue(2)
    window.export_png()
    image = QImage(str(target))
    assert (image.width(), image.height()) == (2 * window.plotter.width(), 2 * window.plotter.height())
    assert 'OpenGL renderer:' in window.graphics_information()
    assert 'OpenGL' in window.details.text()
