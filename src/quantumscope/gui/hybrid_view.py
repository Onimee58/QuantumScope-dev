"""Hybrid QNN (v1.1.0): build a classical–quantum neural network layer by layer, train it, and
compare it with its classical twin.

The network is a list: convolutions, pooling, dropout, batch normalisation, dense layers, and
quantum layers, ending in an output layer with one unit per class. Shapes and parameter counts are
checked as it is built, and a layer that does not fit says what to change. Training runs in the
background (Adam, mini-batches), with live curves; the classical twin, the same network with each
quantum layer replaced by a dense layer of the same width, trains on the same data for comparison.
"""
import math

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout,
                               QLabel, QListWidget, QListWidgetItem, QMenu, QMessageBox, QPushButton, QSpinBox,
                               QTabWidget, QTableWidget, QTableWidgetItem, QToolButton, QVBoxLayout, QWidget)

from quantumscope.ml import datasets as D
from quantumscope.ml import hybrid as H

INPUTS = (('auto', 'As it is (images as images)'), ('features', 'Features (a vector)'),
          ('sequence', 'A sequence (for Conv1D)'))
CHOICES = {'activation': H.ACTIVATIONS, 'padding': ('valid', 'same'), 'entanglement': ('ring', 'line', 'none')}
NUMBERS = {'units': (1, 512), 'filters': (1, 128), 'kernel': (1, 9), 'stride': (1, 4), 'size': (2, 8),
           'qubits': (1, H.MAX_QUBITS), 'layers': (1, 10)}
LABELS = {'units': 'Units', 'filters': 'Filters', 'kernel': 'Kernel size', 'stride': 'Stride', 'padding': 'Padding',
          'activation': 'Activation', 'size': 'Pool size', 'rate': 'Rate', 'qubits': 'Qubits',
          'layers': 'Quantum layers', 'entanglement': 'Entanglement', 'scale': 'Angle scale'}
TIPS = {'qubits': 'One input number per qubit: the layer before must give exactly this many',
        'layers': 'Repetitions of (RY and RZ on every qubit, then the entangling CNOTs)',
        'scale': 'Each input x becomes the angle scale·x of an RY rotation (π: inputs in [−1, 1] cover a full turn)',
        'rate': 'The share of values set to zero at random during training (none at prediction)',
        'padding': '"same" keeps the size, padding the borders with zeros; "valid" shrinks it'}


class HybridExperiment(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        from quantumscope.gui.qml_experiments import OWN_FILE, _plot, _scrolling, _source_combo
        self.specs, self.dataset, self.imported, self.data, self.network, self.run = [], None, None, None, None, None
        root = QHBoxLayout(self)
        left = QWidget()
        left.setMaximumWidth(420)
        form = QVBoxLayout(left)
        title = QLabel('HYBRID QNN  ·  build a classical–quantum neural network, train it, compare it')
        title.setStyleSheet('font-weight:700;')
        title.setWordWrap(True)
        form.addWidget(title)

        data = QGroupBox('Data')
        dv = QFormLayout(data)
        self.source = _source_combo()
        self.source.insertItem(0, OWN_FILE, 'imported')
        self.source.insertSeparator(1)
        self.source.setCurrentIndex(self.source.findData('digits'))
        dv.addRow('Dataset', self.source)
        self.choose_file = QPushButton('Choose the file…')
        self.choose_file.setEnabled(False)
        dv.addRow(self.choose_file)
        self.input_as = QComboBox()
        for key, label in INPUTS:
            self.input_as.addItem(label, key)
        self.input_as.setToolTip('How each sample enters the network: images keep their height × width; '
                                 'features can also be read as a sequence, for 1-D convolutions')
        dv.addRow('Input', self.input_as)
        self.per_class = QSpinBox()
        self.per_class.setRange(0, 5000)
        self.per_class.setValue(150)
        self.per_class.setSpecialValueText('all')
        self.per_class.setToolTip('Samples of each class to use: fewer train faster')
        dv.addRow('Samples per class', self.per_class)
        self.test_share = QDoubleSpinBox()
        self.test_share.setRange(0.1, 0.5)
        self.test_share.setSingleStep(0.05)
        self.test_share.setValue(0.25)
        dv.addRow('Test share', self.test_share)
        self.seed = QSpinBox()
        self.seed.setRange(0, 9999)
        dv.addRow('Seed', self.seed)
        self.data_label = QLabel()
        self.data_label.setWordWrap(True)
        self.data_label.setObjectName('muted')
        dv.addRow(self.data_label)
        form.addWidget(data)

        net = QGroupBox('Network')
        nv = QVBoxLayout(net)
        row = QHBoxLayout()
        self.preset = QComboBox()
        for key, label in H.PRESETS:
            self.preset.addItem(label, key)
        row.addWidget(self.preset, 1)
        self.use_preset = QPushButton('Use')
        self.use_preset.setToolTip('Replace the layers with this ready-made network')
        row.addWidget(self.use_preset)
        nv.addLayout(row)
        self.layer_list = QListWidget()
        self.layer_list.setMinimumHeight(230)
        nv.addWidget(self.layer_list)
        buttons = QHBoxLayout()
        self.add_button = QToolButton()
        self.add_button.setText('Add layer ▾')
        self.add_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        menu = QMenu(self.add_button)
        for kind, (name, _) in H.LAYERS.items():
            menu.addAction(name, lambda k=kind: self.add_layer(k))
        self.add_button.setMenu(menu)
        buttons.addWidget(self.add_button)
        self.remove_button, self.up_button, self.down_button = QPushButton('Remove'), QPushButton('↑'), QPushButton('↓')
        self.up_button.setToolTip('Move the layer up')
        self.down_button.setToolTip('Move the layer down')
        for b in (self.remove_button, self.up_button, self.down_button):
            buttons.addWidget(b)
        nv.addLayout(buttons)
        self.layer_box = QGroupBox('Layer')
        self.layer_form = QFormLayout(self.layer_box)
        nv.addWidget(self.layer_box)
        self.check_label = QLabel()
        self.check_label.setWordWrap(True)
        nv.addWidget(self.check_label)
        form.addWidget(net)

        train = QGroupBox('Training')
        tv = QFormLayout(train)
        self.epochs = QSpinBox()
        self.epochs.setRange(1, 500)
        self.epochs.setValue(15)
        tv.addRow('Epochs', self.epochs)
        self.batch = QSpinBox()
        self.batch.setRange(1, 1024)
        self.batch.setValue(32)
        tv.addRow('Batch size', self.batch)
        self.rate = QDoubleSpinBox()
        self.rate.setRange(0.0001, 0.5)
        self.rate.setDecimals(4)
        self.rate.setSingleStep(0.001)
        self.rate.setValue(0.01)
        self.rate.setToolTip('Adam\'s learning rate')
        tv.addRow('Learning rate', self.rate)
        self.twin = QCheckBox('Also train the classical twin')
        self.twin.setChecked(True)
        self.twin.setToolTip('The same network with each quantum layer replaced by a dense layer of the same width '
                             '(tanh), trained on the same data: an honest comparison')
        tv.addRow(self.twin)
        row = QHBoxLayout()
        self.train_button, self.stop_button = QPushButton('Train'), QPushButton('Stop')
        self.stop_button.setEnabled(False)
        row.addWidget(self.train_button)
        row.addWidget(self.stop_button)
        tv.addRow(row)
        self.status = QLabel()
        self.status.setWordWrap(True)
        tv.addRow(self.status)
        form.addWidget(train)
        form.addStretch()
        from quantumscope.gui.side_panel import CollapsiblePanel
        root.addWidget(CollapsiblePanel(_scrolling(left, form), 'Network and training', 'qml-hybrid'))

        right = QVBoxLayout()
        import pyqtgraph as pg
        self.curve = _plot('Training', 'epoch', 'loss / accuracy')
        self.curve.addLegend(offset=(10, 10))
        dash = Qt.PenStyle.DashLine
        self.lines = {
            ('hybrid', 'loss'): self.curve.plot(pen='#5ae6ff', name='hybrid: training loss'),
            ('hybrid', 'val'): self.curve.plot(pen='#5ad48a', name='hybrid: test accuracy'),
            ('twin', 'loss'): self.curve.plot(pen=pg.mkPen('#5ae6ff', style=dash), name='classical twin: training loss'),
            ('twin', 'val'): self.curve.plot(pen=pg.mkPen('#5ad48a', style=dash), name='classical twin: test accuracy')}
        right.addWidget(self.curve, 3)
        self.tabs = QTabWidget()
        self.results = QLabel('Build a network and press Train.')
        self.results.setWordWrap(True)
        self.results.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.results.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        holder = QWidget()
        QVBoxLayout(holder).addWidget(self.results)
        self.tabs.addTab(holder, 'Results')
        self.summary = QTableWidget(0, 3)
        self.summary.setHorizontalHeaderLabels(['Layer', 'Output shape', 'Parameters'])
        self.summary.horizontalHeader().setStretchLastSection(True)
        self.summary.verticalHeader().setVisible(False)
        self.summary.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabs.addTab(self.summary, 'Network')
        self.confusion_plot = _plot('Confusion matrix (test data, hybrid)', 'predicted', 'true')
        self.tabs.addTab(self.confusion_plot, 'Confusion matrix')
        right.addWidget(self.tabs, 2)
        root.addLayout(right, 1)

        self.source.currentIndexChanged.connect(self._source_changed)
        self.choose_file.clicked.connect(lambda: self.import_file())
        for w in (self.input_as, self.per_class, self.test_share, self.seed):
            (w.currentIndexChanged if isinstance(w, QComboBox) else w.valueChanged).connect(lambda *_: self._prepare())
        self.use_preset.clicked.connect(lambda: self.use(self.preset.currentData()))
        self.layer_list.currentRowChanged.connect(self._show_layer)
        self.remove_button.clicked.connect(self.remove_layer)
        self.up_button.clicked.connect(lambda: self.move_layer(-1))
        self.down_button.clicked.connect(lambda: self.move_layer(1))
        self.train_button.clicked.connect(lambda: self.train())
        self.stop_button.clicked.connect(lambda: self.run.cancel() if self.run else None)
        self._source_changed()
        self.use('cnn')

    # ---- data ------------------------------------------------------------------------------------
    def _source_changed(self, *_):
        key = self.source.currentData()
        self.choose_file.setEnabled(key == 'imported')
        if key == 'imported':
            if self.imported is None and self.import_file() is None:
                self.source.blockSignals(True)
                self.source.setCurrentIndex(self.source.findData(getattr(self, '_last_key', 'digits')))
                self.source.blockSignals(False)
                self.choose_file.setEnabled(False)
                return
            self.dataset = self.imported
        else:
            self.dataset = D.load(key)
            self._last_key = key
        self._prepare()

    def import_file(self, path=None):
        """Your own data: a .csv (with the preview, to choose the label) or a .npz; None if cancelled."""
        if path is None:
            path, _ = QFileDialog.getOpenFileName(self, 'Your own data', '', 'Data (*.csv *.npz *.txt)')
            if not path:
                return None
        try:
            if path.lower().endswith(('.csv', '.txt')):
                from quantumscope.gui.import_dialog import ImportDialog
                dialog = ImportDialog(path, self)
                if not dialog.exec():
                    return None
                dataset = dialog.dataset
            else:
                dataset = D.import_file(path)
        except (OSError, ValueError, UnicodeDecodeError) as exc:
            QMessageBox.warning(self, 'Your own data', f'This file could not be read:\n{exc}')
            return None
        self.imported = self.dataset = dataset
        index = self.source.findData('imported')
        self.source.setItemText(index, f'Your file: {dataset.name}')
        self.source.blockSignals(True)
        self.source.setCurrentIndex(index)
        self.source.blockSignals(False)
        self.choose_file.setEnabled(True)
        self._prepare()
        return dataset

    def _prepare(self):
        if self.dataset is None:
            return
        shape = self.input_as.currentData()
        if shape == 'features' and self.dataset.image_shape is not None:
            shape = 'features'
        try:
            self.data = H.prepare(self.dataset, shape=shape, per_class=self.per_class.value() or None,
                                  test_fraction=self.test_share.value(), seed=self.seed.value())
        except ValueError as exc:
            self.data = None
            self.data_label.setText(f'Cannot use this data: {exc}')
            return
        d = self.data
        self.data_label.setText(f'{len(d.y_train)} training and {len(d.y_test)} test samples · {len(d.classes)} '
                                f'classes · {d.note} · each sample {H._shape(d.input_shape)}')
        self._check()

    # ---- the network -----------------------------------------------------------------------------
    def use(self, preset):
        shape = self.data.input_shape if self.data is not None else (8, 8, 1)
        self.specs = H.preset(preset, shape)
        self._refresh(select=0)

    def add_layer(self, kind):
        row = self.layer_list.currentRow()
        at = len(self.specs) if row < 0 or row >= len(self.specs) else row + 1
        self.specs.insert(at, dict({'type': kind}, **H.LAYERS[kind][1]))
        self._refresh(select=at)

    def remove_layer(self):
        row = self.layer_list.currentRow()
        if 0 <= row < len(self.specs):
            del self.specs[row]
            self._refresh(select=min(row, len(self.specs) - 1))

    def move_layer(self, step):
        row = self.layer_list.currentRow()
        to = row + step
        if 0 <= row < len(self.specs) and 0 <= to < len(self.specs):
            self.specs[row], self.specs[to] = self.specs[to], self.specs[row]
            self._refresh(select=to)

    def _refresh(self, select=None):
        """The list, with each layer's output shape, and the check."""
        self.layer_list.blockSignals(True)
        self.layer_list.clear()
        shapes = self._check()
        for n, spec in enumerate(self.specs):
            layer = H.make_layer(spec)
            shape = f'  →  {H._shape(shapes[n])}' if shapes and n < len(shapes) else ''
            item = QListWidgetItem(f'{n + 1}. {layer.short()}{shape}')
            item.setToolTip(layer.describe())
            if spec['type'] == 'quantum':
                item.setForeground(Qt.GlobalColor.cyan)
            self.layer_list.addItem(item)
        classes = len(self.data.classes) if self.data is not None else '…'
        out = QListWidgetItem(f'Output: dense, {classes} classes, softmax (always last)')
        out.setFlags(Qt.ItemFlag.NoItemFlags)
        self.layer_list.addItem(out)
        self.layer_list.blockSignals(False)
        if select is not None and self.specs:
            self.layer_list.setCurrentRow(max(0, select))
        self._show_layer(self.layer_list.currentRow())

    def _check(self):
        """Build the network to check it; shows the result and returns each layer's output shape."""
        if self.data is None:
            return None
        try:
            net = H.Network(self.data.input_shape, self.specs, len(self.data.classes), seed=self.seed.value())
        except H.ShapeError as exc:
            self.check_label.setStyleSheet('color: #e8a33d;')
            self.check_label.setText(str(exc))
            self.train_button.setEnabled(False)
            self.network_shapes = None
            return None
        classical, quantum = net.counts()
        qubits = [s['qubits'] for s in self.specs if s['type'] == 'quantum']
        self.check_label.setStyleSheet('')
        self.check_label.setObjectName('muted')
        self.check_label.setText(f'{classical:,} classical and {quantum} quantum parameters'
                                 + (f' · {" + ".join(map(str, qubits))} qubits' if qubits else
                                    ' · no quantum layer yet: add one to make it hybrid'))
        self.train_button.setEnabled(self.run is None)
        self._summary(net)
        self.network_shapes = net.shapes[1:]
        return self.network_shapes

    def _summary(self, net):
        rows = net.summary()
        self.summary.setRowCount(len(rows))
        for r, (name, shape, size) in enumerate(rows):
            for c, text in enumerate((name, H._shape(shape), f'{size:,}')):
                self.summary.setItem(r, c, QTableWidgetItem(text))
        self.summary.resizeColumnsToContents()

    def _show_layer(self, row):
        while self.layer_form.rowCount():
            self.layer_form.removeRow(0)
        valid = 0 <= row < len(self.specs)
        for b in (self.remove_button, self.up_button, self.down_button):
            b.setEnabled(valid)
        if not valid:
            self.layer_box.setTitle('Layer')
            self.layer_form.addRow(QLabel('Choose a layer in the list to change it.'))
            return
        spec = self.specs[row]
        self.layer_box.setTitle(f'Layer {row + 1}: {H.LAYERS[spec["type"]][0]}')
        settings = [k for k in spec if k != 'type']
        if not settings:
            self.layer_form.addRow(QLabel('This layer has no settings.'))
        for key in settings:
            self.layer_form.addRow(LABELS.get(key, key), self._editor(row, key, spec[key]))

    def _editor(self, row, key, value):
        def store(v):
            self.specs[row][key] = v
            self._refresh(select=row)
        if key in CHOICES:
            w = QComboBox()
            for choice in CHOICES[key]:
                w.addItem(choice.replace('_', ' '), choice)
            w.setCurrentIndex(max(0, w.findData(value)))
            w.currentIndexChanged.connect(lambda *_: store(w.currentData()))
        elif key in NUMBERS:
            w = QSpinBox()
            w.setRange(*NUMBERS[key])
            w.setValue(int(value))
            w.editingFinished.connect(lambda: store(w.value()) if w.value() != self.specs[row][key] else None)
        else:
            w = QDoubleSpinBox()
            w.setRange(0.0, 0.9 if key == 'rate' else 10.0)
            w.setDecimals(3)
            w.setSingleStep(0.05)
            w.setValue(float(value))
            w.editingFinished.connect(lambda: store(w.value()) if w.value() != self.specs[row][key] else None)
            if key == 'scale':
                w.setToolTip(f'{TIPS["scale"]} (π = {math.pi:.3f})')
        if key in TIPS and not w.toolTip():
            w.setToolTip(TIPS[key])
        return w

    # ---- training --------------------------------------------------------------------------------
    def train(self):
        """Train the network (and its twin) in the background; returns the Run."""
        from quantumscope.gui.background import Run
        if self.data is None or self.run is not None:
            return None
        d, specs, seed = self.data, [dict(s) for s in self.specs], self.seed.value()
        epochs, batch, lr = self.epochs.value(), self.batch.value(), self.rate.value()
        models = [('hybrid', specs)] + ([('twin', H.twin_specs(specs))] if self.twin.isChecked() else [])
        for line in self.lines.values():
            line.setData([], [])
        self.results.setText('Training…')

        def work(report, cancelled):
            done = {}
            for which, s in models:
                net = H.Network(d.input_shape, s, len(d.classes), seed=seed)
                history = net.fit(d.X_train, d.y_train, d.X_test, d.y_test, epochs=epochs, batch=batch, lr=lr,
                                  progress=lambda e, h, w=which: report((w, e, list(h.loss), list(h.val_accuracy))),
                                  cancelled=cancelled)
                done[which] = (net, history)
                if history.stopped:
                    break
            return done

        self.train_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status.setText('Training the hybrid network…')
        self.run = Run(work, owner=self, task='Training the hybrid QNN', on_progress=self._progress,
                       on_done=self._trained, on_error=self._failed).start()
        return self.run

    def _progress(self, value):
        which, epoch, loss, val = value
        x = list(range(1, len(loss) + 1))
        self.lines[(which, 'loss')].setData(x, loss)
        self.lines[(which, 'val')].setData(x[:len(val)], val)
        name = 'hybrid network' if which == 'hybrid' else 'classical twin'
        self.status.setText(f'Training the {name}: epoch {epoch} of {self.epochs.value()}'
                            + (f', test accuracy {val[-1]:.0%}' if val else ''))

    def _trained(self, done):
        self.run = None
        self.stop_button.setEnabled(False)
        self.train_button.setEnabled(True)
        self.models = done
        d = self.data
        lines = []
        for which, (net, history) in done.items():
            loss, acc = net.evaluate(d.X_test, d.y_test)
            classical, quantum = net.counts()
            name = 'Hybrid network' if which == 'hybrid' else 'Classical twin'
            lines.append(f'<b>{name}</b>: test accuracy <b>{acc:.1%}</b> (loss {loss:.3f}) · training accuracy '
                         f'{history.accuracy[-1]:.1%} · {classical:,} classical + {quantum} quantum parameters · '
                         f'{history.seconds:.1f} s' + (' · stopped early' if history.stopped else '')
                         if history.accuracy else f'<b>{name}</b>: stopped before the first epoch ended')
        if 'hybrid' in done and 'twin' in done and done['twin'][1].accuracy:
            h = done['hybrid'][0].evaluate(d.X_test, d.y_test)[1]
            t = done['twin'][0].evaluate(d.X_test, d.y_test)[1]
            verdict = ('about the same as' if abs(h - t) < 0.02 else 'better than' if h > t else 'worse than')
            lines.append(f'On this test data the hybrid network did {verdict} its classical twin. With small data '
                         'and few qubits this varies with the seed: train with a few seeds before drawing a '
                         'conclusion.')
        self.results.setText('<br><br>'.join(lines))
        self.status.setText('Done.')
        if 'hybrid' in done and done['hybrid'][1].accuracy:
            self._confusion(done['hybrid'][0])

    def _failed(self, kind, message, trace=''):
        self.run = None
        self.stop_button.setEnabled(False)
        self.train_button.setEnabled(True)
        self.status.setText(f'Training stopped: {message}')

    def _confusion(self, net):
        import pyqtgraph as pg
        d = self.data
        k = len(d.classes)
        m = H.confusion(d.y_test, net.predict(d.X_test), k)
        plot = self.confusion_plot
        plot.clear()
        share = m / np.maximum(m.sum(1, keepdims=True), 1)
        image = pg.ImageItem(share.T)
        image.setLookupTable(pg.colormap.get('viridis').getLookupTable(nPts=256))
        image.setLevels((0, 1))
        plot.addItem(image)
        for i in range(k):
            for j in range(k):
                text = pg.TextItem(str(m[i, j]), color='w' if share[i, j] < 0.6 else 'k', anchor=(0.5, 0.5))
                text.setPos(j + 0.5, i + 0.5)
                plot.addItem(text)
        plot.getViewBox().invertY(True)
        ticks = [(i + 0.5, str(c)[:10]) for i, c in enumerate(d.classes)]
        plot.getAxis('bottom').setTicks([ticks])
        plot.getAxis('left').setTicks([ticks])
        plot.setAspectLocked(True)
