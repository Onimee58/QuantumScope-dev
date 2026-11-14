"""The start-up splash: only the Q, on a transparent background, while QuantumScope loads."""
from importlib.resources import files

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QGuiApplication, QPainter
from PySide6.QtWidgets import QWidget

SIZE = 220


class Splash(QWidget):
    """A frameless, see-through window with the QuantumScope mark (no box behind it). Desktops
    without a compositor (rare) show the transparent part as a plain colour instead."""

    def __init__(self):
        super().__init__(None, Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint
                         | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedSize(SIZE, SIZE)
        self.painted = False
        self.renderer = None
        try:
            from PySide6.QtSvg import QSvgRenderer
            self.renderer = QSvgRenderer(str(files('quantumscope').joinpath('assets/quantumscope-mark.svg')))
        except ImportError:                                   # no SVG module: the PNG icon instead
            pass
        screen = QGuiApplication.primaryScreen()
        if screen is not None:
            area = screen.availableGeometry()
            self.move(area.center().x() - SIZE // 2, area.center().y() - SIZE // 2)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.fillRect(self.rect(), Qt.GlobalColor.transparent)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        if self.renderer is not None and self.renderer.isValid():
            self.renderer.render(painter, QRectF(8, 8, SIZE - 16, SIZE - 16))
        else:
            from PySide6.QtGui import QPixmap
            painter.drawPixmap(self.rect().adjusted(8, 8, -8, -8),
                               QPixmap(str(files('quantumscope').joinpath('assets/quantumscope-256.png'))))
        painter.end()
        self.painted = True


WAIT = 0.5                                                    # seconds, at most, for the window system


def show_splash(app, wait=WAIT):
    """Show the splash before the slow imports, and return it (None if it cannot show).

    On Windows a new window is on screen and painted almost at once. On Linux (X11, Wayland) and
    macOS, showing a window is asynchronous: the window system maps it a moment later and only then
    asks for it to be painted. So keep handling events until the splash is really exposed and
    painted, for at most `wait` seconds; before v0.8.4 three quick passes ended before that on Linux,
    and the slow imports then kept the splash from ever painting."""
    import time
    try:
        splash = Splash()
        splash.show()
        splash.raise_()
        deadline = time.monotonic() + wait
        while time.monotonic() < deadline:
            app.processEvents()
            handle = splash.windowHandle()
            if splash.painted and handle is not None and handle.isExposed():
                break
            if handle is not None and handle.isExposed() and not splash.painted:
                splash.repaint()                              # exposed: paint now, not later
            time.sleep(0.005)
        app.processEvents()                                   # deliver the painted frame
        return splash
    except Exception:                                         # noqa: BLE001 - a splash must never stop start-up
        return None
