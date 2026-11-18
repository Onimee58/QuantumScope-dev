"""Animated, explicitly schematic view of the double-slit apparatus.

Geometry is drawn for explanation, not to scale. Curved wavefronts indicate
coherent phase fronts, not measured particle trajectories or a wave solver.
"""
import math

import numpy as np
from PySide6.QtCore import Qt, QTimer, QPointF, QRectF, Signal
from PySide6.QtGui import QColor, QFont, QFontMetricsF, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget


class DoubleSlitApparatus(QWidget):
    separationDragged = Signal(float)              # µm, while the slits are dragged (v0.7.4)
    """Responsive source -> slit barrier -> screen diagram with sample hits."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(390, 170)                     # v0.9.17: 220 → 170, for short screens
        self.setToolTip('Illustrative wavefronts only; probability and detections come from the Fraunhofer model.')
        self._phase = 0.0
        self._samples = np.empty(0)
        self._screen_halfwidth_mm = 40.0
        self._separation_um = 100.0
        self._width_um = 20.0
        self._colour = QColor(74, 180, 238)
        self.setMouseTracking(True)
        self.setToolTip('Drag the slits up or down to change their separation')
        self._animated = True
        self._which_path = False
        self._timer = QTimer(self)
        self._timer.setInterval(50)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def set_experiment(self, model, samples):
        self._screen_halfwidth_mm = model.screen_halfwidth_mm
        self._separation_um = model.slit_separation_um
        self._width_um = model.slit_width_um
        self._samples = np.asarray(samples, dtype=float).copy()
        self.update()

    # ---- dragging the slits changes their separation ------------------------------------------
    BARRIER, CENTRE = 315.0, 152.0

    def _scene(self, point):
        return point.x() * 700.0 / max(1, self.width()), point.y() * 300.0 / max(1, self.height())

    def mousePressEvent(self, event):
        x, _ = self._scene(event.position())
        self._dragging = abs(x - self.BARRIER) < 28
        if self._dragging:
            self.mouseMoveEvent(event)

    def mouseMoveEvent(self, event):
        x, y = self._scene(event.position())
        if not event.buttons():
            near = abs(x - self.BARRIER) < 28
            self.setCursor(Qt.CursorShape.SizeVerCursor if near else Qt.CursorShape.ArrowCursor)
            return
        if getattr(self, '_dragging', False):
            spacing = max(24.0, min(95.0, 2 * abs(y - self.CENTRE)))
            self.separationDragged.emit(round(spacing / 44.0 * 100.0 / 5) * 5)    # the inverse of the drawing rule

    def mouseReleaseEvent(self, event):
        self._dragging = False

    def set_colour(self, colour):
        """The light's colour for the drawn waves (set from the wavelength)."""
        self._colour = QColor(colour)
        self.update()

    def set_which_path(self, enabled):
        self._which_path = bool(enabled)
        self.update()

    def set_animated(self, enabled):
        self._animated = bool(enabled)
        if enabled and self.isVisible():
            self._timer.start()
        else:
            self._timer.stop()
        self.update()

    def showEvent(self, event):
        super().showEvent(event)
        if self._animated:
            self._timer.start()

    def hideEvent(self, event):
        self._timer.stop()
        super().hideEvent(event)

    def _tick(self):
        self._phase = (self._phase + 0.024) % 1.0
        self.update()

    def _dot(self, painter, centre, radius):
        """A round dot at a scene position, round however the drawing is stretched (v0.9.18)."""
        scale = min(self.width() / 700.0, self.height() / 300.0)
        point = painter.transform().map(centre)
        painter.save()
        painter.resetTransform()
        painter.drawEllipse(point, radius * scale, radius * scale)
        painter.restore()

    def _label(self, painter, rect, align, text, points, colour):
        """Text at the scene position `rect`, but drawn without the drawing's stretch (v0.9.18): the
        drawing fills the widget and so stretches with it, but letters must keep their shape. The size
        follows the smaller of the two stretches, so it grows on a big screen; long text is shrunk
        (down to 7 points), then shortened with …, to fit its place."""
        area = painter.transform().mapRect(rect)
        scale = min(self.width() / 700.0, self.height() / 300.0)
        font = QFont('Sans Serif')
        size = max(7.0, min(points * 1.6, points * scale))
        font.setPointSizeF(size)
        while size > 7.0 and QFontMetricsF(font).horizontalAdvance(text) > area.width():
            size = max(7.0, size - 0.5)
            font.setPointSizeF(size)
        text = QFontMetricsF(font).elidedText(text, Qt.TextElideMode.ElideRight, area.width())
        painter.save()
        painter.resetTransform()
        painter.setFont(font)
        painter.setPen(colour)
        painter.drawText(area, int(align), text)
        painter.restore()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor('#101923'))
        w, h = self.width(), self.height()
        # Scene coordinates in a consistent 700x300 rectangle.
        painter.translate(0, 0)
        painter.scale(w / 700.0, h / 300.0)
        painter.setPen(QPen(QColor('#34495e'), 1))
        painter.drawRoundedRect(QRectF(5, 5, 690, 290), 9, 9)
        sx, barrier, detector, cy = 70.0, 315.0, 640.0, 152.0
        painter.setPen(QPen(QColor('#638398'), 1, Qt.PenStyle.DashLine))
        painter.drawLine(QPointF(48, cy), QPointF(663, cy))
        # A stylized upstream plane wave, converging on the two apertures.
        for n in range(10):
            x = sx + ((n * 32 + self._phase * 32) % (barrier - sx - 15))
            painter.setPen(QPen(QColor(self._colour.red(), self._colour.green(), self._colour.blue(), 60 + int(80 * (x - sx) / (barrier - sx))), 1.7))
            painter.drawLine(QPointF(x, 54), QPointF(x, 249))
        painter.setPen(QPen(QColor('#d7e8f0'), 2))
        painter.setBrush(QColor('#54b8e7'))
        self._dot(painter, QPointF(sx, cy), 10)
        # Physical gap sizes are exaggerated to remain visible. They still track
        # the slit-width / separation ratio within safe visual bounds.
        gap = max(6., min(16., 12. * self._width_um / 20.))
        spacing = max(24., min(95., 44. * self._separation_um / 100.))
        slit_ys = (cy - spacing / 2., cy + spacing / 2.)
        boundaries = [30., slit_ys[0] - gap / 2., slit_ys[0] + gap / 2.,
                      slit_ys[1] - gap / 2., slit_ys[1] + gap / 2., 275.]
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor('#b8c9d3'))
        for a, b in ((0, 1), (2, 3), (4, 5)):
            painter.drawRoundedRect(QRectF(barrier - 5, boundaries[a], 10,
                                            boundaries[b] - boundaries[a]), 2, 2)
        # The markers represent an idealized path-distinguishing interaction
        # occurring at the apertures, not an upstream position measurement.
        if self._which_path:
            painter.setPen(QPen(QColor('#efaa55'), 2))
            painter.setBrush(QColor('#efaa55'))
            for slit_y in slit_ys:
                self._dot(painter, QPointF(barrier + 13, slit_y), 5)
            self._label(painter, QRectF(338, 35, 165, 24), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                        'PATH DETECTORS ON', 10, QColor('#efaa55'))
        # Two sets of expanding circular phase fronts from the apertures.
        # Clip the rings to the right side of the barrier and within the frame.
        painter.save()
        painter.setClipRect(QRectF(barrier + 7, 29, detector - barrier - 17, 246))
        for slit_y in slit_ys:
            for k in range(11):
                radius = 18 + (k + self._phase) * 35
                opacity = max(35, int(155 * (1 - radius / 550)))
                painter.setPen(QPen(QColor(self._colour.red(), self._colour.green(), self._colour.blue(), opacity), 1.7))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(QPointF(barrier, slit_y), radius, radius)
        painter.restore()
        # Detector with actual sampled screen positions; no trajectories.
        painter.setPen(QPen(QColor('#f1c36a'), 6))
        painter.drawLine(QPointF(detector, 32), QPointF(detector, 272))
        if self._samples.size:
            # Bound visual complexity, retaining a representative range of hits.
            indices = np.linspace(0, self._samples.size - 1,
                                  min(350, self._samples.size), dtype=int)
            values = self._samples[indices]
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(self._colour.red(), self._colour.green(), self._colour.blue(), 185))   # the light's colour
            for idx, value in enumerate(values):
                y = cy - (float(value) / self._screen_halfwidth_mm) * 113
                # Horizontal spread only distinguishes overlapping hits visually.
                x = detector - 3 - (idx % 5) * 3
                self._dot(painter, QPointF(x, y), 1.9)
        centre = Qt.AlignmentFlag.AlignCenter
        for rect, text in ((QRectF(27, 8, 105, 22), 'Source'), (QRectF(252, 8, 130, 22), 'Double slit'),
                           (QRectF(585, 8, 105, 22), 'Detector')):
            self._label(painter, rect, centre, text, 10, QColor('#e2edf3'))
        self._label(painter, QRectF(25, 274, 650, 20), centre,
                    'Schematic, not to scale | Path markers = ideal measurement; dots = detections' if self._which_path
                    else 'Schematic, not to scale | Rings = illustrative phase fronts; dots = detections',
                    9, QColor('#91a8b5'))
        painter.end()
