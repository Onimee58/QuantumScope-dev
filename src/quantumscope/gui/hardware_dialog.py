"""Run on IBM Quantum hardware… (v0.9.16): ready-to-paste code for the current circuit.

QuantumScope does not contact IBM and does not keep the API key or CRN: what is typed here only
fills in the code shown, and is forgotten when the dialog closes.
"""
from PySide6.QtGui import QFontDatabase, QGuiApplication
from PySide6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout,
                               QLabel, QLineEdit, QPlainTextEdit, QPushButton, QScrollArea, QSpinBox, QVBoxLayout,
                               QWidget)

from quantumscope.physics import hardware_code as H


class HardwareDialog(QDialog):
    def __init__(self, workspace, parent=None):
        super().__init__(parent or workspace)
        self.workspace = workspace
        self.setWindowTitle('Run on IBM Quantum hardware')
        self.resize(860, 760)
        root = QVBoxLayout(self)
        intro = QLabel('QuantumScope writes the code; you run it with your own IBM Quantum account '
                       '(<a href="https://quantum.cloud.ibm.com">quantum.cloud.ibm.com</a>: the free Open Plan '
                       'includes a few minutes of quantum time per 28 days). Nothing is sent from QuantumScope, '
                       'and the key and CRN typed below are not saved.')
        intro.setWordWrap(True)
        intro.setOpenExternalLinks(True)
        root.addWidget(intro)
        box = QGroupBox('Your account and the run')
        form = QFormLayout(box)
        self.credentials = QComboBox()
        for key, label in H.CREDENTIALS:
            self.credentials.addItem(label, key)
        form.addRow('API key and CRN', self.credentials)
        self.api_key = QLineEdit()
        self.api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key.setPlaceholderText('optional: fills in the code (IBM Quantum Platform → API key)')
        form.addRow('API key', self.api_key)
        self.crn = QLineEdit()
        self.crn.setPlaceholderText('optional: crn:v1:bluemix:public:quantum-computing:… (Instances → copy CRN)')
        form.addRow('Instance CRN', self.crn)
        self.backend = QLineEdit()
        self.backend.setPlaceholderText('empty: the least busy device with enough qubits (or e.g. ibm_torino)')
        form.addRow('Device', self.backend)
        self.shots = QSpinBox()
        self.shots.setRange(1, 100_000)
        self.shots.setValue(1024)
        form.addRow('Shots', self.shots)
        self.warning = QLabel()
        self.warning.setWordWrap(True)
        self.warning.setObjectName('muted')
        form.addRow(self.warning)
        root.addWidget(box)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.holder = QWidget()
        self.steps = QVBoxLayout(self.holder)
        scroll.setWidget(self.holder)
        root.addWidget(scroll, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        self.save_button = buttons.addButton('Save the hardware script…', QDialogButtonBox.ButtonRole.ActionRole)
        self.save_button.clicked.connect(lambda: self.save())
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)
        for widget in (self.api_key, self.crn, self.backend):
            widget.textChanged.connect(self.update_code)
        self.credentials.currentIndexChanged.connect(self.update_code)
        self.shots.valueChanged.connect(self.update_code)
        self.update_code()

    def _circuit(self):
        w = self.workspace
        notes = []
        if w.model.noise_model.active or w.model.noise:
            notes.append('QuantumScope\'s noise settings are left out: the hardware has its own noise.')
        return w.qasm_text(), w.n, sorted(w.measurements), bool(w.model.dynamic), notes

    def update_code(self, *_):
        from quantumscope import __version__
        qasm, n, measured, dynamic, notes = self._circuit()
        notes += H.check_credentials(self.api_key.text(), self.crn.text())
        if self.credentials.currentData() == 'code' and self.api_key.text().strip():
            notes.append('The key is written into the hardware script: do not share it, or upload it anywhere.')
        if not measured:
            notes.append('The circuit measures nothing at the end, so the code measures every qubit.')
        self.warning.setText(' '.join(notes))
        self.blocks = H.blocks(qasm, n, measured, shots=self.shots.value(), backend=self.backend.text(),
                               credentials=self.credentials.currentData(), api_key=self.api_key.text(),
                               crn=self.crn.text(), dynamic=dynamic, title=f'A {n}-qubit QuantumScope circuit',
                               version=__version__)
        if len(getattr(self, 'editors', ())) == len(self.blocks):   # typing: keep the view, change the text
            for group, note, editor, block in zip(self.groups, self.notes, self.editors, self.blocks):
                group.setTitle(block.title)
                note.setText(block.note)
                if editor.toPlainText() != block.text:
                    editor.setPlainText(block.text)
            return
        while self.steps.count():
            item = self.steps.takeAt(0)
            widget = item.widget()
            if widget is not None:                          # the previous code: gone at once
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()
        self.editors, self.groups, self.notes = [], [], []
        mono = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        for block in self.blocks:
            group = QGroupBox(block.title)
            v = QVBoxLayout(group)
            note = QLabel(block.note)
            note.setWordWrap(True)
            note.setObjectName('muted')
            v.addWidget(note)
            editor = QPlainTextEdit(block.text)
            editor.setReadOnly(True)
            editor.setFont(mono)
            editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
            lines = block.text.count('\n') + 1
            editor.setFixedHeight(min(320, editor.fontMetrics().lineSpacing() * lines + 16))
            v.addWidget(editor)
            row = QHBoxLayout()
            row.addStretch()
            copy = QPushButton('Copy')
            copy.clicked.connect(lambda _=False, e=editor: self.copy(e.toPlainText()))
            row.addWidget(copy)
            v.addLayout(row)
            self.steps.addWidget(group)
            self.editors.append(editor)
            self.groups.append(group)
            self.notes.append(note)
        self.steps.addStretch()

    def copy(self, text):
        QGuiApplication.clipboard().setText(text)
        self.warning.setText('Copied to the clipboard.')

    def save(self, path=None):
        """Save step 4 (the hardware run) as a .py file; returns the path."""
        if path is None:
            path, _ = QFileDialog.getSaveFileName(self, 'Save the hardware script', 'run_on_ibm_quantum.py',
                                                  'Python (*.py)')
            if not path:
                return None
        if not path.lower().endswith('.py'):
            path += '.py'
        hardware = next(b for b in self.blocks if b.title.startswith('4.'))
        with open(path, 'w', encoding='utf-8') as f:
            f.write(hardware.text + '\n')
        return path
