"""Import data… (v0.9.19): look at a .csv file before using it, and choose its label column.

The file is shown as read (the first rows, scrolling both ways). The label column is guessed as
before (a column named label, target, class …, or the last); choose another from the list or by
clicking a column's name. Columns that are only row numbers or IDs are left out by default, and any
column can be left out or put back.
"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout,
                               QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMenu, QPushButton, QSplitter,
                               QStyledItemDelegate, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from quantumscope.ml import datasets as D

PREVIEW_ROWS = 200                                               # rows shown (all are imported)
MANY_CLASSES = 20


class _Columns(QStyledItemDelegate):
    """Tints the label column and fades the columns left out, over whatever the theme draws."""
    def __init__(self, dialog):
        super().__init__(dialog)
        self.dialog = dialog

    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        column = index.column()
        if column == self.dialog.label():
            painter.fillRect(option.rect, QColor(90, 230, 255, 55))
        elif column in self.dialog.leave_out():
            faded = QColor(option.palette.base().color())
            faded.setAlpha(170)
            painter.fillRect(option.rect, faded)


class ImportDialog(QDialog):
    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.path, self.dataset, self.table = path, None, None
        self.setWindowTitle('Import data')
        self.resize(940, 640)
        root = QVBoxLayout(self)
        top = QHBoxLayout()
        self.file_label = QLabel()
        self.file_label.setWordWrap(True)
        top.addWidget(self.file_label, 1)
        self.header_box = QCheckBox('The first row names the columns')
        self.header_box.setToolTip('Untick if the first row is data, not column names')
        top.addWidget(self.header_box)
        root.addLayout(top)
        split = QSplitter(Qt.Orientation.Vertical)
        self.preview = QTableWidget()
        self.preview.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.preview.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.preview.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.preview.setItemDelegate(_Columns(self))
        header = self.preview.horizontalHeader()
        header.setSectionsClickable(True)
        header.setToolTip('Click a column\'s name to make it the label; right-click to leave it out or put it back')
        header.sectionClicked.connect(self.choose_label)
        header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        header.customContextMenuRequested.connect(self._column_menu)
        split.addWidget(self.preview)
        below = QWidget()
        row = QHBoxLayout(below)
        row.setContentsMargins(0, 0, 0, 0)
        left = QFormLayout()
        self.label_box = QComboBox()
        self.label_box.setToolTip('The column that says which class each row belongs to')
        left.addRow('Label column', self.label_box)
        self.classes_label = QLabel()
        self.classes_label.setWordWrap(True)
        left.addRow(self.classes_label)
        self.warning = QLabel()
        self.warning.setWordWrap(True)
        self.warning.setStyleSheet('color: #e8a33d;')
        left.addRow(self.warning)
        holder = QWidget()
        holder.setLayout(left)
        row.addWidget(holder, 3)
        features = QVBoxLayout()
        features.addWidget(QLabel('Features (untick to leave a column out)'))
        self.feature_list = QListWidget()
        features.addWidget(self.feature_list, 1)
        buttons = QHBoxLayout()
        self.all_button, self.none_button = QPushButton('All'), QPushButton('None')
        self.all_button.clicked.connect(lambda: self._tick_all(True))
        self.none_button.clicked.connect(lambda: self._tick_all(False))
        buttons.addWidget(self.all_button)
        buttons.addWidget(self.none_button)
        buttons.addStretch()
        features.addLayout(buttons)
        row.addLayout(features, 2)
        split.addWidget(below)
        split.setStretchFactor(0, 3)
        split.setStretchFactor(1, 2)
        root.addWidget(split, 1)
        self.summary = QLabel()
        self.summary.setWordWrap(True)
        self.summary.setObjectName('muted')
        root.addWidget(self.summary)
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        self.import_button = self.buttons.addButton('Import', QDialogButtonBox.ButtonRole.AcceptRole)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        root.addWidget(self.buttons)
        self.label_box.currentIndexChanged.connect(lambda *_: self._label_changed())
        self.feature_list.itemChanged.connect(lambda *_: self.refresh())
        self.header_box.toggled.connect(lambda on: self.read(on))
        self.read(None)

    # ---- reading ---------------------------------------------------------------------------------
    def read(self, header):
        """(Re)read the file; header None: guessed."""
        self.table = D.read_table(self.path, header)
        t = self.table
        self.header_box.blockSignals(True)
        self.header_box.setChecked(t.header)
        self.header_box.blockSignals(False)
        import os
        self.file_label.setText(f'<b>{os.path.basename(self.path)}</b> · {len(t.rows)} rows, {len(t.names)} columns'
                                + (f' · the first {PREVIEW_ROWS} rows are shown' if len(t.rows) > PREVIEW_ROWS else ''))
        shown = t.rows[:PREVIEW_ROWS]
        self.preview.clear()
        self.preview.setRowCount(len(shown))
        self.preview.setColumnCount(len(t.names))
        self.preview.setHorizontalHeaderLabels(t.names)
        for r, cells in enumerate(shown):
            for c, cell in enumerate(cells):
                self.preview.setItem(r, c, QTableWidgetItem(cell.strip()))
        self.label_box.blockSignals(True)
        self.label_box.clear()
        for c, name in enumerate(t.names):
            kind, distinct, _ = t.describe(c)
            self.label_box.addItem(f'{name}  ({distinct} different {"values" if kind == "number" else "names"})', c)
        self.label_box.setCurrentIndex(t.guess_label())
        self.label_box.blockSignals(False)
        self.feature_list.blockSignals(True)
        self.feature_list.clear()
        self.ids = [c for c in range(len(t.names)) if t.looks_like_an_id(c)]
        for c, name in enumerate(t.names):
            kind, distinct, missing = t.describe(c)
            item = QListWidgetItem(f'{name}  ·  {kind}' + (f', {missing} missing' if missing else '')
                                   + ('  (row numbers or IDs)' if c in self.ids else ''))
            item.setData(Qt.ItemDataRole.UserRole, c)
            item.setData(Qt.ItemDataRole.UserRole + 1, item.text())
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked if c in self.ids else Qt.CheckState.Checked)
            self.feature_list.addItem(item)
        self.feature_list.blockSignals(False)
        self._label_changed()

    # ---- choices ---------------------------------------------------------------------------------
    def label(self):
        return self.label_box.currentData()

    def leave_out(self):
        out = []
        for i in range(self.feature_list.count()):
            item = self.feature_list.item(i)
            c = item.data(Qt.ItemDataRole.UserRole)
            if c != self.label() and item.checkState() != Qt.CheckState.Checked:
                out.append(c)
        return out

    def choose_label(self, column):
        self.label_box.setCurrentIndex(self.label_box.findData(column))

    def set_used(self, column, used):
        item = self.feature_list.item(column)
        item.setCheckState(Qt.CheckState.Checked if used else Qt.CheckState.Unchecked)

    def _tick_all(self, on):
        self.feature_list.blockSignals(True)
        for i in range(self.feature_list.count()):
            self.feature_list.item(i).setCheckState(Qt.CheckState.Checked if on else Qt.CheckState.Unchecked)
        self.feature_list.blockSignals(False)
        self.refresh()

    def _column_menu(self, pos):
        column = self.preview.horizontalHeader().logicalIndexAt(pos)
        if column < 0:
            return
        menu = QMenu(self)
        menu.addAction('Use as the label', lambda: self.choose_label(column))
        if column != self.label():
            used = column not in self.leave_out()
            menu.addAction('Leave out' if used else 'Use as a feature', lambda: self.set_used(column, not used))
        menu.exec(self.preview.horizontalHeader().mapToGlobal(pos))

    def _label_changed(self):
        label = self.label()
        self.feature_list.blockSignals(True)
        for i in range(self.feature_list.count()):                 # the label is never a feature
            item = self.feature_list.item(i)
            flags = item.flags()
            item.setText(item.data(Qt.ItemDataRole.UserRole + 1) + ('  ← the label' if i == label else ''))
            if i == label:
                item.setFlags(flags & ~Qt.ItemFlag.ItemIsEnabled)
                item.setCheckState(Qt.CheckState.Unchecked)
            elif not flags & Qt.ItemFlag.ItemIsEnabled:              # the label before: a feature again
                item.setFlags(flags | Qt.ItemFlag.ItemIsEnabled)
                item.setCheckState(Qt.CheckState.Unchecked if i in self.ids else Qt.CheckState.Checked)
        self.feature_list.blockSignals(False)
        self.refresh()

    # ---- what the choice gives ---------------------------------------------------------------------
    def refresh(self):
        t, label, out = self.table, self.label(), set(self.leave_out())
        bold = self.preview.font()
        bold.setBold(True)
        for c in range(len(t.names)):
            head = self.preview.horizontalHeaderItem(c)
            head.setText(('★ ' if c == label else '') + t.names[c] + (' (left out)' if c in out else ''))
            head.setFont(bold if c == label else self.preview.font())
            head.setToolTip('The label column' if c == label else
                            'Left out: right-click to use it' if c in out else
                            'A feature: click to make it the label instead')
        self.preview.horizontalHeader().resizeSections(self.preview.horizontalHeader().ResizeMode.ResizeToContents)
        for c in range(len(t.names)):
            self.preview.setColumnWidth(c, min(240, max(70, self.preview.columnWidth(c))))
        self.preview.viewport().update()
        warnings = []
        kind, distinct, _ = t.describe(label)
        if distinct > MANY_CLASSES or (kind == 'number' and distinct > max(10, len(t.rows) // 5)):
            warnings.append(f'"{t.names[label]}" has {distinct} different values: it looks like a measurement, '
                            'not a class. Choose the column that names each row\'s class.')
        if label in self.ids:
            warnings.append(f'"{t.names[label]}" is different in every row (an ID?): it cannot be a class.')
        try:
            self.dataset = D.table_dataset(t, label, sorted(out))
        except ValueError as exc:
            self.dataset = None
            warnings.insert(0, str(exc))
        self.import_button.setEnabled(self.dataset is not None)
        self.warning.setText(' '.join(warnings))
        if self.dataset is None:
            self.classes_label.setText('')
            self.summary.setText('')
            return
        ds = self.dataset
        counts = ', '.join(f'{name} ({int(n)})' for name, n in list(zip(ds.classes, ds.counts))[:8])
        more = f' and {len(ds.classes) - 8} more' if len(ds.classes) > 8 else ''
        self.classes_label.setText(f'{len(ds.classes)} classes: {counts}{more}')
        text = len(ds.text_columns)
        left = [t.names[c] for c in sorted(out)]
        self.summary.setText(f'{len(ds.y)} samples · {len(ds.features)} features'
                             + (f' ({text} of text, as categories)' if text else '')
                             + (f' · left out: {", ".join(left)}' if left else ''))
