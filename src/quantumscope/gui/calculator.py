"""The Quantum Calculator, in the Math tab (v0.9.0).

Type an expression in Dirac notation and press Enter. Exact mode keeps √2, i, π and symbols such as
θ (SymPy); Digits mode computes numbers (NumPy) and still shows familiar values exactly. The result
appears as one line (states in Dirac form), as a matrix, and step by step; single-qubit states also
appear on a Bloch sphere. Product states can be sent to the circuit simulator as its starting state.
"""
import math

import numpy as np
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import (QAbstractItemView, QButtonGroup, QComboBox, QGridLayout, QGroupBox, QHBoxLayout,
                               QHeaderView, QLabel, QLineEdit, QListWidget, QPushButton, QSizePolicy, QSplitter,
                               QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from quantumscope.calc import format as F
from quantumscope.calc.evaluate import Calculator, Special
from quantumscope.calc.parser import CalcError

EXAMPLES = (('Bell state', 'CNOT (H ⊗ I)|00⟩'), ('H X H = Z', 'H X H'),
            ('A rotation is an exponential', 'exp(-i θ X / 2)'), ('Commutator [X, Y]', 'comm(X, Y)'),
            ('Eigenstates of Y', 'eig(Y)'), ('Expectation value', 'expect(X ⊗ X, CNOT (H ⊗ I)|00⟩)'),
            ('Entanglement entropy', 'entropy(ptrace(CNOT (H ⊗ I)|00⟩, 1))'), ('Pauli decomposition', 'pauli(CNOT)'),
            ('Bloch vector', 'bloch(RY(pi/3)|0⟩)'), ('Name a state', 'ψ = (|0⟩ + i|1⟩)/sqrt(2)'))
SYMBOLS = ('|0⟩', '|1⟩', '|+⟩', '|-⟩', '⟨', '|', '⟩', '⊗', '†', 'π', 'θ', 'φ', 'ψ', 'i')
FUNCTIONS = ('eig', 'ptrace', 'expect', 'bloch', 'pauli', 'exp', 'dm', 'entropy', 'fidelity', 'tr', 'comm', 'normalize')
HELP = ('Kets |0⟩ |+⟩ |01⟩ (or |0>), bras ⟨0| (or <0|), ⊗ (or (x)), † (or \'), products side by side (H|0⟩). '
        '⊗ binds more tightly than side-by-side products: H ⊗ I |00⟩ is (H ⊗ I)|00⟩. Name a result with ψ = …')


class BlochView(QWidget):
    """A Bloch sphere with one vector (x, y, z); inside the sphere for a mixed state."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.vector = None
        self.setMinimumSize(220, 220)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_vector(self, vector):
        self.vector = None if vector is None else [float(v) for v in vector]
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        palette = self.palette()
        ink, faint = palette.text().color(), palette.mid().color()
        accent = QColor('#ff9a5a')
        r = min(self.width(), self.height()) * 0.36
        cx, cy = self.width() / 2, self.height() / 2 + 6
        az, el = math.radians(35), math.radians(18)

        def project(x, y, z):
            x1, y1 = x * math.cos(az) - y * math.sin(az), x * math.sin(az) + y * math.cos(az)
            return QPointF(cx + r * x1, cy - r * (z * math.cos(el) - y1 * math.sin(el))), y1 * math.cos(el) + z * math.sin(el)

        def pen(colour, width, dashed=False, alpha=1.0):
            c = QColor(colour)
            c.setAlphaF(alpha)
            p = QPen(c, width)
            if dashed:
                p.setDashPattern([3, 3])
            return p
        painter.setPen(pen(ink, 1.3, alpha=0.8))
        painter.drawEllipse(QPointF(cx, cy), r, r)
        steps = [2 * math.pi * k / 96 for k in range(97)]
        for curve in ([project(math.cos(t), math.sin(t), 0) for t in steps],
                      [project(0, math.cos(t), math.sin(t)) for t in steps]):
            for (a, da), (b, db) in zip(curve, curve[1:]):
                back = (da + db) / 2 < 0
                painter.setPen(pen(ink, 0.9, dashed=back, alpha=0.3 if back else 0.6))
                painter.drawLine(a, b)
        font = QFont(self.font())
        font.setPointSizeF(max(8.0, font.pointSizeF() - 1))
        painter.setFont(font)
        for end, label in (((0, 0, 1), '|0⟩'), ((0, 0, -1), '|1⟩'), ((1, 0, 0), 'x'), ((0, 1, 0), 'y')):
            point = project(*end)[0]
            painter.setPen(pen(faint, 0.8, dashed=True))
            painter.drawLine(QPointF(cx, cy), point)
            painter.setPen(pen(ink, 1))
            offset = {'|0⟩': (-10, -6), '|1⟩': (-10, 16), 'x': (-14, 10), 'y': (6, 4)}[label]
            painter.drawText(QPointF(point.x() + offset[0], point.y() + offset[1]), label)
        if self.vector is None:
            painter.setPen(pen(faint, 1))
            painter.drawText(QRectF(0, 0, self.width(), 22), int(Qt.AlignmentFlag.AlignCenter),
                             'Single-qubit states appear here')
            return
        tip = project(*self.vector)[0]
        painter.setPen(pen(accent, 2.6))
        painter.drawLine(QPointF(cx, cy), tip)
        dx, dy = tip.x() - cx, tip.y() - cy
        length = math.hypot(dx, dy)
        if length > 6:
            ux, uy = dx / length, dy / length
            painter.setBrush(accent)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPolygon(QPolygonF([tip, QPointF(tip.x() - 10 * ux + 4.5 * uy, tip.y() - 10 * uy - 4.5 * ux),
                                           QPointF(tip.x() - 10 * ux - 4.5 * uy, tip.y() - 10 * uy + 4.5 * ux)]))
        x, y, z = self.vector
        painter.setPen(pen(ink, 1))
        painter.drawText(QRectF(0, 0, self.width(), 22), int(Qt.AlignmentFlag.AlignCenter),
                         f'(x, y, z) = ({x:.3g}, {y:.3g}, {z:.3g})' + ('' if abs(x * x + y * y + z * z - 1) < 1e-9
                                                                       else '  mixed'))


class CalculatorView(QWidget):
    def __init__(self, parent=None, send_state=None):
        super().__init__(parent)
        self.calculator = Calculator('exact')
        self.send_state = send_state                             # send_state(vector) → message, or None
        self.result = None
        self.history_inputs, self._recall = [], None
        root = QHBoxLayout(self)
        split = QSplitter(Qt.Orientation.Horizontal)
        root.addWidget(split)
        main = QWidget()
        left = QVBoxLayout(main)
        top = QHBoxLayout()
        title = QLabel('<b>QUANTUM CALCULATOR</b> · Dirac notation, exactly or in digits')
        top.addWidget(title)
        top.addStretch(1)
        self.exact_button, self.digits_button = QPushButton('Exact'), QPushButton('Digits')
        self.mode_group = QButtonGroup(self)
        for button, tip in ((self.exact_button, 'Exact answers: √2, i, π, and symbols such as θ'),
                            (self.digits_button, 'Numbers (familiar values such as 1/√2 still shown exactly)')):
            button.setCheckable(True)
            button.setToolTip(tip)
            self.mode_group.addButton(button)
            top.addWidget(button)
        self.exact_button.setChecked(True)
        for button in (self.exact_button, self.digits_button):          # the chosen mode stands out
            button.setStyleSheet('QPushButton:checked { background: #1f6f8b; color: white; font-weight: 600; '
                                 'border: 1px solid #5ae6ff; }')
        self.examples = QComboBox()
        self.examples.addItem('Examples…', None)
        for label, text in EXAMPLES:
            self.examples.addItem(label, text)
        top.addWidget(self.examples)
        left.addLayout(top)
        row = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText('Type an expression, such as CNOT (H ⊗ I)|00⟩, and press Enter')
        self.input.setToolTip(HELP)
        mono = QFont('monospace')
        mono.setStyleHint(QFont.StyleHint.Monospace)
        mono.setPointSizeF(self.font().pointSizeF() + 2)
        self.input.setFont(mono)
        self.go = QPushButton('Evaluate')
        row.addWidget(self.input, 1)
        row.addWidget(self.go)
        left.addLayout(row)
        palette = QGridLayout()
        palette.setHorizontalSpacing(3)
        palette.setVerticalSpacing(3)
        self.palette_buttons = []
        for k, symbol in enumerate(SYMBOLS):
            button = QPushButton(symbol)
            button.setToolTip(f'Insert {symbol}')
            button.clicked.connect(lambda _=False, s=symbol: self.insert(s))
            palette.addWidget(button, 0, k)
            self.palette_buttons.append(button)
        for k, name in enumerate(FUNCTIONS):
            button = QPushButton(name)
            button.setToolTip(f'Insert {name}(…)')
            button.clicked.connect(lambda _=False, s=name: self.insert(f'{s}(', close=True))
            palette.addWidget(button, 1, k + 1)
            self.palette_buttons.append(button)
        left.addLayout(palette)
        self.answer = QLabel('Try an example, or type an expression.')
        self.answer.setWordWrap(True)
        self.answer.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.answer.setStyleSheet('font-family: monospace; font-size: 20px; font-weight: 600; padding: 6px 2px;')
        self.answer.setMinimumHeight(56)                                 # the theme's label font would win otherwise
        left.addWidget(self.answer)
        self.error = QLabel('')
        self.error.setWordWrap(True)
        self.error.setStyleSheet('color: #ff6b6b;')
        left.addWidget(self.error)
        self.matrix = QTableWidget(0, 0)
        self.matrix.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.matrix.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.matrix.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.matrix.setFont(mono)
        left.addWidget(self.matrix, 2)
        steps_box = QGroupBox('Working, step by step')
        steps_layout = QVBoxLayout(steps_box)
        self.steps = QListWidget()
        self.steps.setFont(mono)
        steps_layout.addWidget(self.steps)
        left.addWidget(steps_box, 1)
        split.addWidget(main)
        side = QWidget()
        right = QVBoxLayout(side)
        self.bloch = BlochView()
        right.addWidget(self.bloch, 3)
        self.send_button = QPushButton('Send to circuit simulator')
        self.send_button.setToolTip('Start the circuit simulator from this state (a product of single-qubit states)')
        self.send_button.setEnabled(False)
        right.addWidget(self.send_button)
        self.send_note = QLabel('')
        self.send_note.setWordWrap(True)
        self.send_note.setObjectName('muted')
        right.addWidget(self.send_note)
        right.addWidget(QLabel('Named values (double-click to insert)'))
        self.variables = QListWidget()
        right.addWidget(self.variables, 1)
        right.addWidget(QLabel('History (click to reuse)'))
        self.history = QListWidget()
        right.addWidget(self.history, 2)
        split.addWidget(side)
        split.setStretchFactor(0, 3)
        split.setStretchFactor(1, 2)
        split.setSizes([700, 420])
        self.input.returnPressed.connect(self.evaluate)
        self.go.clicked.connect(self.evaluate)
        self.examples.activated.connect(self._example)
        self.mode_group.buttonClicked.connect(self._mode_changed)
        self.history.itemClicked.connect(lambda item: self.set_expression(item.data(Qt.ItemDataRole.UserRole)))
        self.variables.itemDoubleClicked.connect(lambda item: self.insert(item.data(Qt.ItemDataRole.UserRole)))
        self.send_button.clicked.connect(self._send)
        self.input.installEventFilter(self)

    # ---- input --------------------------------------------------------------------------------
    def insert(self, text, close=False):
        position = self.input.cursorPosition()
        current = self.input.text()
        addition = text + (')' if close else '')
        self.input.setText(current[:position] + addition + current[position:])
        self.input.setCursorPosition(position + len(text))
        self.input.setFocus()

    def set_expression(self, text, evaluate=False):
        self.input.setText(text)
        self.input.setFocus()
        return self.evaluate() if evaluate else None

    def eventFilter(self, obj, event):
        from PySide6.QtCore import QEvent
        if obj is self.input and event.type() == QEvent.Type.KeyPress and self.history_inputs:
            if event.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down):          # recall earlier inputs
                step = -1 if event.key() == Qt.Key.Key_Up else 1
                index = len(self.history_inputs) if self._recall is None else self._recall
                index = max(0, min(len(self.history_inputs), index + step))
                self._recall = index
                self.input.setText(self.history_inputs[index] if index < len(self.history_inputs) else '')
                return True
        return super().eventFilter(obj, event)

    def _example(self, index):
        text = self.examples.itemData(index)
        self.examples.setCurrentIndex(0)
        if text:
            self.set_expression(text, evaluate=True)

    def _mode_changed(self, *_):
        mode = 'exact' if self.exact_button.isChecked() else 'digits'
        if mode != self.calculator.mode:
            self.calculator.set_mode(mode)
            if self.input.text().strip():
                self.evaluate()

    # ---- evaluation ---------------------------------------------------------------------------
    def evaluate(self):
        """Evaluate the input in the background (exact work can take a moment); returns the run."""
        text = self.input.text().strip()
        if not text:
            return None
        running = getattr(self, 'run', None)
        if running is not None and running.running():
            return running
        from quantumscope.gui.background import Run
        self.go.setEnabled(False)
        self.error.setText('')
        self.answer.setText('Working…')
        calculator, mode = self.calculator, self.calculator.mode

        def work(report, cancelled):
            return calculator.evaluate(text)
        self.run = Run(work, owner=self, on_done=lambda result: self._show(text, result, mode),
                       on_error=lambda exc, details: self._failed(exc)).start()
        return self.run

    def _failed(self, exc):
        self.go.setEnabled(True)
        self.answer.setText('')
        self.error.setText(str(exc))
        if isinstance(exc, CalcError) and exc.at is not None:
            self.input.setCursorPosition(exc.at)                         # the cursor at the problem
        self.input.setFocus()

    def _show(self, text, result, mode):
        self.go.setEnabled(True)
        self.result = result
        value = result.value
        if not self.history_inputs or self.history_inputs[-1] != text:
            self.history_inputs.append(text)
        self._recall = None
        line = F.summary(value, mode)
        self.answer.setText((f'{result.assigned} = ' if result.assigned else '') + line)
        self._show_matrix(value, mode)
        self.steps.clear()
        for step_text, step_value in result.steps:
            self.steps.addItem(f'{step_text}  =  {F.summary(step_value, mode)}')
        self.history.insertItem(0, f'{text}   →   {line}')
        self.history.item(0).setData(Qt.ItemDataRole.UserRole, text)
        self._refresh_variables()
        self._update_bloch(value)
        self._update_send(value)

    def _show_matrix(self, value, mode):
        if isinstance(value, Special) or F.kind(value) == 'number':
            self.matrix.setRowCount(0)
            self.matrix.setColumnCount(0)
            if isinstance(value, Special) and value.kind == 'eigen':
                self.answer.setText('\n'.join(F.special_lines(value, mode)))
            return
        cells = F.entries(value, mode)
        rows, cols = len(cells), len(cells[0])
        self.matrix.setRowCount(rows)
        self.matrix.setColumnCount(cols)
        n_row, n_col = rows.bit_length() - 1, cols.bit_length() - 1
        if 1 << n_row == rows and rows > 1:
            self.matrix.setVerticalHeaderLabels([f'|{format(r, f"0{n_row}b")}⟩' for r in range(rows)])
        if 1 << n_col == cols and cols > 1:
            self.matrix.setHorizontalHeaderLabels([f'⟨{format(c, f"0{n_col}b")}|' for c in range(cols)])
        for r in range(rows):
            for c in range(cols):
                item = QTableWidgetItem(cells[r][c])
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.matrix.setItem(r, c, item)

    def _refresh_variables(self):
        self.variables.clear()
        for name, (mode, value) in self.calculator.variables.items():
            self.variables.addItem(f'{name} = {F.summary(value, mode)}')
            self.variables.item(self.variables.count() - 1).setData(Qt.ItemDataRole.UserRole, name)

    def _numeric(self, value):
        import sympy
        if isinstance(value, sympy.MatrixBase):
            if value.free_symbols:
                return None
            return np.array(value.evalf(), complex)
        return value if isinstance(value, np.ndarray) else None

    def _update_bloch(self, value):
        vector = None
        if isinstance(value, Special) and value.kind == 'bloch':
            try:
                vector = [float(complex(getattr(v, 'evalf', lambda: v)()).real) for v in value.data]
            except (TypeError, ValueError):
                vector = None
        else:
            m = self._numeric(value)
            if m is not None:
                if m.shape == (2, 1):
                    m = m @ m.conj().T / max(1e-300, float(np.vdot(m, m).real))
                if m.shape == (2, 2) and np.allclose(m, m.conj().T) and abs(np.trace(m) - 1) < 1e-9:
                    vector = [2 * m[0, 1].real, 2 * m[1, 0].imag, (m[0, 0] - m[1, 1]).real]
        self.bloch.set_vector(vector)

    def _update_send(self, value):
        self._sendable = None
        m = None if isinstance(value, Special) else self._numeric(value)
        if m is not None and m.ndim == 2 and m.shape[1] == 1 and m.shape[0] >= 2:
            self._sendable = m.ravel()
        self.send_button.setEnabled(self._sendable is not None and self.send_state is not None)
        self.send_note.setText('')

    def _send(self):
        if self._sendable is None or self.send_state is None:
            return
        self.send_note.setText(self.send_state(self._sendable) or '')
