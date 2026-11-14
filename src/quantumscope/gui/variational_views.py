"""Optimizer views: live convergence and energy landscapes (both use editor/variational.py)."""
import math

import numpy as np
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPen
from PySide6.QtWidgets import (QApplication, QComboBox, QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout,
                               QWidget)

from quantumscope.editor import variational as V
from quantumscope.gui.theme import canvas_color

METHODS = (('BFGS (quasi-Newton, gradients)', 'BFGS'), ('Gradient descent', 'gradient'),
           ('Adam (momentum, adaptive steps)', 'Adam'), ('SPSA (2 runs per step)', 'SPSA'),
           ('Rotosolve (exact minimum per parameter)', 'Rotosolve'), ('Quantum natural gradient', 'QNG'),
           ('Simulated annealing', 'annealing'), ('COBYLA (no gradients)', 'COBYLA'),
           ('Nelder–Mead (no gradients)', 'Nelder-Mead'))
METHOD_TIPS = {
    'BFGS': 'Builds up curvature from gradients: very fast with exact energies, but noise confuses it.',
    'gradient': 'Steps downhill along the gradient. Simple; it can crawl across flat regions.',
    'Adam': 'Gradient steps with momentum and a step size per parameter, as in deep learning.',
    'SPSA': 'Moves all parameters at once along a random direction: two circuit runs per step, however many '
            'parameters. The usual choice on real hardware.',
    'Rotosolve': 'Sets one parameter at a time to its exact minimum: the energy is a sinusoid in each angle, '
                 'fixed by three values. No learning rate.',
    'QNG': 'The quantum natural gradient: follows the geometry of the quantum state (the Fubini–Study metric), '
           'so every step changes the state by a similar amount.',
    'annealing': 'Random moves; uphill moves are sometimes accepted, less often as a temperature falls. Can escape '
                 'local minima; slow.',
    'COBYLA': 'Builds linear models from energies alone; no gradients.',
    'Nelder-Mead': 'Moves a simplex of points; no gradients. Noise misleads it badly.'}
SHOTS = (('Exact', 0), ('100 shots', 100), ('1,000 shots', 1000), ('10,000 shots', 10000))


class ConvergenceChart(QWidget):
    """⟨H⟩ against iteration, with the exact minimum as a dashed line."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(560, 300)
        self.energies, self.exact, self.measured = [], None, None

    def set_data(self, energies, exact=None, measured=None):
        """energies: the curve to draw; measured: the noisy values the optimizer saw (with shots),
        drawn thin behind the true curve."""
        self.energies, self.exact = list(energies), exact
        self.measured = list(measured) if measured is not None else None
        self.update()

    def paintEvent(self, event):
        if not self.energies:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        left, top, right, bottom = 70, 16, self.width() - 16, self.height() - 40
        values = self.energies + ([self.exact] if self.exact is not None else []) + (self.measured or [])
        lo, hi = min(values), max(values)
        # Never zoom into rounding noise: show at least 1% of the energy scale (or 0.01).
        least = max(0.01, 0.01 * max(abs(lo), abs(hi)))
        if hi - lo < least:
            middle = (hi + lo) / 2
            lo, hi = middle - least / 2, middle + least / 2
        pad = 0.06 * (hi - lo)
        lo, hi = lo - pad, hi + pad
        digits = min(8, max(3, 2 - int(math.floor(math.log10(hi - lo)))))   # enough decimals to tell ticks apart
        count = max(1, len(self.energies) - 1)
        x = lambda i: left + (right - left) * i / count
        y = lambda e: bottom - (bottom - top) * (e - lo) / (hi - lo)
        text = canvas_color('chart_text')
        p.setPen(QPen(canvas_color('bloch_axis'), 1))
        p.drawLine(QPointF(left, bottom), QPointF(right, bottom))
        p.drawLine(QPointF(left, top), QPointF(left, bottom))
        p.setPen(text)
        p.setFont(QFont('Sans', 8))
        for k in range(5):
            e = lo + (hi - lo) * k / 4
            p.drawText(QRectF(2, y(e) - 7, left - 8, 14), Qt.AlignmentFlag.AlignRight, f'{e:.{digits}f}')
        p.drawText(QRectF(left, bottom + 6, right - left, 14), Qt.AlignmentFlag.AlignCenter,
                   'no steps taken' if len(self.energies) == 1 else f'step (0 … {len(self.energies) - 1})')
        if self.exact is not None:
            p.setPen(QPen(canvas_color('chart_sampled'), 1.6, Qt.PenStyle.DashLine))
            p.drawLine(QPointF(left, y(self.exact)), QPointF(right, y(self.exact)))
            p.setPen(text)
            p.drawText(QPointF(right - 190, y(self.exact) - 5), f'exact minimum {self.exact:.6f}')
        p.setPen(QPen(canvas_color('bloch_vector'), 2.4))
        if len(self.energies) == 1:                              # no step: a level line, not a lone dot
            level = y(self.energies[0])
            p.drawLine(QPointF(left, level), QPointF(right, level))
            p.setBrush(canvas_color('bloch_vector'))
            p.drawEllipse(QPointF(left, level), 4, 4)
            p.setPen(text)
            p.drawText(QRectF(left + 10, level - 22, right - left - 20, 16), Qt.AlignmentFlag.AlignLeft,
                       f'no step lowered ⟨H⟩ below {self.energies[0]:.6f}')
            p.end()
            return
        if self.measured:                                        # what the optimizer saw: thin and noisy
            noisy = QColor(canvas_color('chart_sampled'))
            noisy.setAlphaF(0.75)
            p.setPen(QPen(noisy, 1.0))
            seen = [QPointF(x(i), y(e)) for i, e in enumerate(self.measured)]
            for a, b in zip(seen, seen[1:]):
                p.drawLine(a, b)
            p.setPen(text)
            p.drawText(QPointF(left + 8, top + 12), 'thin: ⟨H⟩ measured with shots · bold: true ⟨H⟩')
            p.setPen(QPen(canvas_color('bloch_vector'), 2.4))
        points = [QPointF(x(i), y(e)) for i, e in enumerate(self.energies)]
        for a, b in zip(points, points[1:]):
            p.drawLine(a, b)
        p.setBrush(canvas_color('bloch_vector'))
        p.drawEllipse(points[-1], 4, 4)
        p.end()


class OptimizeDialog(QDialog):
    """Runs the optimizer on the workspace's circuit with live progress; one undo step in total."""

    def __init__(self, workspace, method='BFGS', steps=200):
        super().__init__(workspace)
        self.setWindowTitle('Optimize parameters')
        self.workspace, self.method, self.steps = workspace, method, steps
        self.history, self.stopped = [], False
        layout = QVBoxLayout(self)
        self.summary = QLabel()
        self.summary.setWordWrap(True)
        self.summary.setMinimumHeight(3 * self.summary.fontMetrics().lineSpacing() + 4)   # wrapped text never clipped
        self.summary.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.summary)
        self.chart = ConvergenceChart()
        layout.addWidget(self.chart, 1)
        buttons = QHBoxLayout()
        self.stop_button = QPushButton('Stop')
        self.stop_button.clicked.connect(self._stop)
        self.close_button = QPushButton('Close')
        self.close_button.clicked.connect(self.accept)
        buttons.addStretch()
        buttons.addWidget(self.stop_button)
        buttons.addWidget(self.close_button)
        layout.addLayout(buttons)
        self.resize(720, 460)

    def _stop(self):
        self.stopped = True
        if getattr(self, 'run_handle', None) is not None:
            self.run_handle.cancel()

    def configure(self, method, steps, starts=1, shots=0):
        """Reuse this window for a new run (the panel's current method, step limit, starts and shots)."""
        self.method, self.steps, self.starts, self.shots = method, steps, max(1, int(starts)), int(shots)
        self.history, self.stopped = [], False
        self.stop_button.setEnabled(True)
        self.chart.set_data([], None)
        self.summary.setText('Optimizing…')

    def start(self, on_finished=None):
        """Optimize in the background, on a copy of the circuit; returns the run. The result is applied
        to the circuit when the run finishes, as one undo step, unless the circuit changed meanwhile."""
        import copy
        from quantumscope.gui.background import Run
        if getattr(self, 'run_handle', None) is not None and self.run_handle.running():
            return self.run_handle
        workspace = self.workspace
        model = copy.deepcopy(workspace.model)                  # the worker's own circuit
        key = workspace._path_key()
        method, steps, starts, shots = self.method, self.steps, getattr(self, 'starts', 1), getattr(self, 'shots', 0)

        def work(report, cancelled):                            # the worker: no widgets here
            exact = V.Evaluator(model).exact_minimum()
            report(('exact', exact))
            energies = []

            def progress(iteration, values, energy):
                if energies and iteration == len(energies) - 1:   # a heartbeat, not a new step
                    return not cancelled()
                energies.append(energy)
                report(('step', iteration, energy))
                return not cancelled()
            if starts > 1:
                def begin(k, total):
                    energies.clear()
                    report(('start', k, total))
                history, best_index, finals = V.best_of(model, starts, method, steps, callback=progress,
                                                        on_start=begin, shots=shots)
                history.evaluations = getattr(history, 'evaluations', 0)
            else:
                history, best_index, finals = V.optimize(model, method, steps, callback=progress, shots=shots), 0, []
            return dict(history=history, best_index=best_index, finals=finals, exact=exact)

        self._exact, self._energies = None, []
        workspace.opt_button.setEnabled(False)
        self.run_handle = Run(work, owner=self, on_progress=self._progress,
                              on_done=lambda r: self._finish(r, key, on_finished),
                              on_error=self._failed).start()
        return self.run_handle

    def wait(self):
        """For scripts and tests: wait for the run and return the history."""
        if getattr(self, 'run_handle', None) is not None:
            self.run_handle.wait()
        return self.history

    def waited(self):
        """For scripts and tests: wait for the run and return this window (chainable)."""
        self.wait()
        return self

    def closeEvent(self, event):
        if getattr(self, 'run_handle', None) is not None:
            self.run_handle.cancel()                            # closing the window stops the optimizer
        super().closeEvent(event)

    def _progress(self, value):
        kind = value[0]
        if kind == 'exact':
            self._exact = value[1]
        elif kind == 'start':
            k, total = value[1], value[2]
            self._energies = []
            self.summary.setText(f'Start {k + 1} of {total}' + (' (your current parameters)' if k == 0 else
                                                                ' (random parameters)') + '…')
        else:
            iteration, energy = value[1], value[2]
            self._energies.append(energy)
            exact = self._exact
            self.chart.set_data(self._energies, exact)
            self.summary.setText(f'Iteration {iteration}: ⟨H⟩ = {energy:.6f}' +
                                 (f'   (exact minimum {exact:.6f})' if exact is not None else ''))

    def _failed(self, exc, details):
        self.workspace.opt_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.summary.setText(f'The optimization failed: {exc}')

    def _finish(self, r, key, on_finished):
        self.workspace.opt_button.setEnabled(True)
        self.stopped = self.stopped or self.run_handle.cancel_requested
        self.history, best_index, finals, exact = r['history'], r['best_index'], r['finals'], r['exact']
        model = self.workspace.model
        if self.workspace._path_key() != key:                   # the circuit was edited meanwhile
            self.stop_button.setEnabled(False)
            self.summary.setText('The circuit changed while optimizing, so the result was not applied. '
                                 'Press Optimize again to optimize the new circuit.')
            return
        values, energy = self.history[-1]
        shots = getattr(self, 'shots', 0)
        true = getattr(self.history, 'true', None)
        if shots and true:                                    # report the true result, not the last noisy one
            energy = true[-1]
        model.snapshot()                                      # the whole optimization is one undo step
        values = V.wrap_safely(model, values)                 # back into −π…π where that changes nothing
        for name, value in zip(list(model.parameters), values):
            model.parameters[name] = float(value)
        model._apply_bindings()
        self.workspace._changed()
        self.workspace._sync_parameter_values()
        if shots and true:
            self.chart.set_data(true, exact, measured=[e for _, e in self.history])
        else:
            self.chart.set_data([e for _, e in self.history], exact)
        gap = energy - exact if exact is not None else None
        start = true[0] if shots and true else self.history[0][1]
        steps = len(self.history) - 1
        evaluations = getattr(self.history, 'evaluations', 0)
        if finals:                                              # best of several starts
            ranked = ', '.join(f'{e:.4f}' for e in finals)
            gap_text = ('' if exact is None else ' — the ground state is reached.' if energy - exact < 1e-6 else
                        f' — {energy - exact:.4g} above the exact minimum over all states.')
            self.summary.setText(f'Best of {len(finals)} starts: start {best_index + 1} reached ⟨H⟩ = {energy:.6f}'
                                 + (f' (exact minimum {exact:.6f})' if exact is not None else '') + gap_text
                                 + f' Final values of the starts: {ranked}.')
        elif exact is not None and start - exact < 1e-6:
            self.summary.setText(f'⟨H⟩ = {start:.6f} was already at the exact minimum: nothing to improve.')
        elif steps == 0 and not self.stopped:
            self.summary.setText(
                f'No step lowered ⟨H⟩ = {start:.6f} ({evaluations} circuit evaluations): these parameters are '
                f'already at a minimum of what this circuit can do. The exact minimum over all states is '
                f'{exact:.6f}' + ('; this circuit may not be able to reach it (its layers or its structure, such '
                                  'as a symmetry, limit which states it makes), or this is a local minimum: try '
                                  'other starting values.' if exact is not None else '.'))
        else:
            verdict = ('' if gap is None else
                       f' — {gap:.4g} above the exact minimum (with shots, measurement noise limits how close an '
                       f'optimizer can get).' if shots else
                       ' — the ground state is reached.' if gap < 1e-6 else
                       f' — {gap:.4g} above the exact minimum over all states. This may be the best this circuit '
                       'can reach (its layers or its structure, such as a symmetry, limit which states it makes), '
                       'or a local minimum: try another method or other starting values.')
            evaluations = getattr(self.history, 'evaluations', 0)
            self.summary.setText(f'{"Stopped" if self.stopped else "Finished"} after {steps} '
                                 f'step{"" if steps == 1 else "s"} ({evaluations} circuit evaluations): '
                                 f'⟨H⟩ went from {start:.6f} to {energy:.6f}'
                                 + (f' (exact minimum {exact:.6f})' if exact is not None else '') + verdict
                                 + (f' {shots:,} shots per Pauli term: {getattr(self.history, "shots_used", 0):,} '
                                    f'measurements in total. The thin line is ⟨H⟩ measured with these shots; the bold '
                                    f'line is the true ⟨H⟩.' if shots else ''))
        self.stop_button.setEnabled(False)
        if on_finished is not None:
            on_finished(self.history)


def _colour(t):
    """Blue (low) → yellow (high) for t in [0, 1]."""
    stops = [(0, (40, 60, 160)), (0.5, (60, 190, 200)), (1, (250, 230, 90))]
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        if t <= b:
            f = (t - a) / (b - a)
            return QColor(*[round(x + (y - x) * f) for x, y in zip(ca, cb)])
    return QColor(*stops[-1][1])


class LandscapeView(QWidget):
    """A curve (one parameter) or a colour map (two), with the current point and optional path."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(560, 420)
        self.data, self.current, self.path, self.names = None, None, None, ('', '')

    def set_data(self, data, names, current, path=None):
        self.data, self.names, self.current, self.path = data, names, current, path
        self.update()

    def paintEvent(self, event):
        if self.data is None:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        left, top, right, bottom = 64, 16, self.width() - 100, self.height() - 44
        text = canvas_color('chart_text')
        span = math.pi
        sx = lambda v: left + (right - left) * (v + span) / (2 * span)
        p.setFont(QFont('Sans', 8))
        if len(self.data) == 2:                                   # a curve
            xs, energies = self.data
            lo, hi = float(energies.min()), float(energies.max())
            hi = hi if hi - lo > 1e-12 else lo + 1
            sy = lambda e: bottom - (bottom - top) * (e - lo) / (hi - lo)
            p.setPen(QPen(canvas_color('bloch_vector'), 2.2))
            pts = [QPointF(sx(a), sy(b)) for a, b in zip(xs, energies)]
            for a, b in zip(pts, pts[1:]):
                p.drawLine(a, b)
            if self.current is not None:
                p.setBrush(canvas_color('chart_sampled'))
                p.setPen(Qt.PenStyle.NoPen)
                e = float(np.interp(self.current[0], xs, energies))
                p.drawEllipse(QPointF(sx(self.current[0]), sy(e)), 5, 5)
            p.setPen(text)
            for k in range(5):
                e = lo + (hi - lo) * k / 4
                p.drawText(QRectF(2, sy(e) - 7, left - 8, 14), Qt.AlignmentFlag.AlignRight, f'{e:.3f}')
        else:                                                     # a colour map
            xs, ys, grid = self.data
            lo, hi = float(grid.min()), float(grid.max())
            image = QImage(len(xs), len(ys), QImage.Format.Format_RGB32)
            for i in range(len(ys)):
                for j in range(len(xs)):
                    image.setPixelColor(j, len(ys) - 1 - i, _colour((grid[i, j] - lo) / (hi - lo + 1e-12)))
            p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)        # smooth, same values
            p.drawImage(QRectF(left, top, right - left, bottom - top), image)
            sy = lambda v: bottom - (bottom - top) * (v + span) / (2 * span)
            if self.path is not None and len(self.path) > 1:
                p.setPen(QPen(QColor('white'), 1.6))
                pts = [QPointF(sx(a), sy(b)) for a, b in self.path]
                for a, b in zip(pts, pts[1:]):
                    p.drawLine(a, b)
                p.setBrush(Qt.BrushStyle.NoBrush)                     # where the path started
                p.setPen(QPen(QColor('white'), 2))
                p.drawEllipse(pts[0], 6, 6)
            if self.current is not None:
                p.setPen(QPen(QColor('white'), 2))
                p.setBrush(QColor('#ff5a5a'))
                p.drawEllipse(QPointF(sx(self.current[0]), sy(self.current[1])), 5, 5)
            for k in range(40):                                   # colour scale, low at the bottom
                h = (bottom - top) / 40
                p.fillRect(QRectF(right + 12, bottom - (k + 1) * h, 14, h + 0.5), _colour((k + 0.5) / 40))
            p.setPen(text)
            p.drawText(QRectF(right + 30, top - 2, 66, 14), Qt.AlignmentFlag.AlignLeft, f'{hi:.3f}')
            p.drawText(QRectF(right + 30, bottom - 12, 66, 14), Qt.AlignmentFlag.AlignLeft, f'{lo:.3f}')
            p.drawText(QRectF(right + 30, (top + bottom) / 2 - 7, 66, 14), Qt.AlignmentFlag.AlignLeft, '⟨H⟩')
            for k, v in enumerate((-span, 0, span)):
                label = ('−π', '0', 'π')[k]
                p.drawText(QRectF(2, sy(v) - 7, left - 8, 14), Qt.AlignmentFlag.AlignRight, label)
            p.save()
            p.translate(14, (top + bottom) / 2)
            p.rotate(-90)
            p.drawText(QRectF(-60, -8, 120, 16), Qt.AlignmentFlag.AlignCenter, self.names[1])
            p.restore()
        p.setPen(text)
        for k, v in enumerate((-span, 0, span)):
            p.drawText(QRectF(sx(v) - 20, bottom + 4, 40, 14), Qt.AlignmentFlag.AlignCenter, ('−π', '0', 'π')[k])
        p.drawText(QRectF(left, bottom + 20, right - left, 16), Qt.AlignmentFlag.AlignCenter,
                   self.names[0] + ('   (⟨H⟩ along this parameter, others fixed)' if len(self.data) == 2 else ''))
        p.end()


class LandscapeDialog(QDialog):
    """⟨H⟩ over one or two chosen parameters, the others held at their current values."""

    def __init__(self, workspace, path=None):
        super().__init__(workspace)
        self.setWindowTitle('Energy landscape')
        self.workspace = workspace
        layout = QVBoxLayout(self)
        row = QHBoxLayout()
        self.first, self.second = QComboBox(), QComboBox()
        self.refresh_names()
        row.addWidget(QLabel('Horizontal'))
        row.addWidget(self.first)
        row.addWidget(QLabel('Vertical'))
        row.addWidget(self.second)
        draw = QPushButton('Draw')
        draw.clicked.connect(self.draw)
        row.addWidget(draw)
        row.addStretch()
        layout.addLayout(row)
        self.view = LandscapeView()
        layout.addWidget(self.view, 1)
        self.note = QLabel('Blue is low ⟨H⟩, yellow is high. The red dot is the current parameters; the white '
                           'line is the last optimization path, starting at the white ring. Other parameters are '
                           'held at their current values, so with more than two parameters the path is a projection.')
        self.note.setWordWrap(True)
        layout.addWidget(self.note)
        self.resize(720, 600)

    @property
    def path_history(self):
        """Always the workspace's latest optimization path, so Draw shows the current white line."""
        current = getattr(self.workspace, 'optimization_path', None)
        return current() if callable(current) else None

    def refresh_names(self):
        """Follow the circuit's parameters, keeping the chosen ones when they still exist."""
        names = list(self.workspace.model.parameters)
        first, second = self.first.currentText(), self.second.currentData()
        for box in (self.first, self.second):
            box.blockSignals(True)
            box.clear()
        self.first.addItems(names)
        self.second.addItem('— (one parameter: a curve)', None)
        for n in names:
            self.second.addItem(n, n)
        if first in names:
            self.first.setCurrentText(first)
        if second in names:
            self.second.setCurrentIndex(self.second.findData(second))
        elif len(names) > 1:
            self.second.setCurrentIndex(self.second.findData(names[1] if names[1] != self.first.currentText() else names[0]))
        for box in (self.first, self.second):
            box.blockSignals(False)

    def draw(self):
        """Compute the landscape in the background on a copy of the circuit; returns the run
        (run.wait() returns the data). Only the latest request is shown when several overlap."""
        import copy
        from quantumscope.gui.background import Run
        model = self.workspace.model
        if not model.parameters or not model.observable:
            return None
        if self.first.currentText() not in model.parameters:
            self.refresh_names()
        a, b = self.first.currentText(), self.second.currentData()
        if b == a:
            b = None
        snapshot = copy.deepcopy(model)
        names = list(model.parameters)
        current = (model.parameters[a], model.parameters[b] if b else 0.0)
        path = None
        if b and self.path_history:
            ia, ib = names.index(a), names.index(b)
            wrap = lambda v: (v + math.pi) % (2 * math.pi) - math.pi        # noqa: E731
            path = [(wrap(v[ia]), wrap(v[ib])) for v, _ in self.path_history]
        self._token = getattr(self, '_token', 0) + 1
        token = self._token
        previous = getattr(self, '_run', None)
        if previous is not None and previous.running():
            previous.cancel()                                    # a newer request replaces it
        self.setWindowTitle('Energy landscape — computing…')

        def done(data):
            if token != self._token:                              # an older request: ignore
                return
            self.setWindowTitle('Energy landscape')
            self.view.set_data(data, (a, b or ''), current, path)
        self._run = Run(lambda report, cancelled: V.landscape(snapshot, a, b, points=41 if b else 121),
                        owner=self, on_done=done).start()
        return self._run

    def waited(self):
        """For scripts and tests: wait for the latest landscape and return this window (chainable)."""
        if getattr(self, '_run', None) is not None:
            self._run.wait()
        return self
