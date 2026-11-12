"""The Quantum Annealing experiment (v0.9.2), in the Quantum Circuits area.

Choose a problem, then see why annealing works or fails: the spectrum of H(s) with its minimum gap,
the state during an anneal of time T, and the probability of success against T. "Open as circuit"
turns the anneal into gates (digitized annealing), whose structure is QAOA's. The physics is in
quantumscope.physics.annealing; everything slow runs in the background.
"""
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
                               QPushButton, QSlider, QSpinBox, QTabWidget, QVBoxLayout, QWidget)

from quantumscope.physics import annealing as A

TIMES = (0.5, 1, 2, 3, 5, 7, 10, 15, 20, 30, 50, 80)


def _time(T):
    return f'{T:,.0f}' if T >= 100 else f'{T:.1f}'


class AnnealingExperiment(QWidget):
    def __init__(self, parent=None, open_circuit=None):
        super().__init__(parent)
        from quantumscope.gui.qml_experiments import _plot, _scrolling
        self.open_circuit_in = open_circuit                    # open_circuit(n, gates, observable, note)
        self.problem = self.spectrum = self.result = None
        root = QHBoxLayout(self)
        left = QWidget()
        left.setMaximumWidth(392)
        form = QVBoxLayout(left)
        title = QLabel('<b>QUANTUM ANNEALING</b> · stay in the ground state while the problem is switched on')
        title.setWordWrap(True)
        form.addWidget(title)
        box = QGroupBox('Problem')
        f = self.problem_form = QFormLayout(box)
        self.problem_box = QComboBox()
        for label, key in A.PROBLEMS:
            self.problem_box.addItem(label, key)
        f.addRow('Problem', self.problem_box)
        self.spins = QSpinBox()
        self.spins.setRange(2, A.MAX_QUBITS)
        self.spins.setValue(6)
        f.addRow('Spins', self.spins)
        self.seed = QSpinBox()
        self.seed.setRange(0, 999)
        f.addRow('Instance', self.seed)
        self.numbers = QLineEdit('4, 5, 6, 7, 8')
        self.numbers.setToolTip('Positive numbers to split into two groups of equal sum (2 to 10 of them)')
        f.addRow('Numbers', self.numbers)
        self.text = QLineEdit('Z0 Z1 + Z1 Z2 - 0.5 Z0')
        self.text.setToolTip('A sum of Z terms, as in the observable field: each Z is a spin (+1 or −1)')
        f.addRow('Ising terms', self.text)
        self.answers = QLabel('')
        self.answers.setWordWrap(True)
        self.answers.setObjectName('muted')
        f.addRow(self.answers)
        form.addWidget(box)
        box = QGroupBox('Anneal')
        f = QFormLayout(box)
        self.T = QDoubleSpinBox()
        self.T.setRange(0.1, 200)
        self.T.setValue(10)
        self.T.setDecimals(1)
        self.T.setToolTip('The anneal time T (in units where ħ = 1): s = t/T goes from 0 to 1')
        f.addRow('Anneal time T', self.T)
        self.compute_button = QPushButton('Anneal')
        f.addRow(self.compute_button)
        self.curve_button = QPushButton('Success against T')
        self.curve_button.setToolTip(f'Anneal for T = {", ".join(f"{t:g}" for t in TIMES)} and plot how often the answer '
                                     f'is found')
        f.addRow(self.curve_button)
        row = QHBoxLayout()
        self.steps = QSpinBox()
        self.steps.setRange(1, 200)
        self.steps.setValue(20)
        self.steps.setToolTip('Trotter steps: slices of the anneal, each a problem layer and a driver layer')
        self.circuit_button = QPushButton('Open as circuit')
        self.circuit_button.setToolTip('The anneal as gates (digitized annealing), in the circuit simulator')
        row.addWidget(QLabel('Steps'))
        row.addWidget(self.steps)
        row.addWidget(self.circuit_button, 1)
        f.addRow(row)
        form.addWidget(box)
        self.result_label = QLabel('Choose a problem and press Anneal.')
        self.result_label.setWordWrap(True)
        form.addWidget(self.result_label)
        form.addStretch(1)
        root.addWidget(_scrolling(left, form))
        self.tabs = QTabWidget()
        self.spectrum_plot = _plot('Energy levels of H(s) = (1 − s)·H_driver + s·H_problem', 's', 'energy')
        self.tabs.addTab(self.spectrum_plot, 'Spectrum')
        during = QWidget()
        d = QVBoxLayout(during)
        d.setContentsMargins(0, 0, 0, 0)
        self.during_plot = _plot('During the anneal', 's', 'probability')
        self.during_plot.addLegend(offset=(10, -50))               # lower left, clear of both curves
        d.addWidget(self.during_plot, 3)
        row = QHBoxLayout()
        row.addWidget(QLabel('s'))
        self.s_slider = QSlider(Qt.Orientation.Horizontal)
        self.s_slider.setRange(0, 40)
        self.s_slider.setValue(40)
        row.addWidget(self.s_slider, 1)
        self.s_label = QLabel('1.00')
        row.addWidget(self.s_label)
        d.addLayout(row)
        self.bars = _plot('Bitstring probabilities at s', 'bitstring', 'probability')
        d.addWidget(self.bars, 2)
        self.tabs.addTab(during, 'During the anneal')
        self.curve_plot = _plot('Probability of finding the answer against the anneal time', 'T (log scale)',
                                'P(answer)')
        self.curve_plot.setLogMode(x=True, y=False)
        self.tabs.addTab(self.curve_plot, 'Success against T')
        root.addWidget(self.tabs, 1)
        self.problem_box.currentIndexChanged.connect(self._kind_changed)
        self.compute_button.clicked.connect(lambda: self.compute())
        self.curve_button.clicked.connect(lambda: self.success_curve())
        self.circuit_button.clicked.connect(lambda: self.open_circuit())
        self.s_slider.valueChanged.connect(self._draw_bars)
        self._kind_changed()

    # ---- the problem --------------------------------------------------------------------------
    def _kind_changed(self, *_):
        key = self.problem_box.currentData()
        for widget, shown in ((self.spins, key in ('glass', 'custom')), (self.seed, key == 'glass'),
                              (self.numbers, key == 'partition'), (self.text, key == 'custom')):
            widget.setEnabled(shown)
            self.problem_form.setRowVisible(widget, shown)            # only the options this problem uses

    def build_problem(self):
        key = self.problem_box.currentData()
        if key == 'partition':
            try:
                numbers = [float(v) for v in self.numbers.text().replace(',', ' ').split()]
            except ValueError:
                raise ValueError('Numbers: use positive numbers separated by commas, such as 4, 5, 6, 7, 8') from None
            if not 2 <= len(numbers) <= A.MAX_QUBITS or any(v <= 0 for v in numbers):
                raise ValueError(f'Numbers: give 2 to {A.MAX_QUBITS} positive numbers')
            return A.partition(numbers)
        return A.build(key, n=self.spins.value(), seed=self.seed.value(), text=self.text.text())

    # ---- computing ----------------------------------------------------------------------------
    def compute(self):
        """The spectrum and one anneal of time T, in the background; returns the run."""
        try:
            problem = self.build_problem()
        except ValueError as exc:
            self.result_label.setText(str(exc))
            return None
        T = self.T.value()
        from quantumscope.gui.background import Run

        def work(report, cancelled):
            spectrum = A.spectrum(problem, points=81)
            return problem, spectrum, A.anneal(problem, T, cancelled=cancelled)
        self.compute_button.setEnabled(False)
        self.result_label.setText('Computing the spectrum and the anneal…')
        self.run = Run(work, owner=self, on_done=self._computed, on_error=self._failed).start()
        return self.run

    def _failed(self, exc, details):
        self.compute_button.setEnabled(True)
        self.curve_button.setEnabled(True)
        self.result_label.setText(f'This could not be computed: {exc}')

    def _computed(self, outcome):
        self.compute_button.setEnabled(True)
        if outcome[2] is None:
            return
        self.problem, self.spectrum, self.result = outcome
        p, sp, r = outcome
        from quantumscope.physics import annealing_progress
        annealing_progress.annealed(p.key, r.T, r.final_success, sp.minimum_gap)
        answers = p.solutions()
        shown = ', '.join(answers[:6]) + (f' and {len(answers) - 6} more' if len(answers) > 6 else '')
        self.answers.setText(f'{p.n} spins. Answer{"s" if len(answers) > 1 else ""} (energy {p.ground_energy:g}): '
                             f'{shown}.')
        self.result_label.setText(
            f'<b>Minimum gap Δ = {sp.minimum_gap:.3g}</b> at s = {sp.minimum_at:.2f}; the adiabatic time scale is '
            f'about T* = {_time(sp.adiabatic_time)}.<br><b>With T = {r.T:g}: the answer is found with probability '
            f'{r.final_success:.1%}</b> (by guessing: {len(answers) / 2 ** p.n:.1%}).'
            + ('<br>Much slower than T* finds it almost surely; much faster, the state cannot follow.'
               if r.final_success < 0.95 else ''))
        self._draw_spectrum()
        self._draw_during()

    def success_curve(self):
        """P(answer) against T, in the background; returns the run."""
        try:
            problem = self.build_problem()
        except ValueError as exc:
            self.result_label.setText(str(exc))
            return None
        from quantumscope.gui.background import Run

        def work(report, cancelled):
            spectrum = A.spectrum(problem, points=61)
            curve = A.success_curve(problem, TIMES, cancelled=cancelled, progress=lambda d, t: report((d, t)))
            return None if curve is None else (problem, spectrum, curve)
        self.curve_button.setEnabled(False)
        self.tabs.setCurrentIndex(2)
        self.run = Run(work, owner=self, on_progress=lambda v: self.result_label.setText(
            f'Annealing for T = {TIMES[v[0] - 1]:g} ({v[0]} of {v[1]})…'),
            on_done=self._curve_done, on_error=self._failed).start()
        return self.run

    def _curve_done(self, outcome):
        import pyqtgraph as pg
        self.curve_button.setEnabled(True)
        if outcome is None:
            return
        problem, spectrum, curve = outcome
        self.last_curve = curve
        from quantumscope.physics import annealing_progress
        annealing_progress.curve(problem.key, spectrum.minimum_gap)
        plot = self.curve_plot
        plot.clear()
        plot.plot(list(TIMES), list(curve), pen=pg.mkPen('#5ae6ff', width=2), symbol='o', symbolSize=6,
                  symbolBrush='#5ae6ff')
        guess = len(problem.solutions()) / 2 ** problem.n
        plot.plot([TIMES[0], TIMES[-1]], [guess, guess], pen=pg.mkPen('#8fa3ba', style=Qt.PenStyle.DashLine))
        T_star = spectrum.adiabatic_time
        if TIMES[0] <= T_star <= TIMES[-1]:
            line = pg.InfiniteLine(pos=np.log10(T_star), angle=90, pen=pg.mkPen('#ff9a5a', width=1.5))
            plot.addItem(line)
        plot.setYRange(0, 1.02)
        where = 'orange line' if TIMES[0] <= T_star <= TIMES[-1] else 'beyond this chart'
        plot.setTitle(f'P(answer) against T · dashed: guessing ({guess:.1%}) · T* ≈ {_time(T_star)} ({where})')
        best = int(np.argmax(curve))
        text = (f'From T = {TIMES[0]:g} to {TIMES[-1]:g}, the probability of finding the answer goes from '
                f'{curve[0]:.1%} to {curve[-1]:.1%}')
        if best < len(curve) - 1 and curve[best] > curve[-1] + 0.02:
            text += (f', after peaking at {curve[best]:.1%} (T = {TIMES[best]:g}): a gap far too small to follow is '
                     f'jumped, and the outcome then depends on what happens elsewhere in the anneal')
        self.result_label.setText(text + f'. The adiabatic time scale is T* ≈ {_time(T_star)} (minimum gap '
                                         f'{spectrum.minimum_gap:.3g}).')

    # ---- drawing ------------------------------------------------------------------------------
    def _draw_spectrum(self):
        import pyqtgraph as pg
        sp, plot = self.spectrum, self.spectrum_plot
        plot.clear()
        for k in range(sp.levels.shape[1]):
            colour = '#5ae6ff' if k == 0 else '#ff9a5a' if k == sp.degeneracy else '#6b7a8f'
            plot.plot(sp.s, sp.levels[:, k], pen=pg.mkPen(colour, width=2.2 if k in (0, sp.degeneracy) else 1))
        x = sp.minimum_at
        lo = float(np.interp(x, sp.s, sp.levels[:, 0]))
        plot.plot([x, x], [lo, lo + sp.minimum_gap], pen=pg.mkPen('#ffffff', width=1.5, style=Qt.PenStyle.DashLine))
        plot.plot([x], [lo + sp.minimum_gap / 2], pen=None, symbol='o', symbolSize=14, symbolBrush=None,
                  symbolPen=pg.mkPen('#ffffff', width=1.5))                  # visible even when the gap is tiny
        note = (' (the symmetric levels: every spin flipped is the same answer)' if sp.symmetric else '')
        plot.setTitle(f'Energy levels of H(s){note} · cyan: ground state · orange: the first level that is not an '
                      f'answer · dashed: minimum gap {sp.minimum_gap:.3g}')

    def _draw_during(self):
        import pyqtgraph as pg
        r, plot = self.result, self.during_plot
        plot.clear()
        plot.plot(r.s, r.success, pen=pg.mkPen('#5ad48a', width=2), name='P(answer)')
        plot.plot(r.s, r.ground_overlap, pen=pg.mkPen('#5ae6ff', width=2, style=Qt.PenStyle.DashLine),
                  name='overlap with the ground state of H(s)')
        plot.setYRange(0, 1.02)
        self.s_slider.setRange(0, len(r.s) - 1)
        self.s_slider.setValue(len(r.s) - 1)
        self._draw_bars()

    def _draw_bars(self, *_):
        import pyqtgraph as pg
        r = self.result
        if r is None:
            return
        k = self.s_slider.value()
        self.s_label.setText(f'{r.s[k]:.2f}')
        probabilities = r.probabilities[k]
        n = self.problem.n
        answers = {int(b, 2) for b in self.problem.solutions()}
        order = np.argsort(probabilities)[::-1][:16]                # the 16 likeliest bitstrings
        plot = self.bars
        plot.clear()
        colours = ['#5ad48a' if int(x) in answers else '#5ae6ff' for x in order]
        plot.addItem(pg.BarGraphItem(x=np.arange(len(order)), height=probabilities[order], width=0.7,
                                     brushes=colours))
        plot.getAxis('bottom').setTicks([[(i, format(int(x), f'0{n}b')) for i, x in enumerate(order)]])
        plot.setYRange(0, 1.02)
        plot.setTitle(f'The likeliest bitstrings at s = {r.s[k]:.2f} · green: an answer')

    # ---- the anneal as a circuit ----------------------------------------------------------------
    def open_circuit(self):
        try:
            problem = self.build_problem()
        except ValueError as exc:
            self.result_label.setText(str(exc))
            return None
        steps, T = self.steps.value(), self.T.value()
        gates = A.circuit(problem, T, steps)
        if self.open_circuit_in is None:
            return gates
        note = (f'Digitized annealing: {steps} slices of an anneal of time {T:g}, each a problem layer (RZ and '
                f'CX–RZ–CX) and a driver layer (RX). ⟨O⟩ is the problem energy; measure to see the answers. More '
                f'steps follow the exact anneal more closely. QAOA (in Algorithms) has this structure with few '
                f'layers and free angles, tuned by Optimize.')
        self.open_circuit_in(problem.n, gates, problem.observable, note)
        return gates
