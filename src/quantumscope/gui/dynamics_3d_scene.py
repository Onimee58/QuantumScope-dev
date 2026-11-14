"""3D hydrogen-superposition scene, independent of the dialog's other controls.

Draws into a View3D (quantumscope.visualization.gl3d). Densities are exact; the volume's colours
and opacities only change appearance.
"""
import numpy as np

from quantumscope.visualization import gl3d

VIEWS = ('isometric', 'xy', 'xz', 'yz')       # xy: top (down the z axis), xz: front, yz: side
SURFACE = '#4eb5d6'
CLOUD_GAIN = 0.55                              # one textured slice per grid plane: per-slice opacity


def sigmoid(x):
    """The cloud's opacity against display intensity (VTK's 'sigmoid' transfer function)."""
    return 1 / (1 + np.exp(-(20 * np.asarray(x, float) - 10)))


class HydrogenScene3D:
    def __init__(self, view):
        self.view = view
        self.model = None
        self._volume = None         # the volume item; playback replaces its data in place
        self._volume_key = None     # the visibility it was built for
        self._view_set = False      # the camera is placed once; later changes keep the user's view
        self._table = gl3d.lut('viridis')

    # ---- data ------------------------------------------------------------------------
    def set_model(self, model, n, extent):
        """Sample both eigenstates once on an n³ grid of half-width `extent`."""
        self.model = model
        axis = np.linspace(-extent, extent, n)
        x, y, z = np.meshgrid(axis, axis, axis, indexing='ij', sparse=True)
        psi_a = np.asarray(model.first.wavefunction(x, y, z), dtype=np.complex64)
        psi_b = np.asarray(model.second.wavefunction(x, y, z), dtype=np.complex64)
        shape = (n, n, n)
        self._aa = np.broadcast_to(np.abs(psi_a) ** 2, shape).astype(np.float32).copy()
        self._bb = np.broadcast_to(np.abs(psi_b) ** 2, shape).astype(np.float32).copy()
        self._cross = np.broadcast_to(np.conjugate(psi_a) * psi_b, shape).astype(np.complex64).copy()
        self._peak = max(float(max(np.max(self._aa), np.max(self._bb)) * 2.5), 1e-12)
        self._origin, self._step = float(axis[0]), float(axis[1] - axis[0])
        self._reset_scene()

    def clear(self):
        self.model = None
        self._reset_scene()

    def _reset_scene(self):
        self.view.clear()
        self._volume = self._volume_key = None

    def frame_density(self, fraction):
        """Exact density at `fraction` of a beat period (stationary if degenerate)."""
        p = self.model.probability_first
        theta = (self.model.relative_phase - 2 * np.pi * fraction
                 if np.isfinite(self.model.beat_period_fs) else self.model.relative_phase)
        return (p * self._aa + (1 - p) * self._bb
                + 2 * np.sqrt(p * (1 - p)) * np.real(np.exp(1j * theta) * self._cross)).clip(0).astype(np.float32)

    def cloud(self, density, visibility):
        """RGBA bytes of the cloud for one frame."""
        intensity = np.clip((density / self._peak) ** (0.60 / visibility), 0, 1)
        rgba = np.empty(density.shape + (4,), np.uint8)
        rgba[..., :3] = self._table[(intensity * 255).astype(np.uint8)]
        rgba[..., 3] = np.clip(sigmoid(intensity) * CLOUD_GAIN * 255, 0, 255).astype(np.uint8)
        return rgba

    # ---- drawing ----------------------------------------------------------------------
    def draw(self, fraction, mode='volume', visibility=1.4):
        """Draw the frame. Playback updates the existing volume in place."""
        if self.model is None:
            return
        density = self.frame_density(fraction)
        view = self.view
        if mode == 'volume':
            key = round(visibility, 6)
            rgba = self.cloud(density, visibility)
            if self._volume is not None and 'cloud' in view.named:
                self._volume.setData(rgba)
                view.update()
            else:
                view.remove('surface')
                self._volume = view.volume(rgba, self._origin, self._step, name='cloud')
            self._volume_key = key
        else:
            # The surface's shape changes with time, so it is recomputed each frame.
            positive = density[density > 0]
            cutoff = float(np.quantile(positive, .75)) if positive.size else 1e-12
            verts, faces = gl3d.contour(density, cutoff, self._origin, self._step)
            view.remove('cloud')
            view.remove('surface')
            self._volume = self._volume_key = None
            view.surface(verts, faces, SURFACE, opacity=min(.95, .50 + .12 * visibility), name='surface')
        view.axes()
        if not self._view_set:
            self.reset_view('isometric')

    # ---- camera ------------------------------------------------------------------------
    def reset_view(self, view='isometric'):
        """Standard viewing direction, centered and zoomed to fit the data."""
        if self.model is None:
            self.view.fit(view)
        else:                                                  # the whole grid, whatever is drawn
            lo = np.full(3, self._origin)
            self.view.fit(view, lo, lo + self._step * (np.array(self._aa.shape) - 1))
        self._view_set = True
