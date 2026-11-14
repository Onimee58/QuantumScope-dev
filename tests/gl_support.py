"""For GUI tests that draw 3-D views (v0.9.11): they need a real OpenGL context.

Qt's 'offscreen' platform has none, so these tests run on a display; with no display,
tools/run_gui_tests.sh starts a virtual one (xvfb-run) when it can. Elsewhere they are skipped.
"""
import pytest


def opengl_app():
    """The QApplication, or skip the test if this platform cannot create an OpenGL context."""
    from PySide6.QtGui import QOpenGLContext
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    if app.platformName() in ('offscreen', 'minimal') or not QOpenGLContext().create():
        pytest.skip('needs OpenGL: run on a display (tools/run_gui_tests.sh uses xvfb-run when there is none)')
    return app
