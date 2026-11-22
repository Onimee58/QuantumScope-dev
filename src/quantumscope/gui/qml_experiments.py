"""The Quantum ML area (v0.8.0): Datasets, Quantum Kernel Classifier and Variational Classifier.

The Datasets experiment checks and prepares data; what it prepares is shared with both classifiers
("From the Datasets tab"). Each classifier can also use any built-in or synthetic dataset directly,
prepared with the checker's suggested recipe. The physics and learning live in quantumscope.ml.
"""
import math

import numpy as np
from PySide6.QtCore import QObject, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QImage, QPainter
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog, QFormLayout,
                               QGroupBox, QHBoxLayout, QLabel, QMessageBox, QPushButton, QSpinBox, QVBoxLayout,
                               QWidget)

from quantumscope.ml import datasets as D
from quantumscope.ml import kernels as K
from quantumscope.ml import variational as V
from quantumscope.gui.plots import tidy

CLASS_COLOURS = ('#5ae6ff', '#ff9a5a')                     # +1, −1
# More classes (v0.9.3): labels 0 … k−1; the first two keep the two-class colours.
MANY_COLOURS = ('#5ae6ff', '#ff9a5a', '#5ad48a', '#d77aff', '#ffd75a', '#ffb3e6', '#7f8cff', '#b5e35a', '#e8eef5',
                '#c08a5a')
ALL = 'all'                                                # the class choice that keeps every class


def palette(k):
    """(label, colour) for every class: (+1, −1) for two classes, else 0 … k−1."""
    if k <= 2:
        return list(zip((1, -1), CLASS_COLOURS))
    return [(c, MANY_COLOURS[c % len(MANY_COLOURS)]) for c in range(k)]


def labels_and_colours(y):
    """palette() for labels whose number of classes is not otherwise known."""
    y = np.asarray(y)
    return palette(2 if np.all(np.isin(y, (-1, 1))) else int(np.max(y)) + 1)


class DataStore(QObject):
    """What the Datasets experiment prepared, shared with the classifiers."""
    changed = Signal()

    def __init__(self):
        super().__init__()
        self.dataset = self.recipe = self.prepared = None

    def publish(self, dataset, recipe, prepared):
        self.dataset, self.recipe, self.prepared = dataset, recipe, prepared
        self.changed.emit()


STORE = DataStore()


def _scrolling(panel, layout):
    """A left-hand control panel that scrolls instead of squashing: every control keeps its natural
    height, and a scrollbar appears when the window is too short (v0.8.2)."""
    from PySide6.QtWidgets import QFrame, QLayout, QScrollArea
    for box in panel.findChildren(QComboBox):                      # lists: a sensible width, not their longest entry
        box.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        box.setMinimumContentsLength(4 if box.property('pair') else 14)   # class pairs sit side by side
        box.currentTextChanged.connect(box.setToolTip)            # the full name on hover
        box.setToolTip(box.currentText())
    layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)   # never smaller than its contents
    area = QScrollArea()
    area.setWidget(panel)
    area.setWidgetResizable(True)
    area.setFrameShape(QFrame.Shape.NoFrame)
    area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    width = panel.maximumWidth()
    if width < 16777215:                                           # the column's width, plus the scrollbar's
        area.setFixedWidth(width + area.verticalScrollBar().sizeHint().width() + 2)
    return area


OWN_FILE = 'Your own file (CSV or .npz)…'


def _source_combo():
    box = QComboBox()
    for key, (title, *_rest) in D.BUILTIN.items():
        box.addItem(title, key)
    box.insertSeparator(box.count())
    for kind in D.SYNTHETIC:
        box.addItem(f'{kind.capitalize()} (synthetic, 2-D)', kind)
    return box


def _plot(title, x_label='', y_label=''):
    import pyqtgraph as pg
    plot = tidy(pg.PlotWidget())
    plot.setTitle(title)
    plot.setLabel('bottom', x_label)
    plot.setLabel('left', y_label)
    plot.showGrid(x=True, y=True, alpha=0.15)
    plot.setMinimumHeight(150)                                 # v0.9.17: 220 → 150, for short screens
    for side in ('left', 'bottom'):                            # plain numbers: no automatic "×0.001"
        plot.getAxis(side).enableAutoSIPrefix(False)
    from quantumscope.gui.pop_out import overlay                # v0.9.18: ⧉ opens it in its own window
    overlay(plot, title.split(' (')[0].split(':')[0])
    return plot


def _scatter_points(plot, X, y, size=8, symbol='o', outline=None, palette=None, names=None):
    """names: class names by position in the palette, for a legend (more than two classes)."""
    import pyqtgraph as pg
    for position, (label, colour) in enumerate(palette or labels_and_colours(y)):
        chosen = y == label
        if not chosen.any():
            continue
        plot.addItem(pg.ScatterPlotItem(X[chosen, 0], X[chosen, 1], size=size, symbol=symbol,
                                        brush=pg.mkBrush(colour), pen=pg.mkPen(outline or '#0b1420', width=1),
                                        name=None if names is None else str(names[position])))


class ImageStrip(QWidget):
    """A few example images per chosen class (Digits, MNIST)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(150)
        self.rows = []                                     # (class name, [images])

    def show_images(self, dataset, classes, per_row=10):
        self.rows = []
        if dataset is not None and dataset.image_shape:
            h, w = dataset.image_shape
            for c in classes:
                picks = np.flatnonzero(dataset.y == c)[:per_row]
                self.rows.append((dataset.classes[c], [dataset.X[i].reshape(h, w) for i in picks]))
        self.setVisible(bool(self.rows))
        self.update()

    def paintEvent(self, event):
        if not self.rows:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
        row_h = (self.height() - 8) / len(self.rows)
        font = QFont('Sans', 10 if len(self.rows) <= 4 else 9, QFont.Weight.Bold)
        p.setFont(font)
        labels = [f'class {name}' if str(name).isdigit() else str(name) for name, _ in self.rows]
        label_w = min(150, max(p.fontMetrics().horizontalAdvance(t) for t in labels) + 10)   # names fit
        size = min(row_h - 4, (self.width() - label_w - 6) / max(len(r[1]) for r in self.rows) - 4)
        p.setPen(self.palette().windowText().color())           # readable in both themes
        for r, (name, images) in enumerate(self.rows):
            y = 4 + r * row_h
            p.drawText(QRectF(0, y, label_w - 6, row_h), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                       labels[r])
            for k, image in enumerate(images):
                top = max(1e-9, float(image.max()))
                pixels = (255 * (image / top)).astype(np.uint8).copy()
                qimage = QImage(pixels.data, pixels.shape[1], pixels.shape[0], pixels.shape[1],
                                QImage.Format.Format_Grayscale8)
                p.drawImage(QRectF(label_w + k * (size + 4), y + (row_h - size) / 2, size, size), qimage)
        p.end()


class SampleView(QWidget):
    """What was clicked: one sample, or the two samples of a kernel-matrix cell (v0.8.2).
    Image datasets (Digits, MNIST) show the image; others list the first raw feature values."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(230)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        self.title = QLabel('Click a point (kernel map) or a cell (kernel matrix) to see the samples.')
        self.title.setWordWrap(True)
        self.title.setObjectName('muted')
        layout.addWidget(self.title)
        self.row = QHBoxLayout()
        layout.addLayout(self.row)
        layout.addStretch(1)
        self.entries = []

    def show_samples(self, entries, title=''):
        """entries: dicts with 'heading', 'lines' and optionally 'image' (a 2-D array)."""
        from PySide6.QtGui import QPixmap
        while self.row.count():
            item = self.row.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        self.entries = entries
        self.title.setText(title)
        for entry in entries:
            box = QVBoxLayout()
            holder = QWidget()
            holder.setLayout(box)
            heading = QLabel(f'<b>{entry["heading"]}</b>')
            heading.setWordWrap(True)
            box.addWidget(heading)
            image = entry.get('image')
            if image is not None:
                top = max(1e-9, float(np.max(image)))
                pixels = np.ascontiguousarray((255 * (np.asarray(image) / top)).astype(np.uint8))
                qimage = QImage(pixels.data, pixels.shape[1], pixels.shape[0], pixels.shape[1],
                                QImage.Format.Format_Grayscale8).copy()
                picture = QLabel()
                picture.setPixmap(QPixmap.fromImage(qimage).scaled(96, 96))
                box.addWidget(picture)
            text = QLabel('<br>'.join(entry['lines']))
            text.setWordWrap(True)
            box.addWidget(text)
            box.addStretch(1)
            self.row.addWidget(holder)


# ============================================================================================
class DatasetsExperiment(QWidget):
    """Choose or import data, see whether it fits a quantum model, and prepare it."""

    def __init__(self, parent=None, choose_features=None):
        super().__init__(parent)
        self.choose_features_in = choose_features          # choose_features(task): to Quantum annealing (v0.9.13)
        self.selection = None                              # features chosen by annealing: dict(names, signature)
        root = QHBoxLayout(self)
        left = QWidget()
        left.setMaximumWidth(420)
        form = QVBoxLayout(left)
        title = QLabel('DATASETS  ·  check and prepare data for a quantum classifier')
        title.setStyleSheet('font-weight:700;')
        title.setWordWrap(True)
        form.addWidget(title)
        source = QGroupBox('Data')
        sv = QFormLayout(source)
        self.source = _source_combo()
        self.source.insertItem(0, OWN_FILE, 'imported')     # v1.0.1: your own data is a choice in the list
        self.source.insertSeparator(1)
        self.source.setCurrentIndex(2)
        sv.addRow('Dataset', self.source)
        self.import_button = QPushButton('Choose the file…')
        self.import_button.setToolTip('Your own data: a .csv opens in a preview, where you choose the label '
                                      'column and the columns to use; a .npz needs arrays X and y. Choose '
                                      '"Your own file" in the list above to use it.')
        sv.addRow(self.import_button)
        self.imported, self._shown_source = None, 2
        self.qubits = QSpinBox()
        self.qubits.setRange(1, D.MAX_QUBITS)
        self.qubits.setValue(4)
        self.qubits.setToolTip('One feature per qubit: the checker suggests reducing the data to this many '
                               'features, and the prepared data has that many')
        sv.addRow('Qubits (= features)', self.qubits)
        form.addWidget(source)
        self.verdict = QLabel()
        self.verdict.setWordWrap(True)
        self.verdict.setStyleSheet('font-weight:700;')
        form.addWidget(self.verdict)
        self.findings = QLabel()
        self.findings.setWordWrap(True)
        self.findings.setTextFormat(Qt.TextFormat.RichText)
        form.addWidget(self.findings)
        recipe = QGroupBox('Preprocessing')
        rv = QFormLayout(recipe)
        self.class_a, self.class_b = QComboBox(), QComboBox()
        for box in (self.class_a, self.class_b):
            box.setProperty('pair', True)
        pair = QHBoxLayout()
        pair.addWidget(self.class_a)
        self.vs_label = QLabel('vs')
        pair.addWidget(self.vs_label)
        pair.addWidget(self.class_b)
        rv.addRow('Classes', pair)
        self.class_a.setToolTip('Two classes to separate, or All classes (one-vs-rest)')
        self.missing = QComboBox()
        for label, value in (('Keep', 'none'), ('Drop those samples', 'drop'), ('Fill with the mean', 'mean')):
            self.missing.addItem(label, value)
        rv.addRow('Missing values', self.missing)
        self.text = QComboBox()
        for label, value in (('Encode as numbers', 'encode'), ('Drop', 'drop')):
            self.text.addItem(label, value)
        rv.addRow('Text columns', self.text)
        self.per_class = QSpinBox()
        self.per_class.setRange(0, 5000)
        self.per_class.setSpecialValueText('all')
        rv.addRow('Samples per class', self.per_class)
        self.components = QSpinBox()
        self.components.setRange(0, D.MAX_QUBITS)
        self.components.setSpecialValueText('keep all')
        rv.addRow('PCA components', self.components)
        choose = QHBoxLayout()
        self.anneal_button = QPushButton('Choose by annealing…')
        self.anneal_button.setToolTip('Keep named features instead of PCA components: Quantum annealing chooses '
                                      'Qubits-many that predict the classes without repeating each other')
        self.clear_selection = QPushButton('Clear')
        self.clear_selection.setToolTip('Forget the chosen features (PCA again)')
        choose.addWidget(self.anneal_button, 1)
        choose.addWidget(self.clear_selection)
        rv.addRow('Or keep features', choose)
        self.selection_label = QLabel()
        self.selection_label.setWordWrap(True)
        self.selection_label.setObjectName('muted')
        rv.addRow(self.selection_label)
        self.scale = QCheckBox('Scale each feature to [0, π]')
        self.scale.setChecked(True)
        rv.addRow(self.scale)
        self.test_fraction = QDoubleSpinBox()
        self.test_fraction.setRange(0.1, 0.5)
        self.test_fraction.setSingleStep(0.05)
        self.test_fraction.setValue(0.25)
        rv.addRow('Test share', self.test_fraction)
        buttons = QHBoxLayout()
        self.suggest = QPushButton('Apply suggestions')
        self.prepare_button = QPushButton('Prepare')
        self.prepare_button.setToolTip('Prepare the data and share it with both classifiers')
        buttons.addWidget(self.suggest)
        buttons.addWidget(self.prepare_button)
        rv.addRow(buttons)
        form.addWidget(recipe)
        self.steps = QLabel()
        self.steps.setWordWrap(True)
        self.steps.setObjectName('muted')
        form.addWidget(self.steps)
        form.addStretch()
        from quantumscope.gui.side_panel import CollapsiblePanel
        root.addWidget(CollapsiblePanel(_scrolling(left, form), 'Data', 'qml-datasets'))
        right = QVBoxLayout()
        self.plot = _plot('Prepared training data (first two features)')
        right.addWidget(self.plot, 3)
        self.images = ImageStrip()
        right.addWidget(self.images, 2)
        root.addLayout(right, 1)
        self.dataset, self.recipe = None, None
        self.source.currentIndexChanged.connect(self._load_source)
        self.import_button.clicked.connect(self.import_file)
        self.qubits.valueChanged.connect(self._check)
        self.suggest.clicked.connect(self._check)
        self.class_a.currentIndexChanged.connect(self._class_mode_changed)
        self.prepare_button.clicked.connect(self.prepare)
        self.anneal_button.clicked.connect(lambda: self.choose_by_annealing())
        self.clear_selection.clicked.connect(self._clear_selection_and_prepare)
        self._show_selection()
        self._load_source()

    def _load_source(self, *_):
        key = self.source.currentData()
        self.import_button.setEnabled(key == 'imported')
        if key == 'imported':                               # your own file: the one chosen, or choose one
            if self.imported is not None:
                self.source_key = 'imported'
                self.use(self.imported)
                self._shown_source = self.source.currentIndex()
            elif self.import_file() is None:                  # cancelled: back to what is loaded
                self._show_source(self._shown_source)
            return
        self.source_key = key                                 # a built-in or synthetic key
        self.use(D.load(key))
        self._shown_source = self.source.currentIndex()

    def _show_source(self, index):
        """Select an entry of the list without loading it again."""
        self.source.blockSignals(True)
        self.source.setCurrentIndex(index)
        self.source.blockSignals(False)
        self.import_button.setEnabled(self.source.currentData() == 'imported')

    def _show_imported(self, dataset):
        """The list says which file is loaded (v1.0.1): 'Your file: plants.csv'."""
        self.imported = dataset
        index = self.source.findData('imported')
        self.source.setItemText(index, f'Your file: {dataset.name}' if dataset.name else OWN_FILE)
        self.source.setItemData(index, 'Your own data. Choose the file… to use another one',
                                Qt.ItemDataRole.ToolTipRole)
        self._show_source(index)
        self._shown_source = index

    def import_file(self, path=None, ask=None):
        """Import a .csv or .npz file. ask: show a .csv first, to choose its label column and the
        columns to use (v0.9.19); by default, when the file was chosen here (not given)."""
        if ask is None:
            ask = not path
        if not path:
            path, _ = QFileDialog.getOpenFileName(self, 'Import data', '', 'Data (*.csv *.npz *.txt)')
            if not path:
                return None
        try:
            if ask and path.lower().endswith(('.csv', '.txt')):
                from quantumscope.gui.import_dialog import ImportDialog
                dialog = ImportDialog(path, self)
                if not dialog.exec():
                    return None
                dataset = dialog.dataset
            else:
                dataset = D.import_file(path)
        except (OSError, ValueError, UnicodeDecodeError) as exc:
            QMessageBox.warning(self, 'Import data', f'This file could not be read:\n{exc}')
            return None
        self.source_key = 'imported'
        self._show_imported(dataset)
        self.use(dataset)
        return dataset

    def use(self, dataset):
        self.dataset = dataset
        for box in (self.class_a, self.class_b):
            box.blockSignals(True)
            box.clear()
            if box is self.class_a and len(dataset.classes) > 2:
                box.addItem(f'All {len(dataset.classes)} classes', ALL)
            for k, name in enumerate(dataset.classes):
                box.addItem(f'{name} ({int(dataset.counts[k])})', k)
            box.setCurrentIndex(box.findData(0))                  # a pair first; All classes on request
            box.blockSignals(False)
        self._check()

    def all_classes(self):
        """True when every class is to be separated at once (v0.9.3)."""
        return self.class_a.currentData() == ALL

    def _class_mode_changed(self, *_):
        """Switching between a pair and All classes: the checker's suggestions change with it."""
        self.vs_label.setVisible(not self.all_classes())
        self.class_b.setVisible(not self.all_classes())
        if self.all_classes() or getattr(self, '_was_all', False):
            self._check()
        self._was_all = self.all_classes()

    def _check(self, *_):
        """Run the checker and fill in its suggested recipe."""
        self.selection = None                                  # suggestions replace chosen features too
        self._show_selection()
        everything = self.all_classes()
        verdict, findings, recipe = D.check(self.dataset, qubits=self.qubits.value(),
                                            max_classes=None if everything else 2)
        self.recipe = recipe
        self._show_findings(verdict, findings)
        if not everything:
            for box, value in ((self.class_a, recipe.classes[0]), (self.class_b, recipe.classes[1])):
                box.blockSignals(True)
                box.setCurrentIndex(box.findData(value))
                box.blockSignals(False)
        self._was_all = everything
        self.vs_label.setVisible(not everything)
        self.class_b.setVisible(not everything)
        self.missing.setCurrentIndex(self.missing.findData(recipe.missing))
        self.text.setCurrentIndex(self.text.findData(recipe.text))
        self.per_class.setValue(recipe.per_class)
        self.components.setValue(recipe.components)
        self.prepare_button.setEnabled(verdict != 'stop')
        self.images.show_images(self.dataset, recipe.classes)
        if verdict != 'stop':
            self.prepare()

    def _show_findings(self, verdict, findings):
        colour = {'ready': '#5ad48a', 'preprocess': '#ffba50', 'stop': '#ff7a7a'}[verdict]
        text = {'ready': 'Ready: this data fits as it is.', 'preprocess': 'Usable after preprocessing (suggested below).',
                'stop': 'Cannot be used.'}[verdict]
        self.verdict.setText(f'<span style="color:{colour}">{text}</span>')
        icon = {'ok': '✓', 'fix': '⚠', 'stop': '✗'}
        self.findings.setText('<br>'.join(f'{icon[f.level]} {f.message}' + (f' <i>{f.suggestion}</i>' if f.suggestion else '')
                                          for f in findings))

    def current_recipe(self, with_selection=True):
        a, b = self.class_a.currentData(), self.class_b.currentData()
        classes = tuple(self.recipe.classes) if self.all_classes() else (a, b)
        recipe = D.Recipe(classes=classes, missing=self.missing.currentData(), text=self.text.currentData(),
                          per_class=self.per_class.value(), components=self.components.value(),
                          scale='pi' if self.scale.isChecked() else 'none', test_fraction=self.test_fraction.value())
        if with_selection and self.selection:
            recipe.select, recipe.components = tuple(self.selection['names']), 0
        return recipe

    # ---- features chosen by annealing (v0.9.13) ---------------------------------------------------------
    @staticmethod
    def _signature(recipe):
        """What the split depends on: chosen features stay valid while these are unchanged."""
        return (tuple(recipe.classes), recipe.missing, recipe.text, recipe.per_class, round(recipe.test_fraction, 6),
                recipe.seed)

    def choose_by_annealing(self):
        """Send this data, as the recipe cleans and splits it, to Quantum annealing; returns the task."""
        from quantumscope.ml import feature_selection as F
        try:
            task = F.make_task(self.dataset, self.current_recipe(with_selection=False), 'datasets',
                               self.dataset.name or 'your data', k=min(self.qubits.value(), F.MAX_CANDIDATES - 1))
        except ValueError as exc:
            self.selection_label.setText(f'Cannot choose features: {exc}')
            return None
        if self.choose_features_in is not None:
            self.choose_features_in(task)
        return task

    def use_features(self, task, names):
        """Prepare the task's data with the features an anneal chose (from Quantum annealing)."""
        if self.dataset is not task.dataset:
            index = self.source.findData(task.source)
            if index >= 0 and task.source in D.BUILTIN:
                self.source.blockSignals(True)
                self.source.setCurrentIndex(index)
                self.source.blockSignals(False)
                self.source_key = task.source
            else:
                self.source_key = 'imported' if task.source in ('datasets', 'store') else task.source
                if self.source_key == 'imported':
                    self._show_imported(task.dataset)
            self.use(task.dataset)
        r = task.recipe
        self.qubits.blockSignals(True)
        self.qubits.setValue(len(names))
        self.qubits.blockSignals(False)
        verdict, findings, _ = D.check(self.dataset, qubits=len(names), max_classes=None if self.all_classes() else 2)
        self._show_findings(verdict, findings)                 # the findings for this many qubits
        if len(r.classes) == 2:
            for box, value in ((self.class_a, r.classes[0]), (self.class_b, r.classes[1])):
                box.blockSignals(True)
                box.setCurrentIndex(box.findData(value))
                box.blockSignals(False)
        else:                                                   # all classes at once
            self.class_a.blockSignals(True)
            self.class_a.setCurrentIndex(max(0, self.class_a.findData(ALL)))
            self.class_a.blockSignals(False)
            self.recipe.classes = tuple(r.classes)
            self.vs_label.setVisible(False)
            self.class_b.setVisible(False)
        self.missing.setCurrentIndex(self.missing.findData(r.missing))
        self.text.setCurrentIndex(self.text.findData(r.text))
        self.per_class.setValue(r.per_class)
        self.test_fraction.setValue(r.test_fraction)
        self.selection = dict(names=list(names), signature=self._signature(r))
        self._show_selection()
        return self.prepare()

    def _show_selection(self):
        chosen = self.selection is not None
        self.components.setEnabled(not chosen)
        self.clear_selection.setEnabled(chosen)
        self.selection_label.setText(f'Chosen by annealing: {", ".join(self.selection["names"])} (instead of PCA).'
                                     if chosen else '')

    def _clear_selection_and_prepare(self):
        self.selection = None
        self._show_selection()
        self.prepare()

    def prepare(self):
        if self.selection and self._signature(self.current_recipe(with_selection=False)) != self.selection['signature']:
            self.selection = None
            self._show_selection()
            self.selection_label.setText('The classes or samples changed since the features were chosen, so they '
                                         'were set aside: choose them again.')
        recipe = self.current_recipe()
        if len(set(recipe.classes)) < len(recipe.classes):
            self.steps.setText('Choose two different classes.')
            return None
        try:
            prepared = D.prepare(self.dataset, recipe)
        except (ValueError, np.linalg.LinAlgError) as exc:
            self.steps.setText(f'Could not prepare the data: {exc}')
            return None
        if prepared.X_train.shape[1] > D.MAX_QUBITS:
            self.steps.setText(f'{prepared.X_train.shape[1]} features remain; reduce them to at most '
                               f'{D.MAX_QUBITS} (PCA components) to use them on qubits.')
        else:
            self.steps.setText('Prepared: ' + ' '.join(prepared.steps) + '  Both classifiers can now use it.')
            STORE.publish(self.dataset, recipe, prepared)
            from quantumscope.ml import progress
            progress.prepared(self.source_key, prepared.X_train.shape[1], prepared.classes)
            if recipe.select:
                from quantumscope.learn import progress as learn_progress
                learn_progress.record('featuresused', dataset=self.source_key, k=len(recipe.select),
                                      chosen='+'.join(recipe.select))
        self.plot.clear()
        if prepared.X_train.shape[1] >= 2:
            named = class_legend(self.plot, prepared.k)
            _scatter_points(self.plot, prepared.X_train[:, :2], prepared.y_train, palette=palette(prepared.k),
                            names=prepared.classes if named else None)
            self.plot.setLabel('bottom', prepared.features[0])
            self.plot.setLabel('left', prepared.features[1])
        self.images.show_images(self.dataset, recipe.classes)
        return prepared


# ============================================================================================
class _DataPicker(QGroupBox):
    """Which data a classifier trains on: from the Datasets tab, or a dataset with its suggested recipe."""

    def __init__(self, max_samples, parent=None, allow_all=False, many='one-vs-rest'):
        super().__init__('Data', parent)
        self.max_samples = max_samples
        self.allow_all = allow_all                 # offer All classes (v0.9.3)
        self.many = many                           # how this classifier separates many classes, in words
        form = QFormLayout(self)
        self.source = QComboBox()
        self.source.addItem('From the Datasets tab', 'store')
        self.source.insertSeparator(1)
        quick = _source_combo()
        for i in range(quick.count()):
            if quick.itemData(i):
                self.source.addItem(quick.itemText(i), quick.itemData(i))
        self.source.setCurrentIndex(self.source.findData('circles'))
        form.addRow('Dataset', self.source)
        self.qubits = QSpinBox()
        self.qubits.setRange(1, D.MAX_QUBITS)
        self.qubits.setValue(2)
        self.qubits.setToolTip('One feature per qubit: the data is reduced to this many features')
        form.addRow('Qubits (= features)', self.qubits)
        self.class_a, self.class_b = QComboBox(), QComboBox()
        for box in (self.class_a, self.class_b):
            box.setProperty('pair', True)          # for datasets with more than two classes
        self.class_row = QWidget()
        pair = QHBoxLayout(self.class_row)
        pair.setContentsMargins(0, 0, 0, 0)
        pair.addWidget(self.class_a)
        self.vs_label = QLabel('vs')
        pair.addWidget(self.vs_label)
        pair.addWidget(self.class_b)
        self.class_label = QLabel('Classes')
        form.addRow(self.class_label, self.class_row)
        self.summary = QLabel()
        self.summary.setWordWrap(True)
        self.summary.setObjectName('muted')
        form.addRow(self.summary)
        self.source.currentIndexChanged.connect(self._classes_for_source)
        self.source.currentIndexChanged.connect(self._sync)
        self.class_a.currentIndexChanged.connect(self._pair_visible)
        STORE.changed.connect(self._sync)
        self._classes_for_source()
        self._sync()

    def show_model_data(self, model):
        """Select a loaded model's dataset (built-in or synthetic), qubits and classes, if possible."""
        key = model.info.get('dataset', '')
        index = self.source.findData(key)
        if index < 0 or key == 'store':
            return False
        self.source.setCurrentIndex(index)
        self.qubits.setValue(model.pipeline.outputs)
        if len(model.classes) > 2:
            self.class_a.setCurrentIndex(max(0, self.class_a.findData(ALL)))
            return True
        for box, name in ((self.class_a, model.classes[0]), (self.class_b, model.classes[1])):
            at = box.findText(name)
            if at >= 0:
                box.setCurrentIndex(at)
        return True

    def _classes_for_source(self, *_):
        """Offer the dataset's classes when it has more than two (MNIST, Iris, …), defaulting to the
        checker's suggestion; hidden for two-class data and for the Datasets tab's data."""
        key = self.source.currentData()
        dataset = None if key in (None, 'store') else D.load(key)
        many = dataset is not None and len(dataset.classes) > 2
        self.class_row.setVisible(many)
        self.class_label.setVisible(many)
        if not many:
            return
        suggested = D.check(dataset, qubits=self.qubits.value(), max_samples=self.max_samples)[2].classes
        for box, default in ((self.class_a, suggested[0]), (self.class_b, suggested[1])):
            box.blockSignals(True)
            box.clear()
            if box is self.class_a and self.allow_all:
                box.addItem(f'All {len(dataset.classes)} classes', ALL)
            for k, name in enumerate(dataset.classes):
                box.addItem(name, k)
            box.setCurrentIndex(box.findData(default))
            box.blockSignals(False)
        self._pair_visible()

    def _pair_visible(self, *_):
        everything = self.class_a.currentData() == ALL
        self.vs_label.setVisible(not everything)
        self.class_b.setVisible(not everything)

    def _sync(self, *_):
        """From the Datasets tab, the qubit count is the prepared data's: shown, not editable here."""
        from_store = self.source.currentData() == 'store'
        self.qubits.setEnabled(not from_store)
        if from_store:
            if STORE.prepared is not None:
                self.qubits.blockSignals(True)
                self.qubits.setValue(STORE.prepared.X_train.shape[1])
                self.qubits.blockSignals(False)
                self.qubits.setToolTip('Set in the Datasets tab (one feature per qubit)')
                chosen = getattr(STORE.recipe, 'select', ())
                self.summary.setText(f'Prepared in the Datasets tab: {STORE.prepared.X_train.shape[1]} features '
                                     f'on as many qubits' + (f', chosen by annealing: {", ".join(chosen)}.' if chosen
                                                            else '.'))
            else:
                self.summary.setText('Nothing prepared yet: open the Datasets experiment and press Prepare.')
        else:
            self.qubits.setToolTip('One feature per qubit: the data is reduced to this many features')

    def key(self):
        """The dataset trained on: a built-in or synthetic key, or what the Datasets tab prepared."""
        key = self.source.currentData()
        if key == 'store':
            from quantumscope.ml import progress
            return progress.STATE.get('dataset')
        return key

    def prepared(self):
        key = self.source.currentData()
        if key == 'store':
            if STORE.prepared is None:
                self.summary.setText('Nothing prepared yet: open the Datasets experiment and press Prepare.')
                return None
            p = STORE.prepared
            if p.k > 2 and not self.allow_all:
                self.summary.setText(f'The Datasets tab prepared {p.k} classes; this classifier separates two. '
                                     f'Prepare two classes there, or choose a dataset here.')
                return None
            self.dataset = STORE.dataset
        else:
            dataset = D.load(key)
            verdict, _, recipe = D.check(dataset, qubits=self.qubits.value(), max_samples=self.max_samples)
            if verdict == 'stop':
                self.summary.setText('This dataset cannot be used.')
                return None
            if len(dataset.classes) > 2 and self.class_a.currentData() == ALL:
                verdict, _, recipe = D.check(dataset, qubits=self.qubits.value(), max_samples=self.max_samples,
                                             max_classes=None)
                if verdict == 'stop':
                    self.summary.setText('This dataset cannot be used.')
                    return None
            elif self.class_row.isVisible() or len(dataset.classes) > 2:
                a, b = self.class_a.currentData(), self.class_b.currentData()
                if a is not None and b is not None:
                    if a == b:
                        self.summary.setText('Choose two different classes.')
                        return None
                    recipe.classes = (a, b)
            p = D.prepare(dataset, recipe)
            self.dataset = dataset
        which = (f'{p.classes[0]} (+1) vs {p.classes[1]} (−1)' if p.k == 2 else f'{p.k} classes, {self.many}')
        self.summary.setText(f'{which}: {len(p.y_train)} for training, {len(p.y_test)} for testing, '
                             f'{p.X_train.shape[1]} features on {p.X_train.shape[1]} qubits.')
        return p


def region_plane(X_train, X_test=None):
    """The 2-D view for decision regions (no Qt: safe in a worker). With two features the plane is
    the data's own; with more, the plane of the two leading principal components of the training
    data, a slice through the n-dimensional feature space (each grid point is mapped back into it)."""
    n = X_train.shape[1]
    if n == 1:                                                   # one feature: a line, shown flat
        to_plane = lambda X: np.c_[X[:, 0], np.zeros(len(X))]       # noqa: E731
        from_plane = lambda P: P[:, :1]                              # noqa: E731
        labels = ('feature 1', '')
    elif n == 2:
        to_plane = from_plane = lambda X: X                          # noqa: E731
        labels = ('feature 1', 'feature 2')
    else:
        mean = X_train.mean(axis=0)
        _, _, vt = np.linalg.svd(X_train - mean, full_matrices=False)
        basis = vt[:2]
        to_plane = lambda X: (X - mean) @ basis.T                    # noqa: E731
        from_plane = lambda P: mean + P @ basis                      # noqa: E731
        labels = ('principal component 1', 'principal component 2')
    P_train = to_plane(X_train)
    P_all = P_train if X_test is None or not len(X_test) else np.r_[P_train, to_plane(X_test)]
    lo, hi = P_all.min(axis=0), P_all.max(axis=0)
    pad = 0.08 * np.maximum(hi - lo, 1e-6)
    lo, hi = lo - pad, hi + pad
    if n == 1:
        lo[1], hi[1] = -1.0, 1.0
    res = 90 if n <= 4 else 70 if n <= 6 else 50                 # 2ⁿ amplitudes per grid point
    gx, gy = np.linspace(lo[0], hi[0], res), np.linspace(lo[1], hi[1], res)
    grid = from_plane(np.array([(a, b) for b in gy for a in gx]))
    title = 'Decision regions' + ('' if n <= 2 else f' in the plane of the first two principal components '
                                                  f'(a slice through {n}-D)') + ': training ●, test ▲, mistakes ✕'
    return dict(n=n, to_plane=to_plane, labels=labels, title=title, lo=lo, hi=hi, res=res, grid=grid)


def region_values(decision, plane):
    """The decision function on the plane's grid, as res × res (rows: y), or res × res × k with one
    value per class. No Qt: safe in a worker."""
    grid = plane['grid']
    values = np.concatenate([decision(chunk) for chunk in np.array_split(grid, max(1, len(grid) // 1500))])
    return values.reshape((plane['res'], plane['res']) + values.shape[1:])


def class_legend(plot, k):
    """A legend for more than two classes (cleared otherwise); returns whether names should be given."""
    legend = plot.getPlotItem().legend
    if legend is not None:
        legend.clear()
        legend.setVisible(k > 2)
    if k > 2 and legend is None:
        plot.addLegend(offset=(-8, 8), brush=(11, 20, 32, 190))
    return k > 2


def draw_regions(plot, plane, f, X_train, y_train, X_test=None, y_test=None, predicted=None, k=2, names=None):
    """Draw decision regions (f from region_values, or None for points only) on the interface thread.
    With more classes, each region takes its class's colour, deeper where it wins by more."""
    import pyqtgraph as pg
    plot.clear()
    plot.setLabel('bottom', plane['labels'][0])
    plot.setLabel('left', plane['labels'][1])
    plot.setTitle(plane['title'])
    lo, hi, to_plane = plane['lo'], plane['hi'], plane['to_plane']
    colours = palette(k)
    if f is not None and np.ndim(f) == 3:
        from quantumscope.ml.views import class_margins
        margins = class_margins(f)
        winner, lead = margins.argmax(axis=-1), margins.max(axis=-1)
        scale = max(1e-9, float(np.percentile(lead, 95)))
        rgb = np.array([QColor(c).getRgb()[:3] for _, c in colours], float)
        rgba = np.empty(winner.shape + (4,), np.uint8)
        rgba[..., :3] = rgb[winner].astype(np.uint8)
        rgba[..., 3] = (30 + 110 * np.clip(lead / scale, 0, 1)).astype(np.uint8)
        image = pg.ImageItem(np.transpose(rgba, (1, 0, 2)))
        image.setRect(QRectF(lo[0], lo[1], hi[0] - lo[0], hi[1] - lo[1]))
        plot.addItem(image)
        for c in range(f.shape[-1]):                              # each region's edge
            if (winner == c).any():
                edge = pg.IsocurveItem(margins[..., c].T, level=0.0, pen=pg.mkPen('#ffffff', width=1.5))
                edge.setParentItem(image)
        image.setZValue(-10)
        f = None                                                  # drawn
    if f is not None:
        scale = max(1e-9, float(np.percentile(np.abs(f), 95)))
        strength = np.clip(np.abs(f) / scale, 0, 1)
        plus, minus = np.array((90, 230, 255), float), np.array((255, 154, 90), float)
        base = np.where((f >= 0)[..., None], plus, minus)
        rgba = np.empty(f.shape + (4,), np.uint8)
        rgba[..., :3] = base.astype(np.uint8)
        rgba[..., 3] = (30 + 110 * strength).astype(np.uint8)     # confidence: deeper colour
        image = pg.ImageItem(np.transpose(rgba, (1, 0, 2)))       # ImageItem wants (x, y)
        image.setRect(QRectF(lo[0], lo[1], hi[0] - lo[0], hi[1] - lo[1]))
        plot.addItem(image)
        boundary = pg.IsocurveItem(f.T, level=0.0, pen=pg.mkPen('#ffffff', width=2))
        boundary.setParentItem(image)                             # follows the image's placement
        image.setZValue(-10)
    named = class_legend(plot, k) and names is not None
    _scatter_points(plot, to_plane(X_train), y_train, size=7, palette=colours, names=names if named else None)
    if X_test is not None and len(X_test):
        P_test = to_plane(X_test)
        wrong = predicted != y_test
        _scatter_points(plot, P_test[~wrong], y_test[~wrong], size=11, symbol='t', outline='#ffffff', palette=colours)
        if wrong.any():
            plot.addItem(pg.ScatterPlotItem(P_test[wrong, 0], P_test[wrong, 1], size=14, symbol='x',
                                            brush=pg.mkBrush('#ff4d4d'), pen=pg.mkPen('#ff4d4d', width=2)))
    plot.disableAutoRange()
    plot.setRange(xRange=(lo[0], hi[0]), yRange=(lo[1], hi[1]), padding=0)


def _regions(plot, decision, X_train, y_train, X_test=None, y_test=None, predicted=None, k=2):
    """Compute and draw in one go (on the interface thread), for quick, small cases."""
    plane = region_plane(X_train, X_test)
    draw_regions(plot, plane, None if decision is None else region_values(decision, plane),
                 X_train, y_train, X_test, y_test, predicted, k)


# ============================================================================================
class KernelExperiment(QWidget):
    """A quantum kernel and a classical classifier on top of it."""

    def __init__(self, parent=None):
        super().__init__(parent)
        root = QHBoxLayout(self)
        left = QWidget()
        left.setMaximumWidth(392)
        form = QVBoxLayout(left)
        title = QLabel('QUANTUM KERNEL CLASSIFIER  ·  compare data points as quantum states')
        title.setStyleSheet('font-weight:700;')
        title.setWordWrap(True)
        form.addWidget(title)
        self.data = _DataPicker(max_samples=200, allow_all=True)
        form.addWidget(self.data)
        model = QGroupBox('Kernel and classifier')
        mv = QFormLayout(model)
        self.feature_map = QComboBox()
        for key, label in K.FEATURE_MAPS.items():
            self.feature_map.addItem(label, key)
        mv.addRow('Feature map', self.feature_map)
        self.reps = QSpinBox()
        self.reps.setRange(1, 4)
        self.reps.setValue(2)
        mv.addRow('Repetitions (ZZ)', self.reps)
        self.bandwidth = QDoubleSpinBox()
        self.bandwidth.setRange(0.05, 2.0)
        self.bandwidth.setSingleStep(0.05)
        self.bandwidth.setValue(1.0)
        self.bandwidth.setToolTip('Scales the data before encoding: smaller is smoother')
        mv.addRow('Bandwidth', self.bandwidth)
        self.shots = QSpinBox()
        self.shots.setRange(0, 100000)
        self.shots.setSingleStep(100)
        self.shots.setSpecialValueText('exact')
        self.shots.setToolTip('Estimate each kernel entry from this many shots, as a quantum computer would')
        mv.addRow('Shots per entry', self.shots)
        self.method = QComboBox()
        self.method.addItem('Support vector machine', 'svm')
        self.method.addItem('Kernel ridge', 'ridge')
        mv.addRow('Classifier', self.method)
        self.strength = QDoubleSpinBox()
        self.strength.setRange(0.001, 100.0)
        self.strength.setDecimals(3)
        self.strength.setValue(1.0)
        self.strength.setToolTip('SVM: C (larger fits the training data harder). Ridge: λ (larger is smoother)')
        mv.addRow('C or λ', self.strength)
        self.train_button, self.cancel_button = QPushButton('Train'), QPushButton('Cancel')
        self.cancel_button.setEnabled(False)
        row = QHBoxLayout()
        row.addWidget(self.train_button)
        row.addWidget(self.cancel_button)
        mv.addRow(row)
        form.addWidget(model)
        from quantumscope.gui.model_panel import ModelPanel
        self.model_panel = ModelPanel('kernel')
        self.model_panel.on_loaded = self._use_loaded
        form.addWidget(self.model_panel)
        self.result = QLabel('Press Train.')
        self.result.setWordWrap(True)
        form.addWidget(self.result)
        form.addStretch()
        from quantumscope.gui.side_panel import CollapsiblePanel
        root.addWidget(CollapsiblePanel(_scrolling(left, form), 'Classifier settings', 'qml-kernel'))
        from PySide6.QtWidgets import QSplitter, QTabWidget
        right = QSplitter(Qt.Orientation.Vertical)                # drag the divider to resize
        right.setChildrenCollapsible(False)
        self.regions = _plot('Decision regions')
        self.top_tabs = QTabWidget()
        self.top_tabs.addTab(self.regions, 'Decision regions')
        from quantumscope.gui.decision3d import Decision3DView
        self.view3d = Decision3DView(on_pick=self._show_sample)
        self.top_tabs.addTab(self.view3d, '3-D view')
        right.addWidget(self.top_tabs)
        lower = QWidget()
        below = QHBoxLayout(lower)
        below.setContentsMargins(0, 0, 0, 0)
        self.views = QTabWidget()
        self.heatmap = _plot('Training kernel K(x, x′), sorted by class (dashed: where the classes meet)')
        self.views.addTab(self.heatmap, 'Kernel matrix')
        self.kernel_map = _plot('Kernel map: the data as the kernel sees it', 'kernel component 1', 'kernel component 2')
        self.views.addTab(self.kernel_map, 'Kernel map')
        from quantumscope.gui.evaluation_panel import EvaluationPanel, SearchPanel
        self.evaluation = EvaluationPanel(cross_validate=self._cross_validate)
        self.views.addTab(self.evaluation, 'Evaluation')
        self.search_panel = SearchPanel(self._start_search, self._use_best)
        self.views.addTab(self.search_panel, 'Search')
        self.views.currentChanged.connect(                         # samples matter beside the kernel views only
            lambda index: self.sample_view.setVisible(self.views.widget(index) in (self.heatmap, self.kernel_map)))
        below.addWidget(self.views, 1)
        self.sample_view = SampleView()
        below.addWidget(self.sample_view)
        right.addWidget(lower)
        right.setStretchFactor(0, 3)
        right.setStretchFactor(1, 2)
        right.setSizes([600, 400])                                # regions 3 : lower area 2
        self.splitter = right
        root.addWidget(right, 1)
        self.heatmap.scene().sigMouseMoved.connect(self._heat_hover)
        self.heatmap.scene().sigMouseClicked.connect(self._heat_click)
        self.train_button.clicked.connect(self.train)
        self.cancel_button.clicked.connect(lambda: self.run.cancel() if getattr(self, 'run', None) else None)

    def train(self):
        """Train in the background; returns the run (run.wait() returns the result, for scripts)."""
        if getattr(self, 'run', None) is not None and self.run.running():
            return self.run
        p = self.data.prepared()
        if p is None:
            return None
        if p.X_train.shape[1] > D.MAX_QUBITS:
            self.result.setText('Too many features for the qubits: reduce them in the Datasets tab.')
            return None
        from quantumscope import resources as R
        from quantumscope.gui.resource_monitor import confirm_memory
        if not confirm_memory(self, R.kernel_matrix(len(p.y_train), len(p.y_test), p.X_train.shape[1]),
                              f'A kernel for {len(p.y_train)} training samples on {p.X_train.shape[1]} qubits'):
            self.result.setText('Not trained: use fewer samples or qubits.')
            return None
        settings = dict(kind=self.feature_map.currentData(), reps=self.reps.value(), bandwidth=self.bandwidth.value(),
                        shots=self.shots.value(), method=self.method.currentData(), strength=self.strength.value(),
                        dataset=self.data.key())
        plane = region_plane(p.X_train, p.X_test)

        def work(report, cancelled):                              # the worker: no widgets here
            kind, reps, bandwidth = settings['kind'], settings['reps'], settings['bandwidth']
            rng = np.random.default_rng(0)
            report(f'Computing the {len(p.y_train)}×{len(p.y_train)} training kernel…')
            exact_train = K.kernel(p.X_train, kind=kind, reps=reps, bandwidth=bandwidth)
            Ktr = K.estimate(exact_train, settings['shots'], rng, symmetric=True)
            if cancelled():
                return None
            report('Computing the test kernel…')
            Kte = K.estimate(K.kernel(p.X_test, p.X_train, kind=kind, reps=reps, bandwidth=bandwidth),
                             settings['shots'], rng)
            if cancelled():
                return None
            report('Training the classifier…' if p.k == 2 else f'Training {p.k} classifiers (one per class)…')
            model = K.classifier(settings['method'], settings['strength'], p.k).fit(Ktr, p.y_train)
            predicted = model.predict(Kte)
            if cancelled():
                return None
            report('Drawing the decision regions…')

            def decision(points):
                return model.decision(K.kernel(points, p.X_train, kind=kind, reps=reps, bandwidth=bandwidth))
            f = region_values(decision, plane)
            order = np.argsort(-p.y_train if p.k == 2 else p.y_train, kind='stable')   # grouped by class
            off = float((exact_train.sum() - len(exact_train)) / max(1, len(exact_train) * (len(exact_train) - 1)))
            from quantumscope.ml import views
            map_train, map_test, shown, _ = views.kernel_map(Ktr, Kte)
            return dict(train=K.accuracy(p.y_train, model.predict(Ktr)), test=K.accuracy(p.y_test, predicted),
                        model=model, prepared=p, predicted=predicted, f=f, heat=Ktr[np.ix_(order, order)],
                        order=order, error=float(np.abs(Ktr - exact_train).mean()), off=off,
                        decision_train=model.decision(Ktr), decision_test=model.decision(Kte),
                        map_train=map_train, map_test=map_test, map_shown=shown)

        self.train_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.result.setText('Starting…')
        from quantumscope.gui.background import Run
        self.run = Run(work, on_progress=self.result.setText, owner=self, task='Training the kernel classifier',
                       on_done=lambda r: self._trained(r, settings, plane),
                       on_error=self._failed).start()
        return self.run

    def _draw_kernel_map(self, r):
        import pyqtgraph as pg
        p, plot = r['prepared'], self.kernel_map
        plot.clear()
        concentrated = r['off'] < 0.05
        plot.setTitle(f'Kernel map: {r["map_shown"]:.0%} of the kernel\'s variance shown'
                      + (' · points scatter apart: kernel concentration' if concentrated else ''))
        named = class_legend(plot, p.k)
        for which, coords, labels, symbol, size in (('train', r['map_train'], p.y_train, 'o', 8),
                                                    ('test', r['map_test'], p.y_test, 't', 11)):
            for label, colour in palette(p.k):
                chosen = np.flatnonzero(labels == label)
                if not len(chosen):
                    continue
                spots = pg.ScatterPlotItem(coords[chosen, 0], coords[chosen, 1], size=size, symbol=symbol,
                                           name=p.label_name(label) if named and which == 'train' else None,
                                           brush=pg.mkBrush(colour), data=[(which, int(i)) for i in chosen],
                                           pen=pg.mkPen('#ffffff' if which == 'test' else '#0b1420', width=1))
                spots.sigClicked.connect(lambda item, points, ev=None: self._show_points(points))
                plot.addItem(spots)
        if len(r['predicted']):
            wrong = np.flatnonzero(r['predicted'] != p.y_test)
            if len(wrong):                                        # mistakes: clicking one shows that sample
                marks = pg.ScatterPlotItem(r['map_test'][wrong, 0], r['map_test'][wrong, 1], size=14, symbol='x',
                                           brush=pg.mkBrush('#ff4d4d'), pen=pg.mkPen('#ff4d4d', width=2),
                                           data=[('test', int(i)) for i in wrong])
                marks.sigClicked.connect(lambda item, points, ev=None: self._show_points(points))
                plot.addItem(marks)
        plot.enableAutoRange()

    def sample_entry(self, which, index):
        """A sample's details for the sample viewer: which is 'train' or 'test'."""
        r, ds = self.last, self.dataset
        p = r['prepared']
        rows = p.train_rows if which == 'train' else p.test_rows
        value = (r['decision_train'] if which == 'train' else r['decision_test'])[index]
        truth = p.label_name((p.y_train if which == 'train' else p.y_test)[index])
        if p.k == 2:
            predicted = p.classes[0] if value >= 0 else p.classes[1]
            detail = f'decision {value:+.3f}'
        else:                                                     # the most confident of the k classifiers
            best = int(np.argmax(value))
            predicted = p.classes[best]
            detail = f'confidence {value[best]:+.3f} (next {np.sort(value)[-2]:+.3f})'
        lines = [f'true class {truth}', f'predicted {predicted}' + ('' if predicted == truth else ' ✗'), detail]
        entry = dict(heading=f'{"Training" if which == "train" else "Test"} sample {index + 1}', lines=lines)
        if ds is not None and rows is not None:
            raw = ds.X[rows[index]]
            if ds.image_shape:
                entry['image'] = raw.reshape(ds.image_shape)
            else:
                shown = [f'{ds.features[j]}: {raw[j]:.4g}' for j in range(min(6, len(raw)))]
                entry['lines'] += shown + (['…'] if len(raw) > 6 else [])
        return entry

    def _show_sample(self, which, index):
        if getattr(self, 'last', None) is not None:
            self.sample_view.show_samples([self.sample_entry(which, index)])

    def _show_points(self, points):
        if not len(points) or getattr(self, 'last', None) is None:
            return
        which, index = points[0].data()
        self.sample_view.show_samples([self.sample_entry(which, index)])

    def _heat_cell(self, scene_pos):
        """The (row, column) of the kernel matrix under the mouse, in training-sample numbers, or None."""
        r = getattr(self, 'last', None)
        if r is None or not self.heatmap.sceneBoundingRect().contains(scene_pos):
            return None
        point = self.heatmap.getPlotItem().vb.mapSceneToView(scene_pos)
        size = len(r['order'])
        i, j = int(point.y()), int(point.x())
        if not (0 <= i < size and 0 <= j < size):
            return None
        return int(r['order'][j]), int(r['order'][i]), r['heat'][j, i]

    def _heat_hover(self, scene_pos):
        cell = self._heat_cell(scene_pos)
        if cell is None:
            self.heatmap.setToolTip('')
            return
        a, b, value = cell
        p = self.last['prepared']
        name = lambda k: p.label_name(p.y_train[k])                              # noqa: E731
        self.heatmap.setToolTip(f'K = {value:.3f} between training samples {a + 1} ({name(a)}) and {b + 1} ({name(b)})'
                                '\nClick to see both.')

    def _heat_click(self, event):
        cell = self._heat_cell(event.scenePos())
        if cell is None:
            return
        a, b, value = cell
        self.sample_view.show_samples([self.sample_entry('train', a), self.sample_entry('train', b)],
                                      f'Kernel value K = {value:.3f}')

    def _cross_validate(self, k, on_progress, on_done):
        """Cross-validate the trained settings on the training data, sharing one kernel across folds."""
        from quantumscope.gui.background import Run
        from quantumscope.ml import evaluation as E
        r = getattr(self, 'last', None)
        if r is None:
            on_done(None, 'train first')
            return None
        p, s = r['prepared'], self._settings

        def work(report, cancelled):
            folds = E.stratified_folds(p.y_train, k, seed=0)
            Kx = K.kernel(p.X_train, kind=s['kind'], reps=s['reps'], bandwidth=s['bandwidth'])
            report((1, 2))
            return E.cross_validate_kernel(Kx, p.y_train, lambda: K.classifier(s['method'], s['strength'], p.k),
                                           folds, p.k)
        return Run(work, owner=self, task='Cross-validation', on_progress=on_progress, on_done=on_done,
                   on_error=lambda exc, details: on_done(None, exc)).start()

    def _start_search(self, grid, k, on_progress, on_done):
        """Search the grid on the current data's training split, in the background."""
        from quantumscope.gui.background import Run
        from quantumscope.ml import evaluation as E
        r = getattr(self, 'last', None)
        p = r['prepared'] if r is not None else self.data.prepared()
        if p is None:
            on_done(None, 'no data')
            return None

        def work(report, cancelled):
            return E.search_kernel(p.X_train, p.y_train, grid, k=k, progress=lambda d, t: report((d, t)),
                                   cancelled=cancelled)
        return Run(work, owner=self, task='The grid search', on_progress=on_progress, on_done=on_done,
                   on_error=lambda exc, details: on_done(None, exc)).start()

    def _use_best(self, settings):
        """Set the controls to the search's best settings and train with them."""
        self.feature_map.setCurrentIndex(self.feature_map.findData(settings['feature_map']))
        self.reps.setValue(int(settings['reps']))
        self.bandwidth.setValue(float(settings['bandwidth']))
        self.method.setCurrentIndex(self.method.findData(settings['method']))
        self.strength.setValue(float(settings['strength']))
        self.views.setCurrentWidget(self.evaluation)
        return self.train()

    def _use_loaded(self, model):
        """Match the controls to a loaded model, so they describe it (and Train would rebuild it)."""
        s = model.settings
        self.feature_map.setCurrentIndex(self.feature_map.findData(s['feature_map']))
        self.reps.setValue(int(s['reps']))
        self.bandwidth.setValue(float(s['bandwidth']))
        self.method.setCurrentIndex(self.method.findData(s.get('method', 'svm')))
        self.strength.setValue(float(s.get('strength', 1.0)))
        self.shots.setValue(int(s.get('shots', 0)))
        self.data.show_model_data(model)

    def _failed(self, exc, details):
        self.train_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.result.setText(f'Training failed: {exc}')

    def _trained(self, r, settings, plane):
        import pyqtgraph as pg
        self.train_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        if r is None:
            self.result.setText('Cancelled.')
            return
        p = r['prepared']
        extra = f', {len(r["model"].support)} support vectors' if settings['method'] == 'svm' else ''
        if p.k > 2:
            extra += f' ({p.k} one-vs-rest classifiers; chance is about {1 / p.k:.0%})'
        noise = '' if not settings['shots'] else (f' Kernel estimated from {settings["shots"]} shots per entry '
                                                 f'(typical error {r["error"]:.3f}).')
        hint = '' if r['off'] >= 0.05 else (f' The kernel is close to 0 for different points (average {r["off"]:.3f}): '
                                            f'kernel concentration, common for entangling maps on many qubits. '
                                            f'Try a smaller bandwidth.')
        self.result.setText(f'Training accuracy {r["train"]:.0%}, test accuracy {r["test"]:.0%}{extra}.{noise}{hint}')
        draw_regions(self.regions, plane, r['f'], p.X_train, p.y_train, p.X_test, p.y_test, r['predicted'], p.k,
                     p.classes)
        self.heatmap.clear()
        image = pg.ImageItem(r['heat'])
        image.setLookupTable(pg.colormap.get('viridis').getLookupTable(0, 1, 256))
        image.setLevels((0, 1))
        self.heatmap.addItem(image)
        size = len(r['heat'])
        self.heatmap.setAspectLocked(False)                      # fill the panel
        self.heatmap.disableAutoRange()
        self.heatmap.setRange(xRange=(0, size), yRange=(0, size), padding=0)
        if p.k == 2:                                              # the class borders, as thin lines
            splits = [int((p.y_train == 1).sum())]
        else:
            splits = list(np.cumsum(np.bincount(p.y_train, minlength=p.k))[:-1])
        for split in splits:
            for angle in (90, 0):
                line = pg.InfiniteLine(int(split), angle=angle, pen=pg.mkPen('#ffffff', width=1, style=Qt.PenStyle.DashLine))
                line.setZValue(10)                               # above the image
                self.heatmap.addItem(line)
        self.last = r
        self.dataset = self.data.dataset
        self._draw_kernel_map(r)
        from quantumscope.ml import models as M
        trained = M.from_kernel(r['model'], p, settings, r['train'], r['test'], settings['dataset'])
        self.model_panel.set_model(trained)
        self._settings = settings
        self.evaluation.show_results(p.y_test, r['decision_test'], p.classes)
        self.view3d.set_result(r, trained)
        from quantumscope.ml import progress
        progress.trained('kernel', train=r['train'], test=r['test'], map=settings['kind'],
                         bandwidth=settings['bandwidth'], shots=settings['shots'], dataset=settings['dataset'],
                         classes=p.k)


# ============================================================================================
class VariationalExperiment(QWidget):
    """A trainable quantum circuit as a classifier, trained live."""

    def __init__(self, parent=None):
        super().__init__(parent)
        root = QHBoxLayout(self)
        left = QWidget()
        left.setMaximumWidth(392)
        form = QVBoxLayout(left)
        title = QLabel('VARIATIONAL CLASSIFIER  ·  train a quantum circuit to separate the classes')
        title.setStyleSheet('font-weight:700;')
        title.setWordWrap(True)
        form.addWidget(title)
        self.data = _DataPicker(max_samples=300, allow_all=True, many='one outcome per class')
        form.addWidget(self.data)
        model = QGroupBox('Circuit and training')
        mv = QFormLayout(model)
        self.feature_map = QComboBox()
        for key, label in K.FEATURE_MAPS.items():
            self.feature_map.addItem(label, key)
        mv.addRow('Feature map', self.feature_map)
        self.layers = QSpinBox()
        self.layers.setRange(1, 8)
        self.layers.setValue(3)
        mv.addRow('Trainable layers', self.layers)
        self.method = QComboBox()
        self.method.addItem('BFGS (parameter-shift gradients)', 'BFGS')
        self.method.addItem('Adam (steady steps)', 'Adam')
        self.method.addItem('Gradient descent (fixed learning rate)', 'gradient')
        self.method.setToolTip('BFGS chooses its own step size, so the learning rate does not apply to it. Adam '
                               'adapts its steps; gradient descent moves the learning rate × the gradient each step')
        mv.addRow('Optimizer', self.method)
        self.steps = QSpinBox()
        self.steps.setRange(5, 1000)
        self.steps.setValue(80)
        mv.addRow('Steps', self.steps)
        self.seed = QSpinBox()
        self.seed.setRange(0, 9999)
        mv.addRow('Starting point (seed)', self.seed)
        self.loss_box = QComboBox()
        for label, key in (('Mean squared error', 'mse'), ('Hinge (as an SVM)', 'hinge'), ('Cross-entropy', 'cross-entropy')):
            self.loss_box.addItem(label, key)
        self.loss_box.setToolTip('With more than two classes the loss is always cross-entropy, on the probabilities '
                                 'of the classes\' measurement outcomes')
        mv.addRow('Loss', self.loss_box)
        self.rate = QDoubleSpinBox()
        self.rate.setRange(0.001, 1.0)
        self.rate.setDecimals(3)
        self.rate.setSingleStep(0.01)
        self.rate.setValue(0.1)
        self.rate.setToolTip('How far each step moves: too large and the loss jumps around or blows up, too small '
                             'and it crawls. Adam and gradient descent only: BFGS chooses its own step size')
        mv.addRow('Learning rate', self.rate)
        self.rate_note = QLabel('BFGS chooses its own step size: choose Adam or gradient descent to set a learning rate.')
        self.rate_note.setWordWrap(True)
        self.rate_note.setObjectName('muted')
        mv.addRow(self.rate_note)
        self.batch = QSpinBox()
        self.batch.setRange(0, 5000)
        self.batch.setSpecialValueText('all')
        self.batch.setToolTip('Adam and gradient descent only: each step on a random batch of this many samples')
        mv.addRow('Batch size', self.batch)
        self.validation_share = QDoubleSpinBox()
        self.validation_share.setRange(0.0, 0.4)
        self.validation_share.setSingleStep(0.05)
        self.validation_share.setSpecialValueText('none')
        self.validation_share.setToolTip('Part of the training data held out to watch for overfitting')
        mv.addRow('Validation share', self.validation_share)
        self.patience = QSpinBox()
        self.patience.setRange(0, 500)
        self.patience.setSpecialValueText('off')
        self.patience.setToolTip('Stop when the validation loss has not improved for this many steps, and keep '
                                 'the best step')
        mv.addRow('Early stopping', self.patience)
        self.method.currentIndexChanged.connect(self._adam_controls)
        self.validation_share.valueChanged.connect(self._adam_controls)
        buttons = QHBoxLayout()
        self.train_button, self.stop_button = QPushButton('Train'), QPushButton('Stop')
        self.stop_button.setEnabled(False)
        buttons.addWidget(self.train_button)
        buttons.addWidget(self.stop_button)
        mv.addRow(buttons)
        self.open_circuit = QPushButton('Open in circuit simulator')
        self.open_circuit.setToolTip('The trained circuit for the first test point, with the observable Z0 (two '
                                     'classes) or the readout qubits measured (more classes)')
        self.open_circuit.setEnabled(False)
        mv.addRow(self.open_circuit)
        form.addWidget(model)
        from quantumscope.gui.model_panel import ModelPanel
        self.model_panel = ModelPanel('variational')
        self.model_panel.on_loaded = self._use_loaded
        form.addWidget(self.model_panel)
        self.result = QLabel('Press Train.')
        self.result.setWordWrap(True)
        form.addWidget(self.result)
        form.addStretch()
        from quantumscope.gui.side_panel import CollapsiblePanel
        root.addWidget(CollapsiblePanel(_scrolling(left, form), 'Circuit and training', 'qml-vqc'))
        right = QVBoxLayout()
        self.regions = _plot('Decision regions')
        right.addWidget(self.regions, 3)
        from PySide6.QtWidgets import QTabWidget
        from quantumscope.gui.evaluation_panel import EvaluationPanel
        self.views = QTabWidget()
        self.curve = _plot('Training', 'step', 'loss / accuracy')
        self.curve.addLegend(offset=(8, 4))
        self.loss_line = self.curve.plot(pen='#5ae6ff', name='loss')
        self.acc_line = self.curve.plot(pen='#5ad48a', name='training accuracy')
        dash = Qt.PenStyle.DashLine
        import pyqtgraph as pg
        self.val_loss_line = self.curve.plot(pen=pg.mkPen('#5ae6ff', style=dash), name='validation loss')
        self.val_acc_line = self.curve.plot(pen=pg.mkPen('#5ad48a', style=dash), name='validation accuracy')
        self.views.addTab(self.curve, 'Training')
        self.evaluation = EvaluationPanel(cross_validate=self._cross_validate)
        self.views.addTab(self.evaluation, 'Evaluation')
        right.addWidget(self.views, 2)
        root.addLayout(right, 1)
        self.model = None
        self._adam_controls()
        for signal in (self.data.class_a.currentIndexChanged, self.data.source.currentIndexChanged, STORE.changed):
            signal.connect(self._loss_for_classes)
        self._loss_for_classes()
        self.train_button.clicked.connect(self.train)
        self.stop_button.clicked.connect(lambda: self.run.cancel() if getattr(self, 'run', None) else None)
        self.open_circuit.clicked.connect(self.open_in_circuit)

    def _options(self):
        """The training settings from the controls (shared by Train and Cross-validate)."""
        stepped = self.method.currentData() in ('Adam', 'gradient')
        return dict(method=self.method.currentData(), steps=self.steps.value(), rate=self.rate.value(),
                    batch_size=self.batch.value() if stepped else 0, seed=self.seed.value())

    def _many_classes(self):
        """Whether the chosen data has more than two classes (then the loss is cross-entropy)."""
        key = self.data.source.currentData()
        if key == 'store':
            return STORE.prepared is not None and STORE.prepared.k > 2
        return self.data.class_a.currentData() == ALL and self.data.class_row.isVisibleTo(self.data)

    def _loss_for_classes(self, *_):
        many = self._many_classes()
        if many:
            if self.loss_box.isEnabled():
                self._chosen_loss = self.loss_box.currentData()
            self.loss_box.setCurrentIndex(self.loss_box.findData('cross-entropy'))
        elif not self.loss_box.isEnabled() and getattr(self, '_chosen_loss', None):
            self.loss_box.setCurrentIndex(self.loss_box.findData(self._chosen_loss))   # back to the student's choice
        self.loss_box.setEnabled(not many)

    def _adam_controls(self, *_):
        stepped = self.method.currentData() in ('Adam', 'gradient')   # BFGS chooses its own step size
        self.rate.setEnabled(stepped)
        self.batch.setEnabled(stepped)
        self.rate_note.setVisible(not stepped)
        self.patience.setEnabled(self.validation_share.value() > 0)

    def _new_model(self, p):
        if p.k > 2:                                               # one circuit, one outcome per class (v0.9.4)
            return V.MultiClassifier(p.X_train.shape[1], p.k, layers=self.layers.value(),
                                     feature_map=self.feature_map.currentData(), seed=self.seed.value())
        return V.Classifier(p.X_train.shape[1], layers=self.layers.value(), feature_map=self.feature_map.currentData(),
                            seed=self.seed.value(), loss=self.loss_box.currentData())

    def train(self):
        """Train in the background; returns the run (run.wait() returns the result, for scripts)."""
        if getattr(self, 'run', None) is not None and self.run.running():
            return self.run
        p = self.data.prepared()
        if p is None:
            return None
        if p.X_train.shape[1] > D.MAX_QUBITS:
            self.result.setText('Too many features for the qubits: reduce them in the Datasets tab.')
            return None
        if p.k > 2 and V.readout_qubits(p.k) > p.X_train.shape[1]:
            self.result.setText(f'{p.k} classes are read from {V.readout_qubits(p.k)} qubits (one outcome per class): '
                                f'use at least {V.readout_qubits(p.k)} qubits.')
            return None
        from quantumscope.ml import evaluation as E
        self.prepared = p
        model = self._new_model(p)
        options = self._options()
        share = self.validation_share.value()
        if share > 0:                                             # held out from the training data
            kept, held = E.stratified_split(p.y_train, share, seed=self.seed.value())
            fit, validation = (p.X_train[kept], p.y_train[kept]), (p.X_train[held], p.y_train[held])
            options.update(validation=validation, patience=self.patience.value())
        else:
            fit = (p.X_train, p.y_train)
        settings = dict(method=options['method'], steps=options['steps'], layers=self.layers.value(),
                        map=self.feature_map.currentData(), dataset=self.data.key(),
                        loss=self.loss_box.currentData() if p.k == 2 else 'cross-entropy')
        plane = region_plane(p.X_train, p.X_test)
        self._history, self._validation = [], []

        def work(report, cancelled):                              # the worker: no widgets here
            def step(index, loss, accuracy, valid=None):
                regions = None
                if index % 5 == 0:                                # fresh regions now and then
                    regions = (region_values(model.decision, plane), model.predict(p.X_test))
                report((index, loss, accuracy, valid, regions))
                return not cancelled()
            model.train(*fit, callback=step, **options)
            decision = model.decision(p.X_test)
            predicted = model.predict(p.X_test)
            return dict(model=model, predicted=predicted, decision_test=decision,
                        test=float(np.mean(predicted == p.y_test)), f=region_values(model.decision, plane),
                        stopped=cancelled(), stopped_early=model.stopped_early, best_step=model.best_step)

        self.train_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.open_circuit.setEnabled(False)
        self.result.setText('Starting…')
        from quantumscope.gui.background import Run
        self.run = Run(work, owner=self, task='Training the variational classifier', on_progress=lambda v: self._step(v, plane),
                       on_done=lambda r: self._trained(r, settings, plane), on_error=self._failed).start()
        return self.run

    def _step(self, value, plane):
        index, loss, accuracy, valid, regions = value
        self._history.append((loss, accuracy))
        steps = list(range(len(self._history)))
        self.loss_line.setData(steps, [h[0] for h in self._history])
        self.acc_line.setData(steps, [h[1] for h in self._history])
        text = f'Step {index}: loss {loss:.4f}, training accuracy {accuracy:.0%}'
        if valid is not None:
            self._validation.append(valid)
            self.val_loss_line.setData(steps, [v[0] for v in self._validation])
            self.val_acc_line.setData(steps, [v[1] for v in self._validation])
            text += f'; validation loss {valid[0]:.4f}, accuracy {valid[1]:.0%}'
        else:
            self.val_loss_line.setData([], [])
            self.val_acc_line.setData([], [])
        self.result.setText(text)
        if regions is not None:
            p = self.prepared
            draw_regions(self.regions, plane, regions[0], p.X_train, p.y_train, p.X_test, p.y_test, regions[1], p.k,
                         p.classes)

    def _cross_validate(self, k, on_progress, on_done):
        """Cross-validate the current settings on the training data: k fresh trainings, in the background."""
        from quantumscope.gui.background import Run
        from quantumscope.ml import evaluation as E
        p = getattr(self, 'prepared', None) or self.data.prepared()
        if p is None:
            on_done(None, 'no data')
            return None
        options = self._options()
        make = lambda: self._new_model(p)                         # noqa: E731

        def work(report, cancelled):
            folds = E.stratified_folds(p.y_train, k, seed=self.seed.value())
            return E.cross_validate_variational(p.X_train, p.y_train, make, folds, options,
                                                progress=lambda d, t: report((d, t)), cancelled=cancelled)
        return Run(work, owner=self, task='Cross-validation', on_progress=on_progress, on_done=on_done,
                   on_error=lambda exc, details: on_done(None, exc)).start()

    def _use_loaded(self, model):
        """Match the controls to a loaded model, so they describe it (and Train would rebuild it)."""
        s = model.settings
        self.feature_map.setCurrentIndex(self.feature_map.findData(s['feature_map']))
        self.layers.setValue(int(s['layers']))
        at = self.loss_box.findData(s.get('loss', 'mse'))
        if at >= 0:
            self.loss_box.setCurrentIndex(at)
        if s.get('optimizer'):
            at = self.method.findData(s['optimizer'])
            if at >= 0:
                self.method.setCurrentIndex(at)
        self.data.show_model_data(model)

    def _failed(self, exc, details):
        self.train_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.result.setText(f'Training failed: {exc}')

    def _trained(self, r, settings, plane):
        self.train_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.model, p = r['model'], self.prepared
        losses = [h[0] for h in self._history] or [float('nan')]
        accuracies = [h[1] for h in self._history] or [0.0]
        early = (f' Early stopping kept step {r["best_step"]}, the best on the validation data.'
                 if r.get('stopped_early') else '')
        many = '' if p.k == 2 else (f' {p.k} classes read from {self.model.readout} qubits, with cross-entropy '
                                    f'(chance is about {1 / p.k:.0%}).')
        self.result.setText(f'{"Stopped" if r["stopped"] else "Done"} after {len(self._history) - 1} steps: training '
                            f'accuracy {accuracies[-1]:.0%}, test accuracy {r["test"]:.0%}, final loss {losses[-1]:.4f}.'
                            + early + many)
        self.evaluation.show_results(p.y_test, r['decision_test'], p.classes)
        draw_regions(self.regions, plane, r['f'], p.X_train, p.y_train, p.X_test, p.y_test, r['predicted'], p.k,
                     p.classes)
        self.open_circuit.setEnabled(True)
        self.last = dict(train=accuracies[-1], test=r['test'], history=list(self._history), stopped=r['stopped'])
        r.update(self.last)
        from quantumscope.ml import models as M
        self.model_panel.set_model(M.from_variational(self.model, p, settings, accuracies[-1], r['test'],
                                                      settings['dataset']))
        from quantumscope.ml import progress
        progress.trained('variational', train=accuracies[-1], test=r['test'], map=settings['map'],
                         layers=settings['layers'], dataset=settings['dataset'], classes=p.k)

    def _draw(self):
        p, model = self.prepared, self.model
        _regions(self.regions, model.decision, p.X_train, p.y_train, p.X_test, p.y_test, model.predict(p.X_test), p.k,
                 p.classes)

    def open_in_circuit(self):
        """Load the trained circuit for the first test point into the circuit simulator."""
        if self.model is None:
            return None
        window = self.window()
        workspace = getattr(window, 'circuit_widget', None)
        if workspace is None:
            return None
        x = self.prepared.X_test[0]
        if isinstance(self.model, V.MultiClassifier):            # measure the readout qubits: outcome c is class c
            r, p = self.model.readout, self.prepared
            names = ', '.join(f'{c:0{r}b} = {name}' for c, name in enumerate(p.classes))
            workspace.show_generated_circuit(self.model.qubits, self.model.gates(x), '',
                                             f'The trained circuit for test sample 1 (true class {p.label_name(p.y_test[0])}). '
                                             f'Measure q0…q{r - 1}: {names}. Unused outcomes are discarded.',
                                             measured=tuple(range(r)))
        else:
            workspace.set_circuit(self.model.qubits, self.model.gates(x))
            workspace.model.set_observable('Z0')
            workspace._changed()
        launch = getattr(window, '_launch_circuits', None)
        if callable(launch):
            launch()
        return x
