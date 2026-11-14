"""v0.9.11: the OpenGL 3-D view itself (QUANTUMSCOPE_GUI_TESTS=1; needs OpenGL, see gl_support)."""
import os

import numpy as np
import pytest

if os.environ.get('QUANTUMSCOPE_GUI_TESTS') != '1':
    pytest.skip('GUI tests are opt-in: set QUANTUMSCOPE_GUI_TESTS=1', allow_module_level=True)

pytest.importorskip('PySide6.QtWidgets')
from gl_support import opengl_app  # noqa: E402


@pytest.fixture
def view():
    app = opengl_app()
    from quantumscope.visualization.gl3d import View3D
    v = View3D()
    v.resize(400, 300)
    v.show()
    app.processEvents()
    yield v
    v.close()


def drawn(image, background=(16, 24, 32)):
    """Share of pixels that differ from the background."""
    return float((np.abs(image.astype(int) - background).sum(axis=-1) > 30).mean())


def test_a_lit_sphere_is_drawn_and_fitted(view):
    from quantumscope.visualization import gl3d
    verts, faces = gl3d.glyphs([(5, 5, 5)], 'sphere', 2.0)
    view.surface(verts, faces, (1.0, 0.5, 0.0), name='ball')
    view.fit('isometric')
    assert np.allclose(view.camera()['center'], (5, 5, 5), atol=0.05)
    image = view.rgb()
    assert image.shape == (300, 400, 3) and 0.05 < drawn(image) < 0.6
    centre = image[150, 200].astype(int)
    assert centre[0] > 150 and centre[2] < 80                                # orange, lit from the camera
    xy, front = view.project([(5, 5, 5)])
    assert front[0] and np.allclose(xy[0], (200, 150), atol=1)              # the focal point is in the middle
    assert view.nearest_on_screen(np.array([(5, 5, 5), (50, 50, 50)]), 203, 148) == 0
    assert view.nearest_on_screen(np.array([(5, 5, 5)]), 10, 10) is None


def test_see_through_surfaces_are_drawn_twice_and_named(view):
    from quantumscope.visualization import gl3d
    verts, faces = gl3d.glyphs([(0, 0, 0)], 'sphere', 1.0)
    items = view.surface(verts, faces, '#4eb5d6', opacity=0.5, name='glass')
    assert len(items) == 2 and view.named['glass'] == items
    view.remove('glass')
    assert 'glass' not in view.named and not view.items


def test_exports_are_scaled_and_keep_the_overlays(view, tmp_path):
    from quantumscope.visualization import gl3d
    view.surface(*gl3d.glyphs([(0, 0, 0)], 'cube', 1.0), '#ff8800', smooth=False)
    view.fit('xz')
    plain = view.rgb()
    view.text('caption')
    view.axes()
    view.colour_bar(gl3d.lut('phase'), -np.pi, np.pi, 'phase (rad)')
    marked = view.rgb()
    assert drawn(marked[:30, :120]) > drawn(plain[:30, :120]) + 0.02        # the caption, upper left
    assert drawn(marked[200:, :90]) > drawn(plain[200:, :90])                # the axes marker, lower left
    assert drawn(marked[80:230, 360:380]) > 0.5                              # the colour bar, right
    big = view.image(2)
    assert (big.width(), big.height()) == (800, 600)
    assert os.path.getsize(view.save(tmp_path / 'view.png', scale=2)) > 2000


def test_the_camera_follows_the_user_and_reports_it(view):
    from quantumscope.visualization import gl3d
    view.surface(*gl3d.glyphs([(0, 0, 0)], 'sphere', 1.0), '#ffffff')
    view.fit('isometric')
    changes = []
    view.cameraChanged.connect(lambda: changes.append(view.camera()))
    view.orbit(20, 5)
    assert changes and changes[-1]['azimuth'] == pytest.approx(65)
    saved = view.camera()
    view.look('xy')
    assert np.allclose(view.direction(), (0, 0, 1), atol=1e-9)
    view.set_camera(saved)
    assert view.camera() == saved


def test_a_fit_made_before_layout_still_fits_after(view):
    from quantumscope.visualization import gl3d
    view.surface(*gl3d.glyphs([(0, 0, 0)], 'sphere', 1.0), '#ffffff')
    view.resize(60, 400)                                                      # a narrow view: far away
    view.fit('isometric')
    far = view.camera()['distance']
    view.resize(400, 400)
    assert view.camera()['distance'] < far / 3                                # moved in once there was room
    view.orbit(5, 0)
    near = view.camera()['distance']
    view.resize(200, 400)
    assert view.camera()['distance'] == near                                  # the user's camera stays


def test_graphics_information_names_the_renderer(view):
    text = view.gl_information()
    assert 'OpenGL renderer:' in text and 'OpenGL version:' in text
