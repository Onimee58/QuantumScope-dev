"""Graphs in their own windows (v0.9.18).

A ⧉ button in a graph's corner opens it in a window of its own: put it on a second screen, make it
large for a class, or set two graphs side by side. The graph keeps updating, because it is the same
widget, moved. Where it was, a note offers to bring it back; closing its window brings it back too,
and closing the experiment closes the window.

Works for a graph in a layout, a splitter or a tab, without changes to the code that made it.
"""
from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QLayout, QPushButton, QSplitter, QTabWidget,
                               QToolButton, QVBoxLayout, QWidget)

OPEN = []                                                         # the graph windows now open


def button(widget, title, parent=None):
    """A ⧉ button that opens `widget` in its own window (to place in a layout of your own)."""
    b = QToolButton(parent)
    b.setObjectName('popOut')
    b.setText('⧉')
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setToolTip('Open this graph in its own window (closing the window puts it back)')
    b.clicked.connect(lambda: pop_out(widget, title))
    widget.pop_out_button = b
    return b


class _Corner(QObject):
    """Keeps a button in the top-right corner of its widget."""
    def __init__(self, widget, b):
        super().__init__(widget)
        self.widget, self.b = widget, b
        widget.installEventFilter(self)
        self.place()

    def place(self):
        self.b.move(self.widget.width() - self.b.width() - 6, 6)
        self.b.raise_()

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Type.Resize, QEvent.Type.Show):
            self.place()
        return False


def overlay(widget, title):
    """Put a ⧉ button in the top-right corner of a graph."""
    b = button(widget, title, widget)
    b.setFixedSize(24, 22)
    b.show()
    _Corner(widget, b)
    return b


class Placeholder(QFrame):
    """What stays where a graph was while it is in its own window."""
    def __init__(self, window):
        super().__init__()
        self.setObjectName('popOutPlaceholder')
        self.window_ = window
        layout = QVBoxLayout(self)
        layout.addStretch()
        note = QLabel(f'{window.title} is open in its own window.')
        note.setObjectName('muted')
        note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        note.setWordWrap(True)
        layout.addWidget(note)
        row = QHBoxLayout()
        row.addStretch()
        show = QPushButton('Show the window')
        show.clicked.connect(window.bring_to_front)
        back = QPushButton('Bring it back here')
        back.clicked.connect(window.close)
        row.addWidget(show)
        row.addWidget(back)
        row.addStretch()
        layout.addLayout(row)
        layout.addStretch()


class GraphWindow(QWidget):
    def __init__(self, widget, title, owner):
        super().__init__(owner, Qt.WindowType.Window)
        self.widget, self.title, self.home = widget, title, None
        self.setWindowTitle(f'{title} · QuantumScope')
        self.resize(max(640, int(widget.width() * 1.4)), max(440, int(widget.height() * 1.4)))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

    def bring_to_front(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):
        bring_back(self)
        super().closeEvent(event)


def _swap(old, new):
    """Put `new` where `old` is (layout, splitter or tab); returns how to undo it, or None."""
    parent = old.parentWidget()
    if parent is None:
        return None
    tabs = parent.parentWidget() if parent.parentWidget() is not None else None
    if isinstance(tabs, QTabWidget) and tabs.indexOf(old) >= 0:
        index = tabs.indexOf(old)
        current = tabs.currentIndex() == index
        text, icon, tip = tabs.tabText(index), tabs.tabIcon(index), tabs.tabToolTip(index)
        tabs.blockSignals(True)
        tabs.removeTab(index)
        tabs.insertTab(index, new, icon, text)
        tabs.setTabToolTip(index, tip)
        if current:
            tabs.setCurrentIndex(index)
        tabs.blockSignals(False)
        return True
    if isinstance(parent, QSplitter):
        index = parent.indexOf(old)
        sizes = parent.sizes()
        parent.replaceWidget(index, new)
        parent.setSizes(sizes)
        return True
    layout = parent.layout()
    if layout is not None and layout.replaceWidget(old, new, Qt.FindChildOption.FindChildrenRecursively) is not None:
        return True
    return None


def pop_out(widget, title):
    """Open `widget` in its own window, leaving a placeholder; returns the window (or None)."""
    for window in OPEN:
        if window.widget is widget:
            window.bring_to_front()
            return window
    owner = widget.window()
    window = GraphWindow(widget, title, owner)
    placeholder = Placeholder(window)
    size = widget.size()
    if _swap(widget, placeholder) is None:
        placeholder.deleteLater()
        window.deleteLater()
        return None
    window.home = placeholder
    window.layout().addWidget(widget)
    widget.show()
    b = getattr(widget, 'pop_out_button', None)
    if b is not None:
        b.setVisible(False)                                      # in its window it has nowhere to go
    placeholder.resize(size)
    OPEN.append(window)
    window.show()
    return window


def bring_back(window):
    """Return the graph to its place; the placeholder goes."""
    if window not in OPEN:
        return
    OPEN.remove(window)
    widget, placeholder = window.widget, window.home
    window.layout().removeWidget(widget)
    try:
        placed = _swap(placeholder, widget)
    except RuntimeError:                                         # its experiment was closed
        placed = None
    if placed is None:
        widget.setParent(None)
        widget.deleteLater()
    else:
        widget.show()
        b = getattr(widget, 'pop_out_button', None)
        if b is not None:
            b.setVisible(True)
            b.raise_()
        placeholder.deleteLater()


def close_all():
    for window in list(OPEN):
        window.close()


def windows_for(widget):
    """The graph windows opened from inside `widget` (an experiment)."""
    found = []
    for window in OPEN:
        home = window.home
        try:
            while home is not None and home is not widget:
                home = home.parentWidget()
        except RuntimeError:
            home = None
        if home is widget:
            found.append(window)
    return found
