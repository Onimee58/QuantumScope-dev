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
    plot.setMinimumHeight(220)
    for side in ('left', 'bottom'):                            # plain numbers: no automatic "×0.001"
        plot.getAxis(side).enableAutoSIPrefix(False)
    return plot


def _scatter_points(plot, X, y, size=8, symbol='o', outline=None):
    import pyqtgraph as pg
    for label, colour in zip((1, -1), CLASS_COLOURS):
        chosen = y == label
        plot.addItem(pg.ScatterPlotItem(X[chosen, 0], X[chosen, 1], size=size, symbol=symbol,
                                        brush=pg.mkBrush(colour), pen=pg.mkPen(outline or '#0b1420', width=1)))


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
        size = min(row_h - 6, (self.width() - 90) / max(len(r[1]) for r in self.rows) - 4)
        for r, (name, images) in enumerate(self.rows):
            y = 4 + r * row_h
            p.setPen(QColor('#d8e6f3'))
            p.setFont(QFont('Sans', 10, QFont.Weight.Bold))
            p.drawText(QRectF(0, y, 80, row_h), Qt.AlignmentFlag.AlignCenter, f'class {name}')
            for k, image in enumerate(images):
                top = max(1e-9, float(image.max()))
                pixels = (255 * (image / top)).astype(np.uint8).copy()
                qimage = QImage(pixels.data, pixels.shape[1], pixels.shape[0], pixels.shape[1],
                                QImage.Format.Format_Grayscale8)
                p.drawImage(QRectF(86 + k * (size + 4), y + (row_h - size) / 2, size, size), qimage)
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

    def __init__(self, parent=None):
        super().__init__(parent)
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
        sv.addRow('Dataset', self.source)
        self.import_button = QPushButton('Import CSV or .npz…')
        self.import_button.setToolTip('Your own data: a label column (named label, target, class … or the last '
                                      'column) and numeric or text features')
        sv.addRow(self.import_button)
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
        pair.addWidget(QLabel('vs'))
        pair.addWidget(self.class_b)
        rv.addRow('Classes', pair)
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
        root.addWidget(_scrolling(left, form))
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
        self.prepare_button.clicked.connect(self.prepare)
        self._load_source()

    def _load_source(self, *_):
        self.source_key = self.source.currentData()          # a built-in or synthetic key
        self.use(D.load(self.source_key))

    def import_file(self, path=None):
        if not path:
            path, _ = QFileDialog.getOpenFileName(self, 'Import data', '', 'Data (*.csv *.npz *.txt)')
            if not path:
                return None
        try:
            dataset = D.import_file(path)
        except (OSError, ValueError, UnicodeDecodeError) as exc:
            QMessageBox.warning(self, 'Import data', f'This file could not be read:\n{exc}')
            return None
        self.source_key = 'imported'
        self.use(dataset)
        return dataset

    def use(self, dataset):
        self.dataset = dataset
        for box in (self.class_a, self.class_b):
            box.blockSignals(True)
            box.clear()
            for k, name in enumerate(dataset.classes):
                box.addItem(f'{name} ({int(dataset.counts[k])})', k)
            box.blockSignals(False)
        self._check()

    def _check(self, *_):
        """Run the checker and fill in its suggested recipe."""
        verdict, findings, recipe = D.check(self.dataset, qubits=self.qubits.value())
        self.recipe = recipe
        colour = {'ready': '#5ad48a', 'preprocess': '#ffba50', 'stop': '#ff7a7a'}[verdict]
        text = {'ready': 'Ready: this data fits as it is.', 'preprocess': 'Usable after preprocessing (suggested below).',
                'stop': 'Cannot be used.'}[verdict]
        self.verdict.setText(f'<span style="color:{colour}">{text}</span>')
        icon = {'ok': '✓', 'fix': '⚠', 'stop': '✗'}
        self.findings.setText('<br>'.join(f'{icon[f.level]} {f.message}' + (f' <i>{f.suggestion}</i>' if f.suggestion else '')
                                          for f in findings))
        self.class_a.setCurrentIndex(self.class_a.findData(recipe.classes[0]))
        self.class_b.setCurrentIndex(self.class_b.findData(recipe.classes[1]))
        self.missing.setCurrentIndex(self.missing.findData(recipe.missing))
        self.text.setCurrentIndex(self.text.findData(recipe.text))
        self.per_class.setValue(recipe.per_class)
        self.components.setValue(recipe.components)
        self.prepare_button.setEnabled(verdict != 'stop')
        self.images.show_images(self.dataset, recipe.classes)
        if verdict != 'stop':
            self.prepare()

    def current_recipe(self):
        a, b = self.class_a.currentData(), self.class_b.currentData()
        return D.Recipe(classes=(a, b), missing=self.missing.currentData(), text=self.text.currentData(),
                        per_class=self.per_class.value(), components=self.components.value(),
                        scale='pi' if self.scale.isChecked() else 'none', test_fraction=self.test_fraction.value())

    def prepare(self):
        recipe = self.current_recipe()
        if recipe.classes[0] == recipe.classes[1]:
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
        self.plot.clear()
        if prepared.X_train.shape[1] >= 2:
            _scatter_points(self.plot, prepared.X_train[:, :2], prepared.y_train)
            self.plot.setLabel('bottom', prepared.features[0])
            self.plot.setLabel('left', prepared.features[1])
        self.images.show_images(self.dataset, recipe.classes)
        return prepared


# ============================================================================================
class _DataPicker(QGroupBox):
    """Which data a classifier trains on: from the Datasets tab, or a dataset with its suggested recipe."""

    def __init__(self, max_samples, parent=None):
        super().__init__('Data', parent)
        self.max_samples = max_samples
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
        pair.addWidget(QLabel('vs'))
        pair.addWidget(self.class_b)
        self.class_label = QLabel('Classes')
        form.addRow(self.class_label, self.class_row)
        self.summary = QLabel()
        self.summary.setWordWrap(True)
        self.summary.setObjectName('muted')
        form.addRow(self.summary)
        self.source.currentIndexChanged.connect(self._classes_for_source)
        self.source.currentIndexChanged.connect(self._sync)
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
            for k, name in enumerate(dataset.classes):
                box.addItem(name, k)
            box.setCurrentIndex(box.findData(default))
            box.blockSignals(False)

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
                self.summary.setText(f'Prepared in the Datasets tab: {STORE.prepared.X_train.shape[1]} features '
                                     f'on as many qubits.')
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
            self.dataset = STORE.dataset
        else:
            dataset = D.load(key)
            verdict, _, recipe = D.check(dataset, qubits=self.qubits.value(), max_samples=self.max_samples)
            if verdict == 'stop':
                self.summary.setText('This dataset cannot be used.')
                return None
            if self.class_row.isVisible() or len(dataset.classes) > 2:
                a, b = self.class_a.currentData(), self.class_b.currentData()
                if a is not None and b is not None:
                    if a == b:
                        self.summary.setText('Choose two different classes.')
                        return None
                    recipe.classes = (a, b)
            p = D.prepare(dataset, recipe)
            self.dataset = dataset
        self.summary.setText(f'{p.classes[0]} (+1) vs {p.classes[1]} (−1): {len(p.y_train)} for training, '
                             f'{len(p.y_test)} for testing, {p.X_train.shape[1]} features on {p.X_train.shape[1]} qubits.')
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
    """The decision function on the plane's grid, as res × res (rows: y). No Qt: safe in a worker."""
    grid = plane['grid']
    values = np.concatenate([decision(chunk) for chunk in np.array_split(grid, max(1, len(grid) // 1500))])
    return values.reshape(plane['res'], plane['res'])


def draw_regions(plot, plane, f, X_train, y_train, X_test=None, y_test=None, predicted=None):
    """Draw decision regions (f from region_values, or None for points only) on the interface thread."""
    import pyqtgraph as pg
    plot.clear()
    plot.setLabel('bottom', plane['labels'][0])
    plot.setLabel('left', plane['labels'][1])
    plot.setTitle(plane['title'])
    lo, hi, to_plane = plane['lo'], plane['hi'], plane['to_plane']
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
    _scatter_points(plot, to_plane(X_train), y_train, size=7)
    if X_test is not None and len(X_test):
        P_test = to_plane(X_test)
        wrong = predicted != y_test
        _scatter_points(plot, P_test[~wrong], y_test[~wrong], size=11, symbol='t', outline='#ffffff')
        if wrong.any():
            plot.addItem(pg.ScatterPlotItem(P_test[wrong, 0], P_test[wrong, 1], size=14, symbol='x',
                                            brush=pg.mkBrush('#ff4d4d'), pen=pg.mkPen('#ff4d4d', width=2)))
    plot.disableAutoRange()
    plot.setRange(xRange=(lo[0], hi[0]), yRange=(lo[1], hi[1]), padding=0)


def _regions(plot, decision, X_train, y_train, X_test=None, y_test=None, predicted=None):
    """Compute and draw in one go (on the interface thread), for quick, small cases."""
    plane = region_plane(X_train, X_test)
    draw_regions(plot, plane, None if decision is None else region_values(decision, plane),
                 X_train, y_train, X_test, y_test, predicted)


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
        self.data = _DataPicker(max_samples=200)
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
        root.addWidget(_scrolling(left, form))
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
            report('Training the classifier…')
            if settings['method'] == 'svm':
                model = K.SVM(C=settings['strength']).fit(Ktr, p.y_train)
            else:
                model = K.KernelRidge(settings['strength']).fit(Ktr, p.y_train)
            predicted = model.predict(Kte)
            if cancelled():
                return None
            report('Drawing the decision regions…')

            def decision(points):
                return model.decision(K.kernel(points, p.X_train, kind=kind, reps=reps, bandwidth=bandwidth))
            f = region_values(decision, plane)
            order = np.argsort(-p.y_train, kind='stable')
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
        self.run = Run(work, on_progress=self.result.setText, owner=self,
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
        for which, coords, labels, symbol, size in (('train', r['map_train'], p.y_train, 'o', 8),
                                                    ('test', r['map_test'], p.y_test, 't', 11)):
            for label, colour in zip((1, -1), CLASS_COLOURS):
                chosen = np.flatnonzero(labels == label)
                if not len(chosen):
                    continue
                spots = pg.ScatterPlotItem(coords[chosen, 0], coords[chosen, 1], size=size, symbol=symbol,
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
        predicted = p.classes[0] if value >= 0 else p.classes[1]
        truth = p.classes[0] if (p.y_train if which == 'train' else p.y_test)[index] == 1 else p.classes[1]
        lines = [f'true class {truth}', f'predicted {predicted}' + ('' if predicted == truth else ' ✗'),
                 f'decision {value:+.3f}']
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
        name = lambda k: p.classes[0] if p.y_train[k] == 1 else p.classes[1]      # noqa: E731
        self.heatmap.setToolTip(f'K = {value:.3f} between training samples {a + 1} ({name(a)}) and {b + 1} ({name(b)})'
                                '\nClick to see both.')

    def _heat_click(self, event):
        cell = self._heat_cell(event.scenePos())
        if cell is None:
            return
        a, b, value = cell
        self.sample_view.show_samples([self.sample_entry('train', a), self.sample_entry('train', b)],
                                      f'Kernel value K = {value:.3f}')

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
        noise = '' if not settings['shots'] else (f' Kernel estimated from {settings["shots"]} shots per entry '
                                                 f'(typical error {r["error"]:.3f}).')
        hint = '' if r['off'] >= 0.05 else (f' The kernel is close to 0 for different points (average {r["off"]:.3f}): '
                                            f'kernel concentration, common for entangling maps on many qubits. '
                                            f'Try a smaller bandwidth.')
        self.result.setText(f'Training accuracy {r["train"]:.0%}, test accuracy {r["test"]:.0%}{extra}.{noise}{hint}')
        draw_regions(self.regions, plane, r['f'], p.X_train, p.y_train, p.X_test, p.y_test, r['predicted'])
        self.heatmap.clear()
        image = pg.ImageItem(r['heat'])
        image.setLookupTable(pg.colormap.get('viridis').getLookupTable(0, 1, 256))
        image.setLevels((0, 1))
        self.heatmap.addItem(image)
        size = len(r['heat'])
        self.heatmap.setAspectLocked(False)                      # fill the panel
        self.heatmap.disableAutoRange()
        self.heatmap.setRange(xRange=(0, size), yRange=(0, size), padding=0)
        split = int((p.y_train == 1).sum())                      # the class border, as thin lines
        for line in (pg.InfiniteLine(split, angle=90, pen=pg.mkPen('#ffffff', width=1, style=Qt.PenStyle.DashLine)),
                     pg.InfiniteLine(split, angle=0, pen=pg.mkPen('#ffffff', width=1, style=Qt.PenStyle.DashLine))):
            line.setZValue(10)                                   # above the image
            self.heatmap.addItem(line)
        self.last = r
        self.dataset = self.data.dataset
        self._draw_kernel_map(r)
        from quantumscope.ml import models as M
        trained = M.from_kernel(r['model'], p, settings, r['train'], r['test'], settings['dataset'])
        self.model_panel.set_model(trained)
        self.view3d.set_result(r, trained)
        from quantumscope.ml import progress
        progress.trained('kernel', train=r['train'], test=r['test'], map=settings['kind'],
                         bandwidth=settings['bandwidth'], shots=settings['shots'], dataset=settings['dataset'])


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
        self.data = _DataPicker(max_samples=300)
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
        mv.addRow('Optimizer', self.method)
        self.steps = QSpinBox()
        self.steps.setRange(5, 1000)
        self.steps.setValue(80)
        mv.addRow('Steps', self.steps)
        self.seed = QSpinBox()
        self.seed.setRange(0, 9999)
        mv.addRow('Starting point (seed)', self.seed)
        buttons = QHBoxLayout()
        self.train_button, self.stop_button = QPushButton('Train'), QPushButton('Stop')
        self.stop_button.setEnabled(False)
        buttons.addWidget(self.train_button)
        buttons.addWidget(self.stop_button)
        mv.addRow(buttons)
        self.open_circuit = QPushButton('Open in circuit simulator')
        self.open_circuit.setToolTip('The trained circuit for the first test point, with the observable Z0')
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
        root.addWidget(_scrolling(left, form))
        right = QVBoxLayout()
        self.regions = _plot('Decision regions')
        right.addWidget(self.regions, 3)
        self.curve = _plot('Training', 'step', 'loss / accuracy')
        self.curve.addLegend(offset=(8, 4))
        self.loss_line = self.curve.plot(pen='#5ae6ff', name='loss')
        self.acc_line = self.curve.plot(pen='#5ad48a', name='training accuracy')
        right.addWidget(self.curve, 2)
        root.addLayout(right, 1)
        self.model = None
        self.train_button.clicked.connect(self.train)
        self.stop_button.clicked.connect(lambda: self.run.cancel() if getattr(self, 'run', None) else None)
        self.open_circuit.clicked.connect(self.open_in_circuit)

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
        self.prepared = p
        model = V.Classifier(p.X_train.shape[1], layers=self.layers.value(),
                             feature_map=self.feature_map.currentData(), seed=self.seed.value())
        settings = dict(method=self.method.currentData(), steps=self.steps.value(), layers=self.layers.value(),
                        map=self.feature_map.currentData(), dataset=self.data.key())
        plane = region_plane(p.X_train, p.X_test)
        self._history = []

        def work(report, cancelled):                              # the worker: no widgets here
            def step(index, loss, accuracy):
                regions = None
                if index % 5 == 0:                                # fresh regions now and then
                    regions = (region_values(model.decision, plane), model.predict(p.X_test))
                report((index, loss, accuracy, regions))
                return not cancelled()
            model.train(p.X_train, p.y_train, method=settings['method'], steps=settings['steps'], callback=step)
            predicted = model.predict(p.X_test)
            return dict(model=model, predicted=predicted, test=float(np.mean(predicted == p.y_test)),
                        f=region_values(model.decision, plane), stopped=cancelled())

        self.train_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.open_circuit.setEnabled(False)
        self.result.setText('Starting…')
        from quantumscope.gui.background import Run
        self.run = Run(work, owner=self, on_progress=lambda v: self._step(v, plane),
                       on_done=lambda r: self._trained(r, settings, plane), on_error=self._failed).start()
        return self.run

    def _step(self, value, plane):
        index, loss, accuracy, regions = value
        self._history.append((loss, accuracy))
        steps = list(range(len(self._history)))
        self.loss_line.setData(steps, [h[0] for h in self._history])
        self.acc_line.setData(steps, [h[1] for h in self._history])
        self.result.setText(f'Step {index}: loss {loss:.4f}, training accuracy {accuracy:.0%}')
        if regions is not None:
            p = self.prepared
            draw_regions(self.regions, plane, regions[0], p.X_train, p.y_train, p.X_test, p.y_test, regions[1])

    def _use_loaded(self, model):
        """Match the controls to a loaded model, so they describe it (and Train would rebuild it)."""
        s = model.settings
        self.feature_map.setCurrentIndex(self.feature_map.findData(s['feature_map']))
        self.layers.setValue(int(s['layers']))
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
        self.result.setText(f'{"Stopped" if r["stopped"] else "Done"} after {len(self._history) - 1} steps: training '
                            f'accuracy {accuracies[-1]:.0%}, test accuracy {r["test"]:.0%}, final loss {losses[-1]:.4f}.')
        draw_regions(self.regions, plane, r['f'], p.X_train, p.y_train, p.X_test, p.y_test, r['predicted'])
        self.open_circuit.setEnabled(True)
        self.last = dict(train=accuracies[-1], test=r['test'], history=list(self._history), stopped=r['stopped'])
        r.update(self.last)
        from quantumscope.ml import models as M
        self.model_panel.set_model(M.from_variational(self.model, p, settings, accuracies[-1], r['test'],
                                                      settings['dataset']))
        from quantumscope.ml import progress
        progress.trained('variational', train=accuracies[-1], test=r['test'], map=settings['map'],
                         layers=settings['layers'], dataset=settings['dataset'])

    def _draw(self):
        p, model = self.prepared, self.model
        _regions(self.regions, model.decision, p.X_train, p.y_train, p.X_test, p.y_test, model.predict(p.X_test))

    def open_in_circuit(self):
        """Load the trained circuit for the first test point into the circuit simulator."""
        if self.model is None:
            return None
        window = self.window()
        workspace = getattr(window, 'circuit_widget', None)
        if workspace is None:
            return None
        x = self.prepared.X_test[0]
        workspace.set_circuit(self.model.qubits, self.model.gates(x))
        workspace.model.set_observable('Z0')
        workspace._changed()
        launch = getattr(window, '_launch_circuits', None)
        if callable(launch):
            launch()
        return x
