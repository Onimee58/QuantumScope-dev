"""The 3-D decision view of the Quantum Kernel Classifier (v0.8.2).

Points are shown along three axes (principal components, or axes chosen to show the class
separation), with the classifier's decision boundary as a surface (f = 0) and, for an SVM, the
margins (f = ±1). With more than two classes (v0.9.3), each class's region has its own surface,
in its colour, where it takes over from the next most confident class. With more than three features this is a slice through the data's mean: the caption
gives the share of points where the slice agrees with the real classifier. Drag to rotate, scroll to
zoom, Shift-drag to pan; click a point to see its sample. Nothing is computed until the tab is opened.
"""
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFileDialog, QHBoxLayout, QLabel, QPushButton, QSlider,
                               QVBoxLayout, QWidget)

from quantumscope.ml import views as W

PLUS, MINUS, WRONG, HALO = '#5ae6ff', '#ff9a5a', '#ff4d4d', '#fff3a0'


def make_plotter(parent):
    """The 3-D widget (replaced by an off-screen one in tests)."""
    from pyvistaqt import QtInteractor
    return QtInteractor(parent)


class Decision3DView(QWidget):
    def __init__(self, parent=None, on_pick=None):
        super().__init__(parent)
        self.on_pick = on_pick                                   # on_pick(which, index): show that sample
        self.plotter = None
        self.result = self.model = self.geometry = None
        self._pending = False
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        row = QHBoxLayout()
        self.axes_box = QComboBox()
        for label, key in W.AXES:
            self.axes_box.addItem(label, key)
        row.addWidget(QLabel('Axes'))
        row.addWidget(self.axes_box)
        self.show_boundary, self.show_margins, self.show_support = (QCheckBox('Boundary'), QCheckBox('Margins'),
                                                                     QCheckBox('Support vectors'))
        self.show_boundary.setChecked(True)
        self.show_support.setChecked(True)
        for box in (self.show_boundary, self.show_margins, self.show_support):
            row.addWidget(box)
            box.toggled.connect(lambda *_: self.render())
        row.addWidget(QLabel('Surface'))
        self.opacity = QSlider(Qt.Orientation.Horizontal)
        self.opacity.setRange(10, 100)
        self.opacity.setValue(45)
        self.opacity.setMaximumWidth(110)
        self.opacity.valueChanged.connect(lambda *_: self.render())
        row.addWidget(self.opacity)
        row.addStretch(1)
        layout.addLayout(row)
        views = QHBoxLayout()
        self.preset_buttons = {}
        for name in ('Front', 'Top', 'Side', 'Isometric', 'Reset'):
            button = QPushButton(name)
            button.clicked.connect(lambda _=False, n=name: self.preset(n))
            views.addWidget(button)
            self.preset_buttons[name] = button
        views.addStretch(1)
        self.save_button, self.gif_button = QPushButton('Save image…'), QPushButton('Save rotating GIF…')
        self.save_button.clicked.connect(lambda: self.save_image())
        self.gif_button.clicked.connect(lambda: self.save_gif())
        views.addWidget(self.save_button)
        views.addWidget(self.gif_button)
        layout.addLayout(views)
        self.caption = QLabel('Train the classifier, then open this tab to see the 3-D view.')
        self.caption.setWordWrap(True)
        self.caption.setObjectName('muted')
        layout.addWidget(self.caption)
        self.holder = QVBoxLayout()
        layout.addLayout(self.holder, 1)
        self.axes_box.currentIndexChanged.connect(lambda *_: self.compute())

    # ---- data ---------------------------------------------------------------------------------
    def set_result(self, result, model):
        """A new trained classifier: computed when the view is visible (now, or when the tab opens)."""
        self.result, self.model, self.geometry = result, model, None
        many = result is not None and result['prepared'].k > 2
        self.show_margins.setEnabled(model is not None and model.settings.get('method') == 'svm' and not many)
        self.show_margins.setToolTip('With more than two classes, each class has its own classifier: the '
                                     'boundaries show where one class takes over from another' if many else '')
        if self.isVisible():
            self.compute()
        else:
            self._pending = True

    def showEvent(self, event):
        super().showEvent(event)
        if self._pending:
            self._pending = False
            self.compute()

    def compute(self):
        """Axes, projections, agreement and the decision grid, in the background; returns the run."""
        if self.result is None or self.model is None:
            return None
        p = self.result['prepared']
        if p.X_train.shape[1] < 3:
            self.caption.setText('The 3-D view needs at least 3 features: with 1 or 2, the decision regions show '
                                 'the whole picture.')
            return None
        kind, model = self.axes_box.currentData(), self.model
        X_all = np.r_[p.X_train, p.X_test]

        def work(report, cancelled):
            axes = W.axes3d(p.X_train, p.y_train, kind)
            P_train, P_test = W.project(axes, p.X_train), W.project(axes, p.X_test)
            agreement = W.slice_agreement(model.decision, axes, X_all)
            grid = W.decision_grid(model.decision, axes, np.r_[P_train, P_test], W.grid_resolution(p.X_train.shape[1]),
                                   cancelled=cancelled)
            return None if grid is None else dict(axes=axes, P_train=P_train, P_test=P_test, agreement=agreement,
                                                  ticks=grid[0], f=grid[1])
        self.caption.setText('Computing the 3-D view…')
        from quantumscope.gui.background import Run
        previous = getattr(self, 'run', None)
        if previous is not None and previous.running():
            previous.cancel()
        self.run = Run(work, owner=self, on_done=self._computed,
                       on_error=lambda exc, details: self.caption.setText(f'The 3-D view failed: {exc}')).start()
        return self.run

    def _computed(self, geometry):
        if geometry is None:
            return
        self.geometry = geometry
        axes, n = geometry['axes'], self.result['prepared'].X_train.shape[1]
        names = ', '.join(f'{name}{"" if name == tag else f" ({tag})"} {share:.0%}'
                          for name, tag, share in zip(axes['names'], axes['short'], axes['shares']))
        slice_note = ('' if n == 3 else
                      f' A slice through {n}-D: the surface agrees with the classifier on '
                      f'{geometry["agreement"]:.0%} of the points.')
        self.caption.setText(f'Axes: {names}.{slice_note} Spheres: training · cubes: test · red: mistakes · halo: '
                             f'support vectors. Drag to rotate, scroll to zoom; click a point to see it.')
        self.render(reset_camera=True)

    # ---- drawing ------------------------------------------------------------------------------
    def _ensure_plotter(self):
        if self.plotter is None:
            self.plotter = make_plotter(self)
            self.holder.addWidget(self.plotter)
            self.plotter.set_background('#0b1420')
            self.plotter.enable_point_picking(callback=self._picked, left_clicking=True, show_message=False,
                                              show_point=False, pickable_window=True)
        return self.plotter

    def render(self, reset_camera=False):
        import pyvista as pv
        g = self.geometry
        if g is None:
            return
        plotter = self._ensure_plotter()
        camera = None if reset_camera else plotter.camera_position
        plotter.clear()
        p, r = self.result['prepared'], self.result
        ticks, f = g['ticks'], g['f']
        from quantumscope.gui.qml_experiments import palette
        colours = palette(p.k)
        if f.ndim == 4 and self.show_boundary.isChecked():           # each class's region, in its colour
            spacing = [float(t[1] - t[0]) for t in ticks]
            margins = W.class_margins(f)
            opacity = self.opacity.value() / 100
            for c, colour in colours:
                if (margins[..., c] > 0).any():
                    volume = pv.ImageData(dimensions=f.shape[:3], spacing=spacing, origin=[float(t[0]) for t in ticks])
                    volume.point_data['m'] = margins[..., c].ravel(order='F')
                    surface = volume.contour([0.0], scalars='m')
                    if surface.n_points:
                        plotter.add_mesh(surface, color=colour, opacity=opacity * 0.7, smooth_shading=True,
                                         name=f'region{c}')
        elif self.show_boundary.isChecked() or self.show_margins.isChecked():
            spacing = [float(t[1] - t[0]) for t in ticks]
            volume = pv.ImageData(dimensions=f.shape, spacing=spacing, origin=[float(t[0]) for t in ticks])
            volume.point_data['f'] = f.ravel(order='F')                 # x varies fastest in VTK
            opacity = self.opacity.value() / 100
            if self.show_boundary.isChecked():
                surface = volume.contour([0.0], scalars='f')
                if surface.n_points:
                    plotter.add_mesh(surface, color='#f0f4ff', opacity=opacity, smooth_shading=True, name='boundary')
            if self.show_margins.isChecked() and self.show_margins.isEnabled():
                for level, colour in ((1.0, PLUS), (-1.0, MINUS)):
                    margin = volume.contour([level], scalars='f')
                    if margin.n_points:
                        plotter.add_mesh(margin, color=colour, opacity=opacity * 0.4, name=f'margin{level}')
        wrong = r['predicted'] != p.y_test
        everything = np.r_[g['P_train'], g['P_test']]
        size = 0.018 * float(np.max(everything.max(axis=0) - everything.min(axis=0)) or 1.0)   # markers follow the data
        for label, colour in colours:
            pts = g['P_train'][p.y_train == label]
            if len(pts):
                plotter.add_mesh(pv.PolyData(pts).glyph(geom=pv.Sphere(radius=size), scale=False, orient=False),
                                 color=colour, smooth_shading=True)
            pts = g['P_test'][(p.y_test == label) & ~wrong]
            if len(pts):
                plotter.add_mesh(pv.PolyData(pts).glyph(geom=pv.Cube(x_length=2 * size, y_length=2 * size, z_length=2 * size),
                                                        scale=False, orient=False), color=colour)
        if wrong.any():
            plotter.add_mesh(pv.PolyData(g['P_test'][wrong]).glyph(geom=pv.Cube(x_length=2.6 * size, y_length=2.6 * size,
                                                                                z_length=2.6 * size), scale=False,
                                                                   orient=False), color=WRONG)
        support = getattr(r.get('model'), 'support', None)
        if self.show_support.isChecked() and support is not None and len(support):
            plotter.add_mesh(pv.PolyData(g['P_train'][support]).glyph(geom=pv.Sphere(radius=1.8 * size), scale=False,
                                                                      orient=False),
                             color=HALO, opacity=0.25)
        short = g['axes']['short']                                    # full names are in the caption
        plotter.add_axes(xlabel=short[0], ylabel=short[1], zlabel=short[2], color='#d8e6f3')
        if camera is not None:
            plotter.camera_position = camera
        else:
            plotter.view_isometric()
            plotter.reset_camera()
        plotter.render()

    def preset(self, name):
        if self.plotter is None or self.geometry is None:
            return
        {'Front': self.plotter.view_xz, 'Top': self.plotter.view_xy, 'Side': self.plotter.view_yz,
         'Isometric': self.plotter.view_isometric}.get(name, self.plotter.view_isometric)()
        self.plotter.reset_camera()
        self.plotter.render()

    # ---- picking ------------------------------------------------------------------------------
    def nearest(self, point):
        """The sample nearest a picked 3-D point: ('train' or 'test', index)."""
        g = self.geometry
        best = None
        for which, P in (('train', g['P_train']), ('test', g['P_test'])):
            if len(P):
                d = np.linalg.norm(P - np.asarray(point, float), axis=1)
                k = int(np.argmin(d))
                if best is None or d[k] < best[0]:
                    best = (float(d[k]), which, k)
        return best[1], best[2]

    def _picked(self, point, *rest):
        if point is None or self.geometry is None or self.on_pick is None:
            return
        self.on_pick(*self.nearest(point))

    # ---- saving -------------------------------------------------------------------------------
    def save_image(self, path=None):
        if self.plotter is None or self.geometry is None:
            return None
        if path is None:
            path, _ = QFileDialog.getSaveFileName(self, 'Save image', 'decision-3d.png', 'PNG image (*.png)')
            if not path:
                return None
        if not path.lower().endswith('.png'):
            path += '.png'
        self.plotter.screenshot(path, scale=2)
        return path

    def save_gif(self, path=None, frames=36):
        """A full turn around the vertical axis, as an animated GIF (for slides)."""
        from PIL import Image
        if self.plotter is None or self.geometry is None:
            return None
        if path is None:
            path, _ = QFileDialog.getSaveFileName(self, 'Save rotating GIF', 'decision-3d.gif', 'GIF animation (*.gif)')
            if not path:
                return None
        if not path.lower().endswith('.gif'):
            path += '.gif'
        camera = self.plotter.camera_position
        images = []
        for _ in range(frames):
            self.plotter.camera.azimuth += 360 / frames
            self.plotter.render()
            images.append(Image.fromarray(self.plotter.screenshot(return_img=True)))
        self.plotter.camera_position = camera
        self.plotter.render()
        images[0].save(path, save_all=True, append_images=images[1:], duration=80, loop=0)
        return path
