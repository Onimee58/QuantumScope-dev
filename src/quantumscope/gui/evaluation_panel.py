"""Evaluating the Quantum ML classifiers (v0.8.3): test-set metrics, the confusion matrix, the ROC
curve, cross-validation, and (for the kernel classifier) a hyperparameter search.

The panels do not train anything themselves: each classifier gives them its results and the
functions that run cross-validation or a search in the background.
"""
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QCheckBox, QGridLayout, QGroupBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
                               QProgressBar, QPushButton, QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout,
                               QWidget)

from quantumscope.gui.plots import tidy
from quantumscope.ml import evaluation as E


def _numbers(text, field='Values', example='0.25, 0.5, 1', whole=False):
    """'0.25, 0.5 1' → [0.25, 0.5, 1.0]; a plain message naming the field for anything else."""
    message = f'{field}: use positive {"whole " if whole else ""}numbers separated by commas, such as {example}'
    try:
        values = [float(part) for part in text.replace(',', ' ').split()]
    except ValueError:
        raise ValueError(message) from None
    if not values or any(v <= 0 for v in values) or (whole and any(v != int(v) for v in values)):
        raise ValueError(message)
    return values


CV_HINT = ('Cross-validation trains on k − 1 parts of the training data and checks the remaining part, k times: '
           'a steadier estimate than one test score.')


class EvaluationPanel(QWidget):
    """Test-set metrics, confusion matrix and ROC curve; Cross-validate on the training data."""

    def __init__(self, cross_validate=None, parent=None):
        import pyqtgraph as pg
        super().__init__(parent)
        self.cross_validate = cross_validate                     # cross_validate(k) → a Run, or None
        self.metrics = self.auc = None
        layout = QHBoxLayout(self)
        left = QVBoxLayout()
        self.summary = QLabel('Train the classifier to evaluate it on the test set.')
        self.summary.setWordWrap(True)
        self.summary.setTextFormat(Qt.TextFormat.RichText)
        left.addWidget(self.summary)
        self.confusion = QTableWidget(2, 2)
        self.confusion.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.confusion.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.confusion.setMaximumHeight(96)
        left.addWidget(self.confusion)
        row = QHBoxLayout()
        self.folds = QSpinBox()
        self.folds.setRange(2, 10)
        self.folds.setValue(5)
        self.folds.setPrefix('k = ')
        self.cv_button, self.cv_cancel = QPushButton('Cross-validate'), QPushButton('Cancel')
        self.cv_cancel.setEnabled(False)
        row.addWidget(self.folds)
        row.addWidget(self.cv_button)
        row.addWidget(self.cv_cancel)
        left.addLayout(row)
        self.cv_result = QLabel(CV_HINT)
        self.cv_result.setWordWrap(True)
        self.cv_result.setObjectName('muted')
        left.addWidget(self.cv_result)
        left.addStretch(1)
        holder = QWidget()
        holder.setLayout(left)
        holder.setMaximumWidth(360)
        layout.addWidget(holder)
        self.roc_plot = tidy(pg.PlotWidget(title='ROC curve (test set)'))
        self.roc_plot.setLabel('bottom', 'false-positive rate')
        self.roc_plot.setLabel('left', 'true-positive rate')
        for side in ('left', 'bottom'):
            self.roc_plot.getAxis(side).enableAutoSIPrefix(False)
        layout.addWidget(self.roc_plot, 1)
        from quantumscope.gui.pop_out import overlay              # v0.9.18: ⧉ opens it in its own window
        overlay(self.roc_plot, 'ROC curve')
        self.confusion_plot = tidy(pg.PlotWidget(title='Confusion matrix'))     # many classes (v0.9.3)
        self.confusion_plot.setLabel('bottom', 'predicted class')
        self.confusion_plot.setLabel('left', 'true class')
        self.confusion_plot.setVisible(False)
        layout.addWidget(self.confusion_plot, 1)
        overlay(self.confusion_plot, 'Confusion matrix')
        self.cv_button.clicked.connect(self.run_cross_validation)
        self.cv_cancel.clicked.connect(lambda: self.cv_run.cancel() if getattr(self, 'cv_run', None) else None)
        self.cv_button.setEnabled(False)

    def show_results(self, y_test, decision, classes):
        """The test set's true labels (±1), decision values and class names (+1 first); with more
        than two classes, labels 0 … k−1 and one decision column per class."""
        import pyqtgraph as pg
        y_test, decision = np.asarray(y_test), np.asarray(decision, float)
        self.cv_result.setText(CV_HINT)                          # an earlier model's cross-validation no longer applies
        self.cv_last = None
        if decision.ndim == 2:
            return self._show_many(y_test, decision, list(classes))
        self.confusion.setVisible(True)
        self.confusion_plot.setVisible(False)
        self.confusion.setMaximumHeight(96)
        predicted = np.where(decision >= 0, 1, -1)
        m = E.metrics(y_test, predicted)
        self.metrics, self.classes = m, classes
        self.confusion.setRowCount(2)
        self.confusion.setColumnCount(2)
        try:
            fpr, tpr, _ = E.roc(y_test, decision)
            self.auc = E.auc(y_test, decision)
        except ValueError:                                       # one class only: no ROC curve
            fpr = tpr = None
            self.auc = None
        auc = '—' if self.auc is None else f'{self.auc:.3f}'
        self.summary.setText(
            f'<b>Test set ({m.total} samples)</b><br>accuracy {m.accuracy:.1%} · balanced accuracy '
            f'{m.balanced_accuracy:.1%}<br>precision {m.precision:.1%} · recall {m.recall:.1%} · '
            f'specificity {m.specificity:.1%}<br>F1 {m.f1:.3f} · AUC {auc}<br>'
            f'<span style="color:gray">Precision and recall treat {classes[0]} as the positive class.</span>')
        self.confusion.setHorizontalHeaderLabels([f'predicted {classes[0]}', f'predicted {classes[1]}'])
        self.confusion.setVerticalHeaderLabels([f'true {classes[0]}', f'true {classes[1]}'])
        for i, row in enumerate(m.matrix()):
            for j, count in enumerate(row):
                item = QTableWidgetItem(str(int(count)))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.confusion.setItem(i, j, item)
        self.roc_plot.clear()
        legend = self.roc_plot.getPlotItem().legend
        if legend is not None:                                    # left over from a many-class result
            legend.clear()
        self.roc_plot.plot([0, 1], [0, 1], pen=pg.mkPen('#6b7a8f', style=Qt.PenStyle.DashLine))   # chance
        if fpr is not None:
            self.roc_plot.plot(fpr, tpr, pen=pg.mkPen('#5ae6ff', width=2), stepMode=None)
            self.roc_plot.setTitle(f'ROC curve (test set): AUC {self.auc:.3f}')
        self.roc_plot.setRange(xRange=(0, 1), yRange=(0, 1), padding=0.02)
        self.cv_button.setEnabled(self.cross_validate is not None)

    def _show_many(self, y_test, decision, classes):
        """k classes: accuracy, balanced accuracy and macro averages; the k × k confusion matrix,
        drawn as a picture; a one-vs-rest ROC curve per class."""
        import pyqtgraph as pg
        from quantumscope.gui.qml_experiments import MANY_COLOURS
        k = len(classes)
        m = E.multi_metrics(y_test, decision.argmax(axis=1), k)
        curves = E.roc_by_class(y_test, decision)
        self.metrics, self.classes = m, classes
        self.auc = float(np.mean([c[2] for c in curves.values()])) if curves else None
        auc = '—' if self.auc is None else f'{self.auc:.3f}'
        worst = int(np.argmin(np.where(m.confusion.sum(axis=1) > 0, m.recalls, np.inf)))
        self.summary.setText(
            f'<b>Test set ({m.total} samples, {k} classes)</b><br>accuracy {m.accuracy:.1%} · balanced accuracy '
            f'{m.balanced_accuracy:.1%}<br>macro precision {m.macro_precision:.1%} · macro recall '
            f'{m.macro_recall:.1%}<br>macro F1 {m.macro_f1:.3f} · mean one-vs-rest AUC {auc}<br>'
            f'hardest class: {classes[worst]} (recall {m.recalls[worst]:.0%})<br>'
            f'<span style="color:gray">Macro: the average over the classes, each counting equally. In the '
            f'confusion matrix, each row is a true class: green where it was recognized, red where it was '
            f'taken for another class.</span>')
        short = [name if len(name) <= 10 else name[:9] + '…' for name in classes]
        self.confusion.setVisible(False)                          # drawn as a picture: k × k is too big for a table
        self.confusion_plot.setVisible(True)
        self.draw_confusion(m.confusion, short)
        self.roc_plot.clear()
        legend = self.roc_plot.addLegend(offset=(-8, -8))
        legend.clear()
        self.roc_plot.plot([0, 1], [0, 1], pen=pg.mkPen('#6b7a8f', style=Qt.PenStyle.DashLine))
        for c, (fpr, tpr, area) in curves.items():
            self.roc_plot.plot(fpr, tpr, pen=pg.mkPen(MANY_COLOURS[c % len(MANY_COLOURS)], width=2),
                               name=f'{short[c]} {area:.2f}')
        self.roc_plot.setTitle(f'ROC, one-vs-rest: mean AUC {auc}')
        self.roc_plot.setRange(xRange=(0, 1), yRange=(0, 1), padding=0.02)
        self.cv_button.setEnabled(self.cross_validate is not None)

    def draw_confusion(self, confusion, names):
        """The k × k confusion matrix as a picture: counts in the cells, shaded by the share of each
        true class (green on the diagonal, red elsewhere)."""
        import pyqtgraph as pg
        from PySide6.QtGui import QColor
        plot, k = self.confusion_plot, len(confusion)
        plot.clear()
        rows = np.maximum(confusion.sum(axis=1, keepdims=True), 1)
        share = confusion / rows
        rgba = np.zeros((k, k, 4), np.uint8)
        for i in range(k):
            for j in range(k):
                colour = QColor('#2f9a60' if i == j else '#c04848')
                rgba[i, j, :3] = colour.getRgb()[:3]
                rgba[i, j, 3] = int(255 * min(1.0, 0.12 + 0.88 * share[i, j])) if confusion[i, j] else 18
        image = pg.ImageItem(np.transpose(rgba[::-1], (1, 0, 2)))   # row 0 (first class) at the top
        image.setRect(0, 0, k, k)
        plot.addItem(image)
        size = 9 if k > 6 else 11
        for i in range(k):
            for j in range(k):
                if confusion[i, j]:
                    text = pg.TextItem(str(int(confusion[i, j])), anchor=(0.5, 0.5), color='#ffffff')
                    font = text.textItem.font()
                    font.setPointSize(size)
                    text.setFont(font)
                    text.setPos(j + 0.5, k - i - 0.5)
                    plot.addItem(text)
        plot.getAxis('bottom').setTicks([[(j + 0.5, names[j]) for j in range(k)]])
        plot.getAxis('left').setTicks([[(k - i - 0.5, names[i]) for i in range(k)]])
        plot.setTitle(f'Confusion matrix: {int(np.trace(confusion))} of {int(confusion.sum())} right')
        plot.setAspectLocked(False)
        plot.disableAutoRange()
        plot.setRange(xRange=(0, k), yRange=(0, k), padding=0)
        self.shown_confusion, self.shown_names = confusion, list(names)

    def run_cross_validation(self):
        if self.cross_validate is None:
            return None
        self.cv_button.setEnabled(False)
        self.cv_cancel.setEnabled(True)
        self.cv_result.setText(f'Cross-validating ({self.folds.value()} folds)…')
        self.cv_run = self.cross_validate(self.folds.value(), self._cv_progress, self._cv_done)
        return self.cv_run

    def _cv_progress(self, value):
        done, total = value
        self.cv_result.setText(f'Cross-validating: fold {done} of {total} done…')

    def _cv_done(self, result, error=None):
        self.cv_button.setEnabled(True)
        self.cv_cancel.setEnabled(False)
        if error is not None:
            self.cv_result.setText(f'Cross-validation could not run: {error}')
        elif result is None:
            self.cv_result.setText('Cross-validation cancelled.')
        else:
            folds = ', '.join(f'{s:.0%}' for s in result.scores)
            self.cv_result.setText(f'<b>{len(result.scores)}-fold cross-validation: {result.mean:.1%} ± '
                                   f'{result.std:.1%}</b><br>folds: {folds}')
        self.cv_last = result


class SearchPanel(QWidget):
    """Hyperparameter search for the kernel classifier: the grid, a background search, the results
    sorted best first, and Use best."""

    def __init__(self, start_search, use_best, parent=None):
        super().__init__(parent)
        self.start_search, self.use_best = start_search, use_best
        self.best = None
        layout = QHBoxLayout(self)
        grid_box = QGroupBox('Settings to try')
        grid = QGridLayout(grid_box)
        self.angle, self.zz = QCheckBox('Angle encoding'), QCheckBox('ZZ feature map')
        self.svm, self.ridge = QCheckBox('SVM'), QCheckBox('Kernel ridge')
        for box in (self.angle, self.zz, self.svm):
            box.setChecked(True)
        grid.addWidget(QLabel('Feature maps'), 0, 0)
        grid.addWidget(self.angle, 0, 1)
        grid.addWidget(self.zz, 0, 2)
        grid.addWidget(QLabel('Classifiers'), 1, 0)
        grid.addWidget(self.svm, 1, 1)
        grid.addWidget(self.ridge, 1, 2)
        self.bandwidths, self.reps, self.strengths = QLineEdit('0.25, 0.5, 1'), QLineEdit('1, 2'), QLineEdit('0.1, 1, 10')
        for row, (label, field) in enumerate((('Bandwidths', self.bandwidths), ('Repetitions (ZZ)', self.reps),
                                              ('C or λ', self.strengths)), start=2):
            grid.addWidget(QLabel(label), row, 0)
            grid.addWidget(field, row, 1, 1, 2)
        self.folds = QSpinBox()
        self.folds.setRange(2, 10)
        self.folds.setValue(5)
        self.folds.setPrefix('k = ')
        grid.addWidget(QLabel('Folds'), 5, 0)
        grid.addWidget(self.folds, 5, 1)
        buttons = QHBoxLayout()
        self.search_button, self.cancel_button, self.best_button = (QPushButton('Search'), QPushButton('Cancel'),
                                                                    QPushButton('Use best'))
        self.cancel_button.setEnabled(False)
        self.best_button.setEnabled(False)
        for button in (self.search_button, self.cancel_button, self.best_button):
            buttons.addWidget(button)
        grid.addLayout(buttons, 6, 0, 1, 3)
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        grid.addWidget(self.progress, 7, 0, 1, 3)
        self.status = QLabel('Every combination is cross-validated on the training data; the test set is not '
                             'used, so its score stays honest.')
        self.status.setWordWrap(True)
        self.status.setObjectName('muted')
        grid.addWidget(self.status, 8, 0, 1, 3)
        grid_box.setMaximumWidth(380)
        layout.addWidget(grid_box)
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(['#', 'Map', 'Reps', 'Bandwidth', 'Classifier', 'C or λ', 'Accuracy'])
        self.table.horizontalHeaderItem(6).setToolTip('Cross-validated accuracy: mean ± spread across the folds')
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)   # each column fits its text
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table, 1)
        self.search_button.clicked.connect(self.search)
        self.cancel_button.clicked.connect(lambda: self.run.cancel() if getattr(self, 'run', None) else None)
        self.best_button.clicked.connect(lambda: self.use_best(self.best.settings) if self.best else None)

    def grid(self):
        maps = [m for m, box in (('angle', self.angle), ('zz', self.zz)) if box.isChecked()]
        methods = [m for m, box in (('svm', self.svm), ('ridge', self.ridge)) if box.isChecked()]
        if not maps or not methods:
            raise ValueError('Choose at least one feature map and one classifier')
        reps = [int(r) for r in _numbers(self.reps.text(), 'Repetitions', '1, 2', whole=True)]
        return dict(feature_map=maps, reps=reps, bandwidth=_numbers(self.bandwidths.text(), 'Bandwidths'),
                    method=methods, strength=_numbers(self.strengths.text(), 'C or λ', '0.1, 1, 10'))

    def search(self):
        try:
            grid = self.grid()
        except ValueError as exc:
            self.status.setText(str(exc))
            return None
        self.search_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.best_button.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.status.setText('Searching…')
        self.run = self.start_search(grid, self.folds.value(), self._progress, self._done)
        return self.run

    def _progress(self, value):
        done, total = value
        self.progress.setMaximum(total)
        self.progress.setValue(done)

    def _done(self, outcome, error=None):
        self.search_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.progress.setVisible(False)
        if error is not None:
            self.status.setText(f'The search could not run: {error}')
            return
        if outcome is None:
            self.status.setText('Search cancelled.')
            return
        rows, best = outcome
        self.rows, self.best = rows, best
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            s = row.settings
            cells = [str(i + 1), 'ZZ' if s['feature_map'] == 'zz' else 'angle',
                     str(s['reps']) if s['feature_map'] == 'zz' else '—', f'{s["bandwidth"]:g}',
                     'SVM' if s['method'] == 'svm' else 'kernel ridge', f'{s["strength"]:g}',
                     f'{row.mean:.1%} ± {row.std:.1%}']
            for j, cell in enumerate(cells):
                item = QTableWidgetItem(cell)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(i, j, item)
        self.best_button.setEnabled(True)
        self.status.setText(f'Best of {len(rows)}: {self.table.item(0, 1).text()} map, bandwidth '
                            f'{best.settings["bandwidth"]:g}, {self.table.item(0, 4).text()} with '
                            f'{best.settings["strength"]:g}: {best.mean:.1%} ± {best.std:.1%}. '
                            f'Use best applies it and trains.')
