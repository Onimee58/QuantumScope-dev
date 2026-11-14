"""The 3-D view: OpenGL through pyqtgraph (v0.9.11, in place of VTK).

One widget, View3D, draws everything the 3-D views need: a see-through density cloud (a volume),
lit surfaces (isosurfaces, glyphs), and flat overlays painted on top (captions, a colour bar, an
orientation marker, axis ticks). Overlays are painted with QPainter both on screen and on exported
images, so a saved PNG matches the window.

The camera keeps the conventions the VTK views had: z is up, the vertical field of view is 30°,
and view names ('isometric', 'xy', 'xz', 'yz', '+x', ...) look the same way they did, so earlier
screenshots, lessons and the user guide still match.
"""
import math

import numpy as np
from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QImage, QLinearGradient, QPainter, QPen, QSurfaceFormat
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from OpenGL import GL
from pyqtgraph import functions as fn
from pyqtgraph.opengl import shaders

BACKGROUND = '#101820'
VERTICAL_FOV = 30.0                                     # degrees, as VTK's default camera

# (azimuth, elevation) in degrees; the camera sits at that direction from the focal point.
VIEWS = {
    'isometric': (45.0, math.degrees(math.atan(1 / math.sqrt(2)))),
    'perspective': (-45.0, math.degrees(math.atan(0.85 / math.sqrt(2)))),   # the Hydrogen Explorer's default
    'xy': (-90.0, 90.0),            # top: looking down the z axis, y up
    'xz': (-90.0, 0.0),             # front: looking along +y, z up
    'yz': (0.0, 0.0),               # side: looking along -x, z up
    '+x': (0.0, 0.0), '+y': (90.0, 0.0), '+z': (-90.0, 90.0),
}

# Lit from the camera, on both sides of a surface (so open or inside-out surfaces never go dark),
# with a soft highlight: close to VTK's default headlight.
LIT = shaders.ShaderProgram('quantumscope-lit', [
    shaders.VertexShader("""
        uniform mat4 u_mvp;
        uniform mat3 u_normal;
        attribute vec4 a_position;
        attribute vec3 a_normal;
        attribute vec4 a_color;
        varying vec4 v_color;
        varying vec3 v_normal;
        void main() {
            v_normal = u_normal * a_normal;
            v_color = a_color;
            gl_Position = u_mvp * a_position;
        }
    """),
    shaders.FragmentShader("""
        #ifdef GL_ES
        precision mediump float;
        #endif
        varying vec4 v_color;
        varying vec3 v_normal;
        void main() {
            vec3 n = normalize(v_normal);
            float d = abs(n.z);
            float s = pow(d, 24.0);
            vec3 rgb = v_color.rgb * (0.28 + 0.72 * d) + vec3(0.28 * s);
            gl_FragColor = vec4(min(rgb, vec3(1.0)), v_color.a);
        }
    """),
])

OPAQUE = 'opaque'


def _translucent(cull):
    return {GL.GL_DEPTH_TEST: True, GL.GL_BLEND: True, GL.GL_CULL_FACE: True,
            'glBlendFunc': (GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA), 'glCullFace': (cull,)}


# ---- colour maps ----------------------------------------------------------------------------------------
def lut(name, n=256):
    """An n × 3 uint8 colour table: 'viridis', 'phase' (cyclic: light at ±π, dark at 0, like
    matplotlib's twilight) or 'coolwarm' (blue, light grey, red)."""
    if name == 'phase':
        return pg.colormap.get('CET-C3').getLookupTable(1.0, 0.0, n, alpha=False).astype(np.uint8)
    if name == 'coolwarm':
        stops = np.array([[59, 76, 192], [221, 221, 221], [180, 4, 38]], float)
        t = np.linspace(0, 2, n)
        return np.stack([np.interp(t, [0, 1, 2], stops[:, c]) for c in range(3)], axis=1).astype(np.uint8)
    return pg.colormap.get(name).getLookupTable(0.0, 1.0, n, alpha=False).astype(np.uint8)


def colours(values, table, lo, hi, nan=(128, 128, 128)):
    """Map values to RGBA floats (0..1) through a colour table; NaN gets the `nan` colour."""
    values = np.asarray(values, float)
    index = np.clip((values - lo) / (hi - lo) * (len(table) - 1), 0, len(table) - 1)
    bad = ~np.isfinite(index)
    rgb = table[np.where(bad, 0, index).astype(int)].astype(np.float32)
    rgb[bad] = nan
    return np.concatenate([rgb / 255, np.ones((len(rgb), 1), np.float32)], axis=1)


# ---- geometry ---------------------------------------------------------------------------------------------
def contour(field, level, origin, spacing):
    """The surface field = level (marching cubes), in world coordinates.

    Returns (vertices, faces); vertices shared between triangles are merged, so the surface is
    smoothly shaded. origin and spacing are the grid's first point and step (a number or 3 numbers);
    field[i, j, k] is the value at origin + (i, j, k) * spacing.
    """
    verts, faces = fn.isosurface(np.ascontiguousarray(field), float(level))
    if len(faces) == 0:
        return np.zeros((0, 3), np.float32), np.zeros((0, 3), np.uint32)
    unique, inverse = np.unique(np.round(verts, 5), axis=0, return_inverse=True)
    faces = inverse.reshape(-1)[faces]
    world = unique * np.broadcast_to(np.asarray(spacing, float), 3) + np.broadcast_to(np.asarray(origin, float), 3)
    return world.astype(np.float32), faces.astype(np.uint32)


class Mesh(gl.MeshData):
    """MeshData with vertex normals computed in one vectorized step (pyqtgraph's loops over vertices:
    about 0.1 s for a 96³ isosurface, every frame of the Dynamics 3D surface)."""
    def vertexNormals(self, indexed=None):
        if self._vertexNormals is None:
            faces = self.faces()
            normals = np.zeros(self._vertexes.shape, np.float64)
            face_normals = self.faceNormals()                    # area-weighted, as pyqtgraph sums them
            for corner in range(3):
                np.add.at(normals, faces[:, corner], face_normals)
            length = np.linalg.norm(normals, axis=1, keepdims=True)
            self._vertexNormals = (normals / np.where(length > 0, length, 1)).astype(np.float32)
        return self._vertexNormals if indexed is None else self._vertexNormals[self.faces()]


def _cube():
    v = np.array([[x, y, z] for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)], float)
    f = np.array([[0, 1, 3], [0, 3, 2], [4, 6, 7], [4, 7, 5], [0, 4, 5], [0, 5, 1],
                  [2, 3, 7], [2, 7, 6], [0, 2, 6], [0, 6, 4], [1, 5, 7], [1, 7, 3]])
    return v, f


def _sphere():
    md = gl.MeshData.sphere(rows=10, cols=16, radius=1.0)
    return md.vertexes(), md.faces()


SHAPES = {'sphere': _sphere, 'cube': _cube}


def glyphs(points, shape, size):
    """One mesh holding a small sphere or cube (half-width `size`) at each point."""
    base_v, base_f = SHAPES[shape]()
    points = np.asarray(points, float).reshape(-1, 3)
    verts = (base_v[None] * size + points[:, None]).reshape(-1, 3)
    faces = (base_f[None] + (np.arange(len(points)) * len(base_v))[:, None, None]).reshape(-1, 3)
    return verts.astype(np.float32), faces.astype(np.uint32)


# ---- the view -----------------------------------------------------------------------------------------------
class View3D(gl.GLViewWidget):
    """A 3-D view: drag to rotate, scroll to zoom, Ctrl-drag or middle-drag to pan.

    Views in separate windows need Qt.AA_ShareOpenGLContexts set before the QApplication is
    created (quantumscope.__main__ does): pyqtgraph compiles each shader once, for all contexts.
    """
    cameraChanged = Signal()                 # the user rotated, zoomed or panned
    clicked = Signal(float, float)           # a click without dragging, in widget coordinates

    def __init__(self, parent=None, background=BACKGROUND):
        super().__init__(parent)
        surface = QSurfaceFormat(self.format())
        surface.setSamples(4)                                    # smooth edges where the driver allows
        self.setFormat(surface)
        self.setBackgroundColor(background)
        self.setMinimumSize(120, 120)
        self.named = {}                                          # name → item(s), for the caller and tests
        self._texts, self._bar, self._triad, self._ticks = [], None, None, None
        self._lo = self._hi = None                               # bounds of what is drawn
        self._press = None
        self._fitted = None                                      # radius of the last fit, while it holds
        self.setCameraPosition(distance=10, elevation=VIEWS['isometric'][1], azimuth=VIEWS['isometric'][0])
        self._update_fov()

    # ---- scene ---------------------------------------------------------------------------------
    def clear(self):
        for item in list(self.items):
            self.removeItem(item)
        self.named = {}
        self._texts, self._bar, self._triad, self._ticks = [], None, None, None
        self._lo = self._hi = None
        self.update()

    def remove(self, name):
        for item in self.named.pop(name, ()):
            if item in self.items:
                self.removeItem(item)
        self.update()

    def _add(self, items, name, lo=None, hi=None):
        for item in items:
            self.addItem(item)
        if name is not None:
            self.named[name] = items
        if lo is not None:
            self._lo = np.minimum(self._lo, lo) if self._lo is not None else np.asarray(lo, float)
            self._hi = np.maximum(self._hi, hi) if self._hi is not None else np.asarray(hi, float)
        self.update()
        return items

    def surface(self, verts, faces, color=(0.0, 0.75, 1.0), opacity=1.0, vertex_colors=None, smooth=True, name=None):
        """A lit triangle mesh. See-through meshes are drawn back faces first, then front faces."""
        if len(faces) == 0:
            return []
        if vertex_colors is not None:
            vertex_colors = np.array(vertex_colors, np.float32)
            vertex_colors[:, 3] = opacity
        data = Mesh(vertexes=verts, faces=faces, vertexColors=vertex_colors)
        rgb = fn.mkColor(color).getRgbF()[:3] if isinstance(color, str) else tuple(map(float, color[:3]))
        rgba = (*rgb, float(opacity))
        if opacity >= 1:
            items = [gl.GLMeshItem(meshdata=data, smooth=smooth, shader=LIT, color=rgba, glOptions=OPAQUE)]
        else:
            items = [gl.GLMeshItem(meshdata=data, smooth=smooth, shader=LIT, color=rgba, glOptions=_translucent(cull))
                     for cull in (GL.GL_FRONT, GL.GL_BACK)]
            for depth, item in enumerate(items):
                item.setDepthValue(20 + depth)
        verts = np.asarray(verts, float)
        return self._add(items, name, verts.min(axis=0), verts.max(axis=0))

    def volume(self, rgba, origin, spacing, name=None):
        """A see-through volume from an (nx, ny, nz, 4) uint8 array of colours and opacities."""
        item = gl.GLVolumeItem(np.ascontiguousarray(rgba), sliceDensity=1, smooth=True, glOptions='translucent')
        step = float(spacing)
        item.scale(step, step, step)
        start = float(origin) - 0.5 * step                      # voxel i is centred at origin + i·step
        item.translate(start, start, start)
        item.setDepthValue(10)
        lo = np.full(3, float(origin))
        return self._add([item], name, lo, lo + step * (np.array(rgba.shape[:3]) - 1))[0]

    def text(self, text, corner='upper_left'):
        self._texts.append((text, corner))
        self.update()

    def colour_bar(self, table, lo, hi, title):
        self._bar = (np.asarray(table), float(lo), float(hi), title)
        self.update()

    def axes(self, labels=('x', 'y', 'z')):
        """An orientation marker in the lower-left corner that turns with the camera."""
        self._triad = tuple(labels)
        self.update()

    def bounds(self, lo, hi, titles=('x', 'y', 'z'), ticks=5):
        """A box around the region, with ticks and coordinates along three edges."""
        lo, hi = np.asarray(lo, float), np.asarray(hi, float)
        corners = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
        edges = [(0, 1), (2, 3), (4, 5), (6, 7), (0, 2), (1, 3), (4, 6), (5, 7), (0, 4), (1, 5), (2, 6), (3, 7)]
        line = gl.GLLinePlotItem(pos=corners[np.array(edges).ravel()], mode='lines', color=(1, 1, 1, 0.45),
                                 width=1, antialias=True)
        self._add([line], 'bounds')
        values = [np.linspace(lo[a], hi[a], ticks) for a in range(3)]
        self._ticks = (lo, hi, values, tuple(titles))
        self.update()

    # ---- camera --------------------------------------------------------------------------------
    def resizeGL(self, w, h):
        super().resizeGL(w, h)
        self._update_fov()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_fov()

    def _update_fov(self):
        """pyqtgraph's field of view is horizontal: keep the vertical one at 30° as the window changes shape."""
        w, h = max(self.width(), 1), max(self.height(), 1)
        self.opts['fov'] = math.degrees(2 * math.atan(math.tan(math.radians(VERTICAL_FOV / 2)) * w / h))
        if getattr(self, '_fitted', None):
            self.opts['distance'] = self._fit_distance(self._fitted)

    def look(self, view='isometric', distance=None, center=(0.0, 0.0, 0.0)):
        """Look at `center` from a named direction (VIEWS) or an (azimuth, elevation) pair."""
        azimuth, elevation = VIEWS[view] if isinstance(view, str) else view
        self._fitted = None
        self.setCameraPosition(pos=pg.Vector(*map(float, center)), azimuth=azimuth, elevation=elevation,
                               distance=float(distance if distance is not None else self.opts['distance']))
        self.update()

    def fit(self, view=None, lo=None, hi=None):
        """Centre what is drawn (or the box lo..hi) and move back until it all fits (VTK's reset_camera).

        Until the user moves the camera, the fit follows the view's size: a view fitted before its
        window is laid out still fits once it is."""
        if view is not None:
            self.look(view)
        lo, hi = (self._lo, self._hi) if lo is None else (np.asarray(lo, float), np.asarray(hi, float))
        if lo is None:
            return
        centre = (lo + hi) / 2
        radius = max(float(np.linalg.norm(hi - lo)) / 2, 1e-6)
        self.look((self.opts['azimuth'], self.opts['elevation']), self._fit_distance(radius), centre)
        self._fitted = radius

    def _fit_distance(self, radius):
        aspect = min(1.0, max(self.width(), 1) / max(self.height(), 1))
        half = math.atan(math.tan(math.radians(VERTICAL_FOV / 2)) * aspect)
        return radius / math.sin(half)

    def camera(self):
        o = self.opts
        return dict(center=tuple(float(c) for c in (o['center'].x(), o['center'].y(), o['center'].z())),
                    distance=float(o['distance']), azimuth=float(o['azimuth']), elevation=float(o['elevation']))

    def set_camera(self, camera):
        self.look((camera['azimuth'], camera['elevation']), camera['distance'], camera['center'])

    def eye(self):
        """The camera's position in world coordinates."""
        p = self.cameraPosition()
        return np.array([p.x(), p.y(), p.z()])

    def direction(self):
        """Unit vector from the focal point towards the camera."""
        c = self.camera()
        a, e = math.radians(c['azimuth']), math.radians(c['elevation'])
        return np.array([math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)])

    def orbit(self, azim, elev):
        super().orbit(azim, elev)
        self._fitted = None
        self.cameraChanged.emit()

    def pan(self, dx, dy, dz, relative='global'):
        super().pan(dx, dy, dz, relative)
        self._fitted = None
        self.cameraChanged.emit()

    def wheelEvent(self, event):
        super().wheelEvent(event)
        self._fitted = None
        self.cameraChanged.emit()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self._press = event.position()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self._press is not None and (event.position() - self._press).manhattanLength() < 5 \
                and event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(float(event.position().x()), float(event.position().y()))
        self._press = None

    # ---- projection ------------------------------------------------------------------------------
    def _matrix(self, width, height):
        viewport = (0, 0, width, height)
        m = self.projectionMatrix(viewport, viewport) * self.viewMatrix()
        return np.array(m.data(), float).reshape(4, 4).T          # QMatrix4x4.data() is column-major

    def project(self, points, width=None, height=None):
        """Screen positions (x right, y down, in pixels) of 3-D points, and whether each is in front."""
        width, height = width or self.width(), height or self.height()
        p = np.c_[np.asarray(points, float).reshape(-1, 3), np.ones(len(np.asarray(points).reshape(-1, 3)))]
        clip = p @ self._matrix(width, height).T
        w = clip[:, 3]
        safe = np.where(np.abs(w) < 1e-12, 1e-12, w)
        x = (clip[:, 0] / safe + 1) / 2 * width
        y = (1 - clip[:, 1] / safe) / 2 * height
        return np.c_[x, y], w > 0

    def nearest_on_screen(self, points, x, y, within=14):
        """Index of the point drawn nearest (x, y), or None if none is within `within` pixels."""
        if len(points) == 0:
            return None
        xy, front = self.project(points)
        d = np.hypot(xy[:, 0] - x, xy[:, 1] - y)
        d[~front] = np.inf
        k = int(np.argmin(d))
        return k if d[k] <= within else None

    # ---- overlays ----------------------------------------------------------------------------------
    def paintGL(self):
        super().paintGL()
        if self._texts or self._bar or self._triad or self._ticks:
            painter = QPainter(self)
            try:
                self._paint_overlay(painter, self.width(), self.height(), 1.0)
            finally:
                painter.end()

    def _paint_overlay(self, painter, width, height, scale):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        font = QFont(painter.font())
        font.setPointSizeF(9 * scale)
        painter.setFont(font)
        white = QColor('#f0f4f8')
        painter.setPen(white)
        margin = 8 * scale
        rows = {}
        for text, corner in self._texts:
            row = rows.get(corner, 0)
            rows[corner] = row + 1
            y = margin + (row + 0.8) * 16 * scale if corner.startswith('upper') else height - margin - row * 16 * scale
            rect = QRectF(margin, y - 14 * scale, width - 2 * margin, 18 * scale)
            align = Qt.AlignmentFlag.AlignLeft if corner.endswith('left') else Qt.AlignmentFlag.AlignRight
            painter.drawText(rect, align | Qt.AlignmentFlag.AlignVCenter, text)
        if self._ticks:
            self._paint_ticks(painter, width, height, scale)
        if self._bar:
            self._paint_bar(painter, width, height, scale)
        if self._triad:
            self._paint_triad(painter, height, scale)

    def _paint_bar(self, painter, width, height, scale):
        table, lo, hi, title = self._bar
        x, w = width * 0.915, max(10 * scale, width * 0.028)
        top, bottom = height * 0.27, height * 0.75
        gradient = QLinearGradient(0, bottom, 0, top)
        for k in range(0, len(table), max(1, len(table) // 32)):
            gradient.setColorAt(k / (len(table) - 1), QColor(*map(int, table[k][:3])))
        gradient.setColorAt(1.0, QColor(*map(int, table[-1][:3])))
        painter.setPen(QPen(QColor(255, 255, 255, 120), 1 * scale))
        painter.setBrush(gradient)
        painter.drawRect(QRectF(x, top, w, bottom - top))
        painter.setPen(QColor('#f0f4f8'))
        painter.drawText(QRectF(x - 60 * scale, top - 22 * scale, w + 66 * scale, 16 * scale),
                         Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, title)
        for value, y in ((hi, top), ((lo + hi) / 2, (top + bottom) / 2), (lo, bottom)):
            painter.drawText(QRectF(x - 64 * scale, y - 8 * scale, 60 * scale, 16 * scale),
                             Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, f'{value:.3g}')
        painter.setBrush(Qt.BrushStyle.NoBrush)

    def _paint_triad(self, painter, height, scale):
        view = np.array(self.viewMatrix().data(), float).reshape(4, 4).T[:3, :3]     # world → camera
        centre = QPointF(46 * scale, height - 46 * scale)
        length = 30 * scale
        axes = [(view @ np.eye(3)[a], label, colour) for a, (label, colour) in
                enumerate(zip(self._triad, ('#ff6b6b', '#7be07b', '#6ba8ff')))]
        for direction, label, colour in sorted(axes, key=lambda t: t[0][2]):      # farthest first
            end = QPointF(centre.x() + length * direction[0], centre.y() - length * direction[1])
            painter.setPen(QPen(QColor(colour), 2.4 * scale, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(centre, end)
            painter.setPen(QColor(colour))
            tip = QPointF(centre.x() + (length + 9 * scale) * direction[0],
                          centre.y() - (length + 9 * scale) * direction[1])
            painter.drawText(QRectF(tip.x() - 30 * scale, tip.y() - 8 * scale, 60 * scale, 16 * scale),
                             Qt.AlignmentFlag.AlignCenter, label)

    def _paint_ticks(self, painter, width, height, scale):
        lo, hi, values, titles = self._ticks
        painter.setPen(QColor(240, 244, 248, 210))
        for axis in range(3):
            base = lo.copy()
            points = np.repeat(base[None], len(values[axis]), axis=0)
            points[:, axis] = values[axis]
            xy, front = self.project(points, width, height)
            for (x, y), ok, value in zip(xy, front, values[axis]):
                if ok:
                    painter.drawText(QRectF(x - 30 * scale, y + 2 * scale, 60 * scale, 14 * scale),
                                     Qt.AlignmentFlag.AlignCenter, f'{value:g}')
            middle = base.copy()
            middle[axis] = (lo[axis] + hi[axis]) / 2
            (x, y), ok = (v[0] for v in self.project(middle, width, height))
            if ok:
                painter.drawText(QRectF(x - 50 * scale, y + 14 * scale, 100 * scale, 16 * scale),
                                 Qt.AlignmentFlag.AlignCenter, titles[axis])

    # ---- output -------------------------------------------------------------------------------------
    def image(self, scale=1):
        """The view as a QImage, `scale` times the window's size, with its overlays."""
        if not self.isValid():
            raise RuntimeError('The 3-D view has no OpenGL context (it has not been shown, or OpenGL is unavailable)')
        width, height = int(self.width() * scale), int(self.height() * scale)
        pixels = np.ascontiguousarray(self.renderToArray((width, height)))
        self.update()
        picture = QImage(pixels.data, width, height, 4 * width, QImage.Format.Format_RGB32).copy()
        painter = QPainter(picture)
        try:
            self._paint_overlay(painter, width, height, scale)
        finally:
            painter.end()
        return picture

    def rgb(self, scale=1):
        """The view as an (height, width, 3) uint8 array."""
        picture = self.image(scale).convertToFormat(QImage.Format.Format_RGB888)
        w, h = picture.width(), picture.height()
        data = np.frombuffer(picture.constBits(), np.uint8, count=picture.bytesPerLine() * h)
        return data.reshape(h, picture.bytesPerLine())[:, :3 * w].reshape(h, w, 3).copy()

    def save(self, path, scale=1):
        if not self.image(scale).save(str(path)):
            raise OSError(f'Could not write {path}')
        return path

    def gl_information(self):
        """Renderer, vendor and version of the OpenGL context actually in use."""
        if not self.isValid():
            return 'OpenGL context not created yet (open a 3-D view first).'
        self.makeCurrent()
        try:
            read = lambda name: GL.glGetString(name).decode(errors='replace')     # noqa: E731
            return '\n'.join((f'OpenGL renderer: {read(GL.GL_RENDERER)}', f'OpenGL vendor: {read(GL.GL_VENDOR)}',
                              f'OpenGL version: {read(GL.GL_VERSION)}',
                              f'Shading language: {read(GL.GL_SHADING_LANGUAGE_VERSION)}'))
        finally:
            self.doneCurrent()
