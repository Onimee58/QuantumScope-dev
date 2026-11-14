"""v0.9.11: the 3-D views draw with OpenGL through pyqtgraph instead of VTK (no window)."""
import os
import subprocess
import sys

import numpy as np
import pytest

gl3d = pytest.importorskip('quantumscope.visualization.gl3d')


# ---- geometry ---------------------------------------------------------------------------------------------
def sphere_field(n=33, half=2.0):
    x = np.linspace(-half, half, n)
    return x, np.sqrt(x[:, None, None] ** 2 + x[None, :, None] ** 2 + x[None, None, :] ** 2)


def test_contours_are_in_world_coordinates_and_welded():
    x, r = sphere_field()
    verts, faces = gl3d.contour(r, 1.2, x[0], x[1] - x[0])
    radii = np.linalg.norm(verts, axis=1)
    assert len(faces) > 500 and np.allclose(radii, 1.2, atol=0.02)
    assert len(np.unique(np.round(verts, 5), axis=0)) == len(verts)          # each vertex once: smooth shading
    assert faces.max() < len(verts) and faces.dtype == np.uint32
    edges = np.sort(np.r_[faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]], axis=1)
    _, counts = np.unique(edges, axis=0, return_counts=True)
    assert (counts == 2).all()                                                # a closed surface, no cracks


def test_contours_follow_the_grid_spacing_on_each_axis():
    x, r = sphere_field(n=21, half=1.0)                                       # field on a unit grid ...
    verts, _ = gl3d.contour(r, 0.6, (10.0, 0.0, -5.0), (2.0, 1.0, 0.5))      # ... placed and stretched
    centre = (verts.max(axis=0) + verts.min(axis=0)) / 2
    extent = verts.max(axis=0) - verts.min(axis=0)
    assert np.allclose(centre, (10 + 2 * 10, 10, -5 + 0.5 * 10), atol=0.05)
    assert np.allclose(extent / extent[1], (2.0, 1.0, 0.5), atol=0.03)


def test_nothing_to_contour_gives_an_empty_mesh():
    verts, faces = gl3d.contour(np.zeros((5, 5, 5)), 1.0, 0, 1)
    assert verts.shape == (0, 3) and faces.shape == (0, 3)


def test_fast_normals_match_pyqtgraphs():
    import pyqtgraph.opengl as gl
    x, r = sphere_field(n=17)
    verts, faces = gl3d.contour(r, 1.0, x[0], x[1] - x[0])
    fast = gl3d.Mesh(vertexes=verts, faces=faces).vertexNormals()
    slow = gl.MeshData(vertexes=verts, faces=faces).vertexNormals()
    assert np.allclose(fast, slow, atol=1e-5)
    outward = np.einsum('ij,ij->i', fast, verts / np.linalg.norm(verts, axis=1, keepdims=True))
    assert (np.abs(outward) > 0.95).all()                                     # normals point along the radius
    assert gl3d.Mesh(vertexes=verts, faces=faces).vertexNormals(indexed='faces').shape == (len(faces), 3, 3)


def test_glyphs_put_one_shape_at_each_point():
    points = np.array([[0, 0, 0], [5, 0, 0], [0, 5, 5]], float)
    verts, faces = gl3d.glyphs(points, 'cube', 0.5)
    assert verts.shape == (24, 3) and faces.shape == (36, 3) and faces.max() == 23
    assert np.allclose(verts[8:16].mean(axis=0), points[1])
    verts, faces = gl3d.glyphs(points, 'sphere', 2.0)
    per = len(verts) // 3
    assert np.allclose(np.linalg.norm(verts[per:2 * per] - points[1], axis=1), 2.0)


# ---- colours ------------------------------------------------------------------------------------------
def test_the_phase_colours_are_cyclic_light_at_pi_and_dark_at_zero():
    table = gl3d.lut('phase')
    assert table.shape == (256, 3) and table.dtype == np.uint8
    assert np.abs(table[0].astype(int) - table[-1]).max() <= 6                # −π and +π look the same
    assert table[128].sum() < 200 < table[0].sum()                            # like matplotlib's twilight
    rgba = gl3d.colours([-np.pi, 0.0, np.nan], table, -np.pi, np.pi)
    assert rgba.shape == (3, 4) and np.allclose(rgba[2, :3], 128 / 255) and (rgba[:, 3] == 1).all()


def test_the_cloud_shows_more_where_the_density_is_higher():
    from quantumscope.visualization import orbitals
    display = np.linspace(0, 1, 50).reshape(5, 5, 2)
    rgba = orbitals.cloud_colours(display)
    alpha = rgba[..., 3].ravel()
    assert rgba.dtype == np.uint8 and alpha[0] == 0 and (np.diff(alpha.astype(int)) >= 0).all()
    assert alpha[-1] == round(255 * 0.25 * orbitals.CLOUD_GAIN)
    assert (orbitals.cloud_colours(display, 2.0)[..., 3] >= rgba[..., 3]).all()   # "Cloud visibility" raises it
    assert np.array_equal(rgba[..., :3].reshape(-1, 3)[-1], gl3d.lut('viridis')[-1])


def test_the_dynamics_cloud_keeps_vtks_sigmoid():
    from quantumscope.gui.dynamics_3d_scene import sigmoid
    vtk = [0, 0, 0, 4, 30, 127, 224, 250, 254, 254, 254]                     # pyvista's table, 11 steps
    assert np.allclose(sigmoid(np.linspace(0, 1, 11)) * 255, vtk, atol=1.5)


# ---- camera ----------------------------------------------------------------------------------------------
class FakeView:
    def look(self, view, distance, center):
        self.looked = (view, distance, center)


@pytest.mark.parametrize('name,view,factor', [('Perspective', 'perspective', np.sqrt(2 + .85 ** 2)),
                                               ('+X', '+x', 1.0), ('+Z', '+z', 1.0)])
def test_the_hydrogen_cameras_sit_where_they_always_did(name, view, factor):
    from quantumscope.visualization.orbitals import set_camera_view
    fake = FakeView()
    set_camera_view(fake, 10.0, name, 2.0)
    assert fake.looked[0] == view and fake.looked[1] == pytest.approx(3.1 * 10 / 2 * factor)


@pytest.mark.parametrize('view,direction', [('isometric', np.ones(3) / np.sqrt(3)), ('xy', (0, 0, 1)),
                                            ('xz', (0, -1, 0)), ('yz', (1, 0, 0)), ('+y', (0, 1, 0)),
                                            ('perspective', np.array([1, -1, .85]) / np.sqrt(2 + .85 ** 2))])
def test_named_views_look_from_the_same_directions_as_before(view, direction):
    import math
    azimuth, elevation = gl3d.VIEWS[view]
    a, e = math.radians(azimuth), math.radians(elevation)
    assert np.allclose([math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)], direction, atol=1e-9)


# ---- no VTK left ------------------------------------------------------------------------------------------
def test_the_app_no_longer_loads_vtk():
    code = '''
import os, sys
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication
app = QApplication([])
import quantumscope.gui.main_window, quantumscope.gui.decision3d, quantumscope.gui.dynamics_3d_dialog
print(sorted(m for m in sys.modules if m.split(".")[0] in ("vtk", "vtkmodules", "pyvista", "pyvistaqt")))
print("pyqtgraph.opengl" in sys.modules)
'''
    out = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, timeout=300)
    if out.returncode != 0 and 'cannot open shared object file' in out.stderr:
        pytest.skip('Qt cannot load here (a system library is missing): ' + out.stderr.strip().splitlines()[-1])
    assert out.returncode == 0, out.stderr[-2000:]
    assert out.stdout.split('\n')[-3:-1] == ['[]', 'True']


def test_packaging_and_requirements_have_no_vtk():
    root = os.path.join(os.path.dirname(__file__), '..')
    project = open(os.path.join(root, 'pyproject.toml')).read()
    workflow = open(os.path.join(root, '.github', 'workflows', 'release.yml')).read()
    assert 'pyvista' not in project and 'PyOpenGL' in project and 'pyqtgraph' in project
    for gone in ('VTK_ARGS', 'pyvista', 'pyinstaller_vtk_args', '--exclude-module pyqtgraph.opengl'):
        assert gone not in workflow
    assert '--collect-data pyqtgraph' in workflow                         # its colour maps are data files
    assert not os.path.exists(os.path.join(root, 'tools', 'pyinstaller_vtk_args.py'))


def test_the_volume_rendering_setting_is_gone():
    from quantumscope.gui import preferences as prefs
    assert 'graphics/volume_method' not in prefs.PREFS and 'graphics/device' in prefs.PREFS
