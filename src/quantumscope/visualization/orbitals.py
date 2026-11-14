"""The Hydrogen Explorer's 3-D drawing, with probability-aware framing (OpenGL view since v0.9.11)."""
import numpy as np
from quantumscope.visualization.phase import phase_with_node_mask
from quantumscope.physics.hydrogen import enclosing_density_threshold
from quantumscope.visualization import gl3d

DEEPSKYBLUE = (0.0, 0.75, 1.0)
ORANGE = (1.0, 0.65, 0.0)
POSITIVE, NEGATIVE = (0.84, 0.30, 0.25), (0.30, 0.42, 0.88)     # coolwarm's ends
TRANSFER = (0, .003, .01, .025, .05, .09, .15, .25)       # the cloud's opacity against display intensity
CLOUD_GAIN = 1.6                                           # one slice per voxel needs a little more than VTK's ray caster


def probability_radius(axis, density, fraction=0.995):
    """Radius containing fraction of *sampled* probability, used only for camera framing."""
    step = float(axis[1] - axis[0])
    x, y, z = np.meshgrid(axis, axis, axis, indexing="ij", sparse=True)
    radii = np.sqrt(x*x + y*y + z*z).ravel()
    weights = density.ravel()
    order = np.argsort(radii)
    cumulative = np.cumsum(weights[order], dtype=np.float64)
    if cumulative.size == 0 or cumulative[-1] <= 0:
        return max(step, float(np.max(np.abs(axis))))
    index = np.searchsorted(cumulative, fraction * cumulative[-1])
    return float(max(3 * step, radii[order[min(index, len(order) - 1)]]))


def cloud_colours(display, opacity_strength=1.0, table=None):
    """RGBA bytes for the density cloud: viridis colour, opacity from the transfer function."""
    table = gl3d.lut('viridis') if table is None else table
    display = np.clip(display, 0.0, 1.0)
    alpha = np.interp(display, np.linspace(0, 1, len(TRANSFER)), TRANSFER) * opacity_strength * CLOUD_GAIN
    rgba = np.empty(display.shape + (4,), np.uint8)
    rgba[..., :3] = table[(display * 255).astype(np.uint8)]
    rgba[..., 3] = np.clip(alpha * 255, 0, 255).astype(np.uint8)
    return rgba


def draw_orbital(view, axis, density, psi, mode, enclosed=90, opacity_strength=1.0,
                 phase_coloring=False, show_grid=False, camera_view="Perspective", zoom=1.0):
    """Draw true spatial field; visual transfer function does not modify exported physics.

    Returns (a description of how it was drawn, the framing radius)."""
    view.clear()
    drawn = "OpenGL surface"
    radius = probability_radius(axis, density)
    step, origin = float(axis[1] - axis[0]), float(axis[0])
    if mode == "Density cloud":
        peak = float(density.max())
        if peak <= 0:
            raise ValueError("Probability density is zero")
        # Perceptual enhancement only, not probability/density remapping in science arrays.
        display = np.power(np.clip(density / peak, 0.0, 1.0), 0.35)
        view.volume(cloud_colours(display, opacity_strength), origin, step, name="cloud")
        drawn = "OpenGL volume (one textured slice per grid plane)"
        # Explain intensity transformation rather than incorrectly label it density.
        view.text("Display intensity = (density / peak)^0.35")
    elif mode == "Probability enclosure":
        level = enclosing_density_threshold(density, step, enclosed / 100)
        verts, faces = gl3d.contour(density, level, origin, step)
        if len(faces):
            if phase_coloring:
                # Interpolate the *complex wavefunction* at surface vertices, not
                # nearest voxel cell centers. Nearest-cell phase coloring created
                # staircase/triangle artifacts around nodal features.
                from scipy.ndimage import map_coordinates
                coords = ((verts - origin) / step).T
                real = map_coordinates(np.real(psi), coords, order=1, mode="nearest")
                imag = map_coordinates(np.imag(psi), coords, order=1, mode="nearest")
                phase = phase_with_node_mask(real, imag, float(np.sqrt(np.max(density))))
                table = gl3d.lut("phase")
                view.surface(verts, faces, opacity=0.96, vertex_colors=gl3d.colours(phase, table, -np.pi, np.pi),
                             name="enclosure")
                view.colour_bar(table, -np.pi, np.pi, "phase (rad)")
            else:
                view.surface(verts, faces, DEEPSKYBLUE, opacity=0.78, name="enclosure")
    else:
        field = np.real(psi) if mode == "Real(psi)" else np.imag(psi)
        magnitude = float(np.max(np.abs(field)))
        if magnitude > 1e-14:
            for sign, colour, name in ((1, POSITIVE, "positive lobes"), (-1, NEGATIVE, "negative lobes")):
                verts, faces = gl3d.contour(sign * field, 0.15 * magnitude, origin, step)
                view.surface(verts, faces, colour, opacity=0.72, name=name)
            part = "Re ψ" if mode == "Real(psi)" else "Im ψ"
            view.text(f"Red: {part} > 0 · blue: {part} < 0 (surfaces at ±15% of the largest |{part}|)")
        else:
            view.text("Imaginary component is zero for this state")
    view.axes()
    if show_grid:
        view.bounds((axis[0],) * 3, (axis[-1],) * 3, ('x (a_mu)', 'y (a_mu)', 'z (a_mu)'))
    # nucleus is symbolic (not displayed to atomic physical scale)
    verts, faces = gl3d.glyphs([(0, 0, 0)], "sphere", max(radius * .012, .05))
    view.surface(verts, faces, ORANGE, name="nucleus")
    set_camera_view(view, radius, camera_view, zoom)
    return drawn, radius


CAMERA_VIEWS = {"Perspective": "perspective", "+X": "+x", "+Y": "+y", "+Z": "+z"}


def set_camera_view(view, radius, camera_view="Perspective", zoom=1.0):
    """Stable orientation and magnification in unchanged Bohr-radius coordinates."""
    distance = max(1.0, 3.1 * radius) / max(0.5, min(float(zoom), 5.0))
    if CAMERA_VIEWS.get(camera_view, "perspective") == "perspective":
        distance *= float(np.sqrt(2 + .85 ** 2))         # the camera sits at (d, −d, 0.85 d), as it always has
    view.look(CAMERA_VIEWS.get(camera_view, "perspective"), distance, (0.0, 0.0, 0.0))
