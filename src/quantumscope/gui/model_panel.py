"""Saving, loading and using trained models in the Quantum ML classifiers (v0.8.2).

ModelPanel sits in both classifiers: a summary of the current model (just trained, or loaded from a
file), Save model…, Load model… and Predict on a file…. Predictions run in the background and appear
in a PredictionDialog: one row per sample, accuracy when the file has labels, and Export CSV….
The model files themselves are quantumscope.ml.models (safe .npz, never unpickled).
"""
import csv
import os
import re

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QFileDialog, QGroupBox, QHBoxLayout, QHeaderView, QLabel, QMessageBox,
                               QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout)

from quantumscope.ml import datasets as D
from quantumscope.ml import models as M

KIND_NAMES = {'kernel': 'Quantum Kernel Classifier', 'variational': 'Variational Classifier'}


def describe(model):
    """One short paragraph about a model: what it is, what it was trained on, how well it did."""
    s, info = model.settings, model.info
    if model.kind == 'kernel':
        what = (f'{"SVM" if s.get("method") == "svm" else "Kernel ridge"}, '
                f'{"ZZ" if s["feature_map"] == "zz" else "angle"} feature map'
                + (f' ({s["reps"]} repetitions)' if s['feature_map'] == 'zz' else '')
                + f', bandwidth {s["bandwidth"]:g}, {len(model.arrays["points"])} stored points')
    else:
        what = (f'{s["layers"]} trainable layers, {"ZZ" if s["feature_map"] == "zz" else "angle"} feature map'
                + (f', trained with {s["optimizer"]}' if s.get('optimizer') else ''))
    data = info.get('dataset') or 'unknown data'
    scores = (f'training accuracy {info["train"]:.0%}, test accuracy {info["test"]:.0%}'
              if 'train' in info and 'test' in info else '')
    when = f', {info["created"].replace("T", " ")[:16]}' if info.get('created') else ''
    return (f'{what}; {model.pipeline.outputs} qubits; {model.classes[0]} (+1) vs {model.classes[1]} (−1); '
            f'trained on {data}' + (f'; {scores}' if scores else '') + when + '.')


def suggested_name(model):
    method = model.settings.get('method', 'variational') if model.kind == 'kernel' else 'variational'
    raw = f'{method}-{model.info.get("dataset") or "model"}-{model.classes[0]}-vs-{model.classes[1]}'
    return re.sub(r'[^A-Za-z0-9._-]+', '-', raw).strip('-') + '.npz'


class ModelPanel(QGroupBox):
    """The current model of one classifier, with Save, Load and Predict on a file."""

    def __init__(self, kind, parent=None):
        super().__init__('Model', parent)
        self.kind, self.model, self.origin = kind, None, ''
        self.on_loaded = None                                      # the experiment matches its controls to it
        layout = QVBoxLayout(self)
        self.summary = QLabel('Train, or load a saved model.')
        self.summary.setWordWrap(True)
        self.summary.setObjectName('muted')
        layout.addWidget(self.summary)
        row = QHBoxLayout()
        self.save_button, self.load_button = QPushButton('Save model…'), QPushButton('Load model…')
        row.addWidget(self.save_button)
        row.addWidget(self.load_button)
        layout.addLayout(row)
        self.predict_button = QPushButton('Predict on a file…')
        self.predict_button.setToolTip('New samples as .csv or .npz, with the same raw features as the training data')
        layout.addWidget(self.predict_button)
        self.save_button.clicked.connect(lambda: self.save())
        self.load_button.clicked.connect(lambda: self.load())
        self.predict_button.clicked.connect(lambda: self.predict_file())
        self._refresh()

    def set_model(self, model, origin='trained just now'):
        self.model, self.origin = model, origin
        self._refresh()

    def _refresh(self):
        has = self.model is not None
        self.save_button.setEnabled(has)
        self.predict_button.setEnabled(has)
        if has:
            self.summary.setText(f'<b>{self.origin.capitalize()}:</b> {describe(self.model)}')

    # ---- files --------------------------------------------------------------------------------
    def save(self, path=None):
        if self.model is None:
            return None
        if path is None:
            path, _ = QFileDialog.getSaveFileName(self, 'Save model', suggested_name(self.model),
                                                  'QuantumScope model (*.npz)')
            if not path:
                return None
        try:
            path = self.model.save(path)
        except OSError as exc:
            QMessageBox.warning(self, 'Save model', f'The model could not be saved:\n{exc}')
            return None
        self.origin = f'saved as {os.path.basename(path)}'
        self._refresh()
        return path

    def load(self, path=None):
        if path is None:
            path, _ = QFileDialog.getOpenFileName(self, 'Load model', '', 'QuantumScope model (*.npz)')
            if not path:
                return None
        try:
            model = M.load(path)
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, 'Load model', f'This file could not be loaded:\n{exc}')
            return None
        if model.kind != self.kind:
            QMessageBox.information(self, 'Load model', f'This is a {KIND_NAMES[model.kind]} model: open it in the '
                                                        f'{KIND_NAMES[model.kind]} experiment.')
            return None
        self.set_model(model, f'loaded from {os.path.basename(path)}')
        if self.on_loaded is not None:
            self.on_loaded(model)
        return model

    def predict_file(self, path=None):
        """Predict every sample in a file, in the background; returns the run (run.wait() → result)."""
        if self.model is None:
            return None
        if path is None:
            path, _ = QFileDialog.getOpenFileName(self, 'Predict on a file', '', 'Data (*.csv *.npz *.txt)')
            if not path:
                return None
        model = self.model
        try:
            data = D.read_for_prediction(path, model.pipeline)
        except (OSError, ValueError, UnicodeDecodeError) as exc:
            QMessageBox.warning(self, 'Predict on a file', f'This file could not be used:\n{exc}')
            return None
        from quantumscope.gui.background import Run

        def work(report, cancelled):
            report(f'Predicting {len(data.X)} samples…')
            names, values = model.predict(data.X)
            return dict(names=names, values=values, data=data, path=path)
        self.predict_button.setEnabled(False)
        self.summary.setText(f'Predicting {len(data.X)} samples…')

        def done(result):
            self._refresh()
            self.dialog = PredictionDialog(model, result, self)
            self.dialog.show()
        self.run = Run(work, owner=self, on_done=done, on_error=self._failed).start()
        return self.run

    def _failed(self, exc, details):
        self._refresh()
        QMessageBox.warning(self, 'Predict on a file', f'The prediction failed:\n{exc}')


class PredictionDialog(QDialog):
    """One row per sample: prediction, decision value, and the true class when the file has labels."""

    def __init__(self, model, result, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f'Predictions: {os.path.basename(result["path"])}')
        self.model, self.result = model, result
        names, values, data = result['names'], result['values'], result['data']
        layout = QVBoxLayout(self)
        counts = {c: names.count(c) for c in model.classes}
        text = (f'{len(names)} samples: ' + ', '.join(f'{n} predicted {c}' for c, n in counts.items()) + '.')
        self.correct = None
        if data.labels is not None:
            known = [i for i, label in enumerate(data.labels) if label in model.classes]
            if known:
                hits = sum(names[i] == data.labels[i] for i in known)
                self.correct = hits / len(known)
                text += f' Accuracy on the {len(known)} labelled samples of these two classes: {self.correct:.0%}.'
            others = len(data.labels) - len(known)
            if others:
                text += f' {others} samples belong to other classes, which this model cannot recognize.'
        if data.notes:
            text += ' ' + ' '.join(data.notes)
        self.summary = QLabel(text)
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)
        labelled = data.labels is not None
        headers = ['#', 'Prediction', 'Decision value'] + (['True class', 'Correct'] if labelled else [])
        self.table = QTableWidget(len(names), len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        for i, (name, value) in enumerate(zip(names, values)):
            cells = [str(i + 1), name, f'{value:+.4f}']
            if labelled:
                truth = data.labels[i]
                cells += [truth, '' if truth not in model.classes else '✓' if truth == name else '✗']
            for j, cell in enumerate(cells):
                item = QTableWidgetItem(cell)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(i, j, item)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table, 1)
        row = QHBoxLayout()
        export, close = QPushButton('Export CSV…'), QPushButton('Close')
        export.clicked.connect(lambda: self.export())
        close.clicked.connect(self.accept)
        row.addStretch()
        row.addWidget(export)
        row.addWidget(close)
        layout.addLayout(row)
        self.resize(620, 520)

    def export(self, path=None):
        if path is None:
            base = os.path.splitext(os.path.basename(self.result['path']))[0]
            path, _ = QFileDialog.getSaveFileName(self, 'Export predictions', f'{base}-predictions.csv', 'CSV file (*.csv)')
            if not path:
                return None
        if not path.lower().endswith('.csv'):
            path += '.csv'
        data = self.result['data']
        with open(path, 'w', newline='', encoding='utf-8') as handle:
            writer = csv.writer(handle)
            writer.writerow(['sample', 'prediction', 'decision'] + (['true_class'] if data.labels is not None else []))
            for i, (name, value) in enumerate(zip(self.result['names'], np.asarray(self.result['values']))):
                writer.writerow([i + 1, name, f'{value:.10g}'] + ([data.labels[i]] if data.labels is not None else []))
        return path
