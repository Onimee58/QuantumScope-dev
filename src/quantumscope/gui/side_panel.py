"""Side panels that fold to a narrow strip instead of disappearing (v0.9.15).

A control panel dragged shut used to vanish without a trace. Wrapped in a CollapsiblePanel, it
folds to a strip with its name written down the side and a button to open it again; the choice is
remembered between sessions.

v0.9.17: the groups inside a panel (Data, Preprocessing, …) fold too: a click on a group's title
folds it to that title, and the choice is remembered.
"""
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (QFrame, QGroupBox, QHBoxLayout, QScrollArea, QSplitter, QToolButton, QVBoxLayout,
                               QWidget)

STRIP = 28                                     # width of the folded panel (v0.9.17: 24 → 28)
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

    def __init__(self, content, title, key=None, side='left', parent=None, fold_groups=True):
        super().__init__(parent)
        self.content, self.title, self.key, self.side = content, title, key, side
        self._sizes = None
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        self.strip = QWidget()
        self.strip.setObjectName('panelStrip')
        self.strip.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.strip.setFixedWidth(STRIP)
        strip = QVBoxLayout(self.strip)
        strip.setContentsMargins(0, 3, 0, 3)
        strip.setSpacing(6)
        self.button = QToolButton()                       # v0.9.17: a filled button, easy to see
        self.button.setObjectName('panelToggle')
        self.button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.button.setFixedSize(STRIP - 4, 34)
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
        self.groups = [foldable(g, f'{key}/{g.title()}' if key else None)
                       for g in (content.findChildren(QGroupBox) if fold_groups else ())
                       if not g.isCheckable() and g.title()]
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
        opening, closing = ('»', '«') if self.side == 'left' else ('«', '»')
        self.button.setText(opening if c else closing)
        self.button.setToolTip(f'Show {self.title}' if c else f'Hide {self.title}: it folds to this strip')
        if c:
            self.setFixedWidth(STRIP)
        else:
            self.setMinimumWidth(0)
            self.setMaximumWidth(UNLIMITED)


def scrolling(panel):
    """A control panel that scrolls up and down when the window is too short for it (v0.9.17)."""
    area = QScrollArea()
    area.setWidget(panel)
    area.setWidgetResizable(True)
    area.setFrameShape(QFrame.Shape.NoFrame)
    area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    bar = area.verticalScrollBar().sizeHint().width() + 2
    area.setMinimumWidth(panel.minimumSizeHint().width() + bar)
    if panel.maximumWidth() < UNLIMITED:                            # a column of a set width stays so
        area.setMaximumWidth(panel.maximumWidth() + bar)
    return area


def foldable(group, key=None):
    """Let a group box fold to its title: a click on the title (with its ▾/▸) hides or shows what is
    inside. The group's contents move into an inner widget, so rows hidden on purpose stay hidden.
    Returns the group (group.fold is the inner widget)."""
    if getattr(group, 'fold', None) is not None:
        return group
    inner = QWidget()
    layout = group.layout()
    if layout is not None:
        inner.setLayout(layout)                               # takes the layout and its widgets along
    outer = QVBoxLayout(group)
    outer.setContentsMargins(0, 0, 0, 0)
    outer.addWidget(inner)
    group.fold = inner
    group.setProperty('fold', True)
    group.setCheckable(True)
    group.setChecked(True)
    group.setToolTip('Click the title to fold or unfold this group')

    def show(opened):
        inner.setVisible(opened)
        if key:
            _remember(f'groups/{key}', not opened, prefix='')
    group.toggled.connect(show)
    if key and _remembered(f'groups/{key}', prefix=''):
        group.setChecked(False)
    return group


def _remembered(key, prefix='panels/'):
    try:
        from quantumscope.gui import preferences as prefs
        return str(prefs._settings().value(f'{prefix}{key}', 'false')).lower() == 'true'
    except Exception:                                     # settings are a convenience here
        return False


def _remember(key, collapsed, prefix='panels/'):
    try:
        from quantumscope.gui import preferences as prefs
        store = prefs._settings()
        store.setValue(f'{prefix}{key}', bool(collapsed))
        store.sync()
    except Exception:
        pass


def wrap_in_splitter(splitter, index, title, key, fold_groups=True):
    """Wrap the splitter's widget at `index` in a CollapsiblePanel (in place) and stop the splitter
    from collapsing it to nothing."""
    content = splitter.widget(index)
    sizes = splitter.sizes()
    panel = CollapsiblePanel(content, title, key, side='left' if index == 0 else 'right', fold_groups=fold_groups)
    splitter.insertWidget(index, panel)
    splitter.setCollapsible(index, False)
    splitter.setStretchFactor(index, 0)                   # spare width goes to the main view
    for other in range(splitter.count()):
        if other != index:
            splitter.setStretchFactor(other, 1)
    if sizes and all(sizes):                               # sizes are known only once laid out
        splitter.setSizes(sizes)
    return panel
