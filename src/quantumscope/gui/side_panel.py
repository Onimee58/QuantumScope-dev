"""Side panels that fold to a narrow strip instead of disappearing (v0.9.15).

A control panel dragged shut used to vanish without a trace. Wrapped in a CollapsiblePanel, it
folds to a strip with its name written down the side and a button to open it again; the choice is
remembered between sessions.
"""
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QHBoxLayout, QSplitter, QToolButton, QVBoxLayout, QWidget

STRIP = 24                                     # width of the folded panel
UNLIMITED = 16777215                           # Qt's QWIDGETSIZE_MAX


class VerticalTitle(QWidget):
    """A name written bottom-to-top, for the folded strip."""
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.text = text
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def sizeHint(self):
        metrics = self.fontMetrics()
        return QSize(metrics.height() + 6, metrics.horizontalAdvance(self.text) + 16)

    def minimumSizeHint(self):
        return self.sizeHint()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(self.palette().windowText().color())
        painter.translate(self.width() / 2 + self.fontMetrics().ascent() / 2 - 1, self.height() - 8)
        painter.rotate(-90)
        painter.drawText(0, 0, self.text)
        painter.end()

    def mouseReleaseEvent(self, event):
        self.parent().parent().set_collapsed(False)


class CollapsiblePanel(QWidget):
    """Wraps a side panel: a ‹ button folds it to a strip (› or a click on its name opens it again).

    side: 'left' when the panel is at the left of its window (the strip is on its right edge)."""
    collapsedChanged = Signal(bool)

    def __init__(self, content, title, key=None, side='left', parent=None):
        super().__init__(parent)
        self.content, self.title, self.key, self.side = content, title, key, side
        self._sizes = None
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        self.strip = QWidget()
        self.strip.setFixedWidth(STRIP)
        strip = QVBoxLayout(self.strip)
        strip.setContentsMargins(0, 2, 0, 2)
        strip.setSpacing(6)
        self.button = QToolButton()
        self.button.setAutoRaise(True)
        self.button.setFixedSize(STRIP - 2, STRIP - 2)
        self.button.clicked.connect(lambda: self.set_collapsed(not self.collapsed))
        strip.addWidget(self.button, 0, Qt.AlignmentFlag.AlignHCenter)
        self.name = VerticalTitle(title)
        strip.addWidget(self.name, 0, Qt.AlignmentFlag.AlignHCenter)
        strip.addStretch()
        if side == 'left':
            layout.addWidget(content, 1)
            layout.addWidget(self.strip)
        else:
            layout.addWidget(self.strip)
            layout.addWidget(content, 1)
        self.collapsed = False
        self._show()
        if key and _remembered(key):
            self.set_collapsed(True)

    def set_collapsed(self, collapsed):
        collapsed = bool(collapsed)
        if collapsed == self.collapsed:
            return
        splitter = self.parent() if isinstance(self.parent(), QSplitter) else None
        if collapsed and splitter is not None:
            self._sizes = splitter.sizes()
        self.collapsed = collapsed
        self._show()
        if splitter is not None:
            sizes = splitter.sizes()
            index = splitter.indexOf(self)
            if collapsed:                                  # give the room to the other side
                others = [i for i in range(len(sizes)) if i != index]
                spare = sizes[index] - STRIP
                sizes[index] = STRIP
                if others:
                    sizes[others[0] if index > 0 else others[0]] += spare
                splitter.setSizes(sizes)
            elif self._sizes:
                splitter.setSizes(self._sizes)
        if self.key:
            _remember(self.key, collapsed)
        self.collapsedChanged.emit(collapsed)

    def _show(self):
        c = self.collapsed
        self.content.setVisible(not c)
        self.name.setVisible(c)
        opening, closing = ('›', '‹') if self.side == 'left' else ('‹', '›')
        self.button.setText(opening if c else closing)
        self.button.setToolTip(f'Show {self.title}' if c else f'Hide {self.title}: it folds to this strip')
        if c:
            self.setFixedWidth(STRIP)
        else:
            self.setMinimumWidth(0)
            self.setMaximumWidth(UNLIMITED)


def _remembered(key):
    try:
        from quantumscope.gui import preferences as prefs
        return str(prefs._settings().value(f'panels/{key}', 'false')).lower() == 'true'
    except Exception:                                     # settings are a convenience here
        return False


def _remember(key, collapsed):
    try:
        from quantumscope.gui import preferences as prefs
        store = prefs._settings()
        store.setValue(f'panels/{key}', bool(collapsed))
        store.sync()
    except Exception:
        pass


def wrap_in_splitter(splitter, index, title, key):
    """Wrap the splitter's widget at `index` in a CollapsiblePanel (in place) and stop the splitter
    from collapsing it to nothing."""
    content = splitter.widget(index)
    sizes = splitter.sizes()
    panel = CollapsiblePanel(content, title, key, side='left' if index == 0 else 'right')
    splitter.insertWidget(index, panel)
    splitter.setCollapsible(index, False)
    splitter.setStretchFactor(index, 0)                   # spare width goes to the main view
    for other in range(splitter.count()):
        if other != index:
            splitter.setStretchFactor(other, 1)
    if sizes and all(sizes):                               # sizes are known only once laid out
        splitter.setSizes(sizes)
    return panel
