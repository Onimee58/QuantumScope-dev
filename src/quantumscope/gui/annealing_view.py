"""The Quantum Annealing experiment (v0.9.2), in the Quantum Circuits area.

Choose a problem, then see why annealing works or fails: the spectrum of H(s) with its minimum gap,
the state during an anneal of time T, and the probability of success against T. "Open as circuit"
turns the anneal into gates (digitized annealing), whose structure is QAOA's. The physics is in
quantumscope.physics.annealing; everything slow runs in the background.
"""
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
                               QListWidget, QListWidgetItem, QPushButton, QSlider, QSpinBox, QTabWidget, QVBoxLayout,
                               QWidget)

from quantumscope.physics import annealing as A
from quantumscope.ml import feature_selection as F

TIMES = (0.5, 1, 2, 3, 5, 7, 10, 15, 20, 30, 50, 80)


def _short(name, width=14):
    return name if len(name) <= width else name[:width - 1] + '…'


def _time(T):
    return f'{T:,.0f}' if T >= 100 else f'{T:.1f}'


class AnnealingExperiment(QWidget):
    def __init__(self, parent=None, open_circuit=None, use_features=None):
        super().__init__(parent)
        from quantumscope.gui.qml_experiments import _plot, _scrolling
        self.open_circuit_in = open_circuit                    # open_circuit(n, gates, observable, note)
        self.use_features_in = use_features                    # use_features(task, names): to the Datasets tab
        self.problem = self.spectrum = self.result = None
        self.task = self.reads = self.rows = None              # feature selection (v0.9.13)
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
        self._feature_controls(f)
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
        from quantumscope.gui.side_panel import CollapsiblePanel
        root.addWidget(CollapsiblePanel(_scrolling(left, form), 'Problem and anneal', 'annealing'))
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
        self.tabs.addTab(self._features_page(_plot), 'Chosen features')
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
        features = key == 'features'
        for widget, shown in ((self.spins, key in ('glass', 'custom')), (self.seed, key == 'glass'),
                              (self.numbers, key == 'partition'), (self.text, key == 'custom'),
                              *((w, features) for w in self.feature_widgets)):
            widget.setEnabled(shown)
            self.problem_form.setRowVisible(widget, shown)            # only the options this problem uses
        self.tabs.setTabVisible(3, features)
        if features and self.task is None:
            self._load_data()

    def build_problem(self):
        key = self.problem_box.currentData()
        if key == 'features':
            return self._feature_problem()
        if key == 'partition':
            try:
                numbers = [float(v) for v in self.numbers.text().replace(',', ' ').split()]
            except ValueError:
                raise ValueError('Numbers: use positive numbers separated by commas, such as 4, 5, 6, 7, 8') from None
            if not 2 <= len(numbers) <= A.MAX_QUBITS or any(v <= 0 for v in numbers):
                raise ValueError(f'Numbers: give 2 to {A.MAX_QUBITS} positive numbers')
            return A.partition(numbers)
        return A.build(key, n=self.spins.value(), seed=self.seed.value(), text=self.text.text())

    # ---- feature selection (v0.9.13) ---------------------------------------------------------
    def _feature_controls(self, f):
        """The Feature selection problem's options, in the Problem box (hidden for other problems)."""
        from quantumscope.ml import datasets as D
        self.data_box = QComboBox()
        self.data_box.addItem('From the Datasets tab', 'store')
        for key, (title, *_rest) in D.BUILTIN.items():
            self.data_box.addItem(title, key)
        self.data_box.setCurrentIndex(self.data_box.findData('breast_cancer'))
        self.data_box.setToolTip('The data to choose features from. From the Datasets tab: as prepared there (your '
                                 'own CSV too); a dataset here: with the checker\'s suggestions')
        f.addRow('Data', self.data_box)
        self.keep = QSpinBox()
        self.keep.setRange(1, F.MAX_CANDIDATES - 1)
        self.keep.setValue(3)
        self.keep.setToolTip('How many features to keep: one per qubit in the classifiers')
        f.addRow('Keep (features)', self.keep)
        self.alpha = QDoubleSpinBox()
        self.alpha.setRange(0.0, 1.0)
        self.alpha.setSingleStep(0.05)
        self.alpha.setValue(F.ALPHA)
        self.alpha.setToolTip('α: how much relevance counts against redundancy. 1 ignores redundancy (the k most '
                              'relevant features); lower values avoid features that repeat each other')
        f.addRow('Relevance weight α', self.alpha)
        self.candidates = QListWidget()
        self.candidates.setMinimumHeight(150)
        self.candidates.setToolTip(f'The candidates, one spin each (at most {F.MAX_CANDIDATES}), sorted by relevance: '
                                   f'how well each feature alone separates the classes')
        f.addRow('Candidates', self.candidates)
        self.reads_box = QSpinBox()
        self.reads_box.setRange(1, 10000)
        self.reads_box.setValue(100)
        self.reads_box.setToolTip('How many times to run the anneal and measure, keeping the best choice seen: '
                                  'how annealers are used')
        f.addRow('Reads', self.reads_box)
        self.feature_note = QLabel()
        self.feature_note.setWordWrap(True)
        self.feature_note.setObjectName('muted')
        f.addRow(self.feature_note)
        self.feature_widgets = (self.data_box, self.keep, self.alpha, self.candidates, self.reads_box, self.feature_note)
        self.data_box.currentIndexChanged.connect(self._load_data)
        self.candidates.itemChanged.connect(self._candidate_ticked)

    def _features_page(self, _plot):
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(0, 0, 0, 0)
        row = QHBoxLayout()
        self.relevance_plot = _plot('Relevance', 'relevance', '')
        row.addWidget(self.relevance_plot, 1)
        self.redundancy_plot = _plot('Redundancy')
        row.addWidget(self.redundancy_plot, 1)
        v.addLayout(row, 3)
        self.comparison = QLabel('Anneal a feature selection to compare the choices.')
        self.comparison.setWordWrap(True)
        self.comparison.setTextFormat(Qt.TextFormat.RichText)
        v.addWidget(self.comparison, 2)
        self.use_button = QPushButton('Use these features in the Datasets tab')
        self.use_button.setToolTip('Prepare the data with the chosen features, for both classifiers')
        self.use_button.setEnabled(False)
        self.use_button.clicked.connect(lambda: self.use_features())
        v.addWidget(self.use_button)
        return page

    def _load_data(self, *_):
        """Build the feature-selection task for the chosen data (cleaned and split; nothing annealed yet)."""
        from quantumscope.ml import datasets as D
        key = self.data_box.currentData()
        try:
            if key == 'store':
                from quantumscope.gui.qml_experiments import STORE
                if STORE.dataset is None:
                    raise ValueError('Nothing prepared yet: open the Datasets experiment (Quantum ML) and press '
                                     'Prepare, or choose a dataset here')
                dataset, recipe = STORE.dataset, STORE.recipe
                title = getattr(dataset, 'name', '') or 'the Datasets tab\'s data'
                source = 'store'
            else:
                dataset = D.load(key)
                verdict, _, recipe = D.check(dataset, qubits=self.keep.value())
                if verdict == 'stop':
                    raise ValueError('This dataset cannot be used')
                title, source = D.BUILTIN[key][0], key
            task = F.make_task(dataset, recipe, source, title, k=self.keep.value(), alpha=self.alpha.value())
        except ValueError as exc:
            self.task = None
            self.candidates.clear()
            self.feature_note.setText(str(exc))
            return None
        return self.load_task(task, select_problem=False)

    def load_task(self, task, select_problem=True):
        """Show a feature-selection task (also from the Datasets tab's "Choose by annealing")."""
        self.task = task
        if select_problem:
            self.problem_box.setCurrentIndex(self.problem_box.findData('features'))
            if task.source == 'datasets':
                self.data_box.blockSignals(True)
                self.data_box.setCurrentIndex(self.data_box.findData('store'))
                self.data_box.blockSignals(False)
            self.keep.setValue(task.k)
        self.candidates.blockSignals(True)
        self.candidates.clear()
        order = np.argsort(-task.relevance, kind='stable')
        for i in order:
            item = QListWidgetItem(f'{task.names[i]}  ·  {task.relevance[i]:.2f}')
            item.setData(Qt.ItemDataRole.UserRole, int(i))
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if i in task.candidates else Qt.CheckState.Unchecked)
            self.candidates.addItem(item)
        self.candidates.blockSignals(False)
        self._describe_task()
        return task

    def _ticked(self):
        return sorted(int(self.candidates.item(r).data(Qt.ItemDataRole.UserRole)) for r in range(self.candidates.count())
                      if self.candidates.item(r).checkState() == Qt.CheckState.Checked)

    def _candidate_ticked(self, item):
        if len(self._ticked()) > F.MAX_CANDIDATES and item.checkState() == Qt.CheckState.Checked:
            self.candidates.blockSignals(True)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.candidates.blockSignals(False)
            self.feature_note.setText(f'At most {F.MAX_CANDIDATES} candidates: one spin each, and the simulation '
                                      f'has {F.MAX_CANDIDATES}. Untick one first.')
            return
        if self.task is not None:
            self.task.candidates = self._ticked()
            self._describe_task()

    def set_candidates(self, names):
        """Tick exactly these features (by name) as the candidates."""
        self.candidates.blockSignals(True)
        for r in range(self.candidates.count()):
            item = self.candidates.item(r)
            name = self.task.names[int(item.data(Qt.ItemDataRole.UserRole))]
            item.setCheckState(Qt.CheckState.Checked if name in names else Qt.CheckState.Unchecked)
        self.candidates.blockSignals(False)
        self.task.candidates = self._ticked()
        self._describe_task()

    def _describe_task(self):
        t = self.task
        p = t.prepared
        many = len(t.names) > len(t.candidates)
        self.feature_note.setText(
            f'{t.title}: {len(t.names)} features, {len(p.y_train)} training and {len(p.y_test)} test samples '
            f'({", ".join(p.classes)}). Relevance and redundancy come from the training samples only.'
            + (f' The anneal chooses among the {len(t.candidates)} ticked candidates, not all {len(t.names)}.'
               if many else ''))

    def _feature_problem(self):
        if self.task is None:
            self._load_data()
        if self.task is None:
            raise ValueError(self.feature_note.text() or 'Choose the data first')
        self.task.k, self.task.alpha = self.keep.value(), self.alpha.value()
        self.task.candidates = self._ticked()
        return F.problem(self.task)

    def _show_features(self):
        """The Chosen features tab: what was kept, why, and how the choice compares."""
        import pyqtgraph as pg
        reads, task = self.reads, self.problem.task
        c = task.candidates
        names = [task.names[i] for i in c]
        kept = set(F.subset(reads.best)) if reads.best else set()
        greedy = set(F.greedy(task))
        n = len(c)
        plot = self.relevance_plot                              # horizontal bars: the names stay readable
        plot.clear()
        rel = task.relevance[c]
        rows = n - 1 - np.arange(n)                             # the first candidate at the top
        plot.addItem(pg.BarGraphItem(x0=np.zeros(n), y=rows, width=rel, height=0.7,
                                     brushes=['#5ad48a' if i in kept else '#4a5a70' for i in range(n)],
                                     pens=[pg.mkPen('#ff9a5a', width=2) if i in greedy else pg.mkPen('#1a2533')
                                           for i in range(n)]))
        plot.getAxis('left').setTicks([[(int(rows[i]), f'{i + 1}  {_short(name, 22)}') for i, name in enumerate(names)]])
        plot.setXRange(0, 1.0)
        plot.setYRange(-0.6, n - 0.4)
        plot.setTitle('Relevance · green: kept · orange: best alone')
        R = F.redundancy(task.prepared.X_train[:, c])
        view = self.redundancy_plot
        view.clear()
        image = pg.ImageItem(R.T[:, ::-1])                       # ImageItem is [x, y]: candidate 0 at the top
        image.setLookupTable(pg.colormap.get('viridis').getLookupTable(0.0, 1.0, 256))
        image.setLevels((0, 1))
        view.addItem(image)
        view.getAxis('bottom').setTicks([[(i + 0.5, str(i + 1)) for i in range(n)]])
        view.getAxis('left').setTicks([[(n - 1 - i + 0.5, str(i + 1)) for i in range(n)]])
        box = view.getViewBox()
        box.setAspectLocked(False)
        box.setRange(xRange=(0, n), yRange=(0, n), padding=0.02)
        view.setTitle('Redundancy |corr| · yellow: repeats')
        lines = [f'<b>{reads.shots} reads</b> of the anneal (T = {self.result.T:g}): {reads.valid} kept exactly '
                 f'{task.k} features; {reads.hits} gave the best choice.']
        if reads.best:
            place = 'the best of all' if reads.rank == 1 else f'number {reads.rank} (by energy) of all'
            lines.append(f'The best read keeps <b>{", ".join(names[i] for i in sorted(kept))}</b>: {place} '
                         f'{reads.choices} ways to keep {task.k} of {len(c)}.')
        else:
            lines.append(f'No read kept exactly {task.k} features: anneal more slowly, or read more often.')
        if self.rows:
            table = ['<table cellspacing="0" cellpadding="3"><tr><th align="left">Choice</th><th align="left">'
                     'Features</th><th>Test accuracy</th><th>Mean redundancy</th></tr>']
            for row in self.rows:
                mean_r = '' if np.isnan(row.redundancy) else f'{row.redundancy:.2f}'
                shown = ', '.join(row.features) if len(row.features) <= 4 else f'{len(row.features)} features'
                table.append(f'<tr><td>{row.method}</td><td>{shown}</td><td align="center">{row.accuracy:.1%}</td>'
                             f'<td align="center">{mean_r}</td></tr>')
            table.append('</table>')
            lines.append(''.join(table))
            lines.append('<i>Scored with a classical Gaussian-kernel classifier on the test samples, which the choice '
                         'never saw. The energy stands in for accuracy, so the lowest energy is not always the most '
                         'accurate; PCA mixes every feature into unnamed components.</i>')
        self.comparison.setText('<br>'.join(lines))
        self.use_button.setEnabled(bool(reads.best))
        self.result_label.setText(self.result_label.text() + '<br>' + lines[0] + ' ' + (lines[1] if reads.best else ''))
        from quantumscope.learn import progress as learn_progress
        accuracy = {row.method: row.accuracy for row in (self.rows or [])}
        learn_progress.record('features', dataset=task.source, k=task.k, alpha=round(task.alpha, 4), candidates=len(c),
                              T=self.result.T, reads=reads.shots, valid=reads.valid, hits=reads.hits, rank=reads.rank,
                              chosen='+'.join(names[i] for i in sorted(kept)),
                              annealed=accuracy.get('Annealed', 0.0),
                              greedy=accuracy.get('Most relevant alone (greedy)', 0.0))

    def chosen_names(self):
        if not self.reads or not self.reads.best:
            return []
        task = self.problem.task
        return [task.names[task.candidates[i]] for i in F.subset(self.reads.best)]

    def use_features(self):
        """Send the best read's features to the Datasets tab; returns them."""
        names = self.chosen_names()
        if names and self.use_features_in is not None:
            self.use_features_in(self.problem.task, names)
        return names

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

        shots = self.reads_box.value()

        def work(report, cancelled):
            spectrum = A.spectrum(problem, points=81)
            result = A.anneal(problem, T, cancelled=cancelled)
            if result is None or getattr(problem, 'task', None) is None:
                return problem, spectrum, result
            reads = F.read_out(problem, result.probabilities[-1], shots)       # sampled as a real annealer is
            rows = F.compare(problem.task, F.subset(reads.best)) if reads.best else None
            return problem, spectrum, result, reads, rows
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
        self.problem, self.spectrum, self.result = outcome[:3]
        p, sp, r = outcome[:3]
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
        if len(outcome) > 3:
            self.reads, self.rows = outcome[3], outcome[4]
            self._show_features()

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
