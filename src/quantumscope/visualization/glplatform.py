"""Make PyOpenGL use the same windowing interface as Qt (v0.9.11 fix, Linux only).

PyOpenGL picks its interface from the session, not from Qt: on a Wayland desktop it chooses EGL
even when Qt runs through XWayland with GLX (the 'xcb' platform, which the NVIDIA setting and
run_nvidia.sh select). Mismatched, the 3-D views cannot talk to Qt's OpenGL context, and the
packaged app closed at start. Call opengl_environment() after the QApplication exists and before
anything imports OpenGL. This module imports neither OpenGL nor Qt.
"""
import os
import sys

QT_TO_PYOPENGL = {'xcb': 'glx', 'wayland': 'egl', 'wayland-egl': 'egl', 'eglfs': 'egl'}


def opengl_platform(qt_platform, environ=None, system=None):
    """The PYOPENGL_PLATFORM value for Qt's platform, or None to leave PyOpenGL's own choice
    (other systems, other Qt platforms, or a value the user set)."""
    environ = os.environ if environ is None else environ
    system = system or sys.platform
    if not system.startswith('linux') or environ.get('PYOPENGL_PLATFORM'):
        return None
    return QT_TO_PYOPENGL.get(qt_platform)


def opengl_environment(app):
    """Set PYOPENGL_PLATFORM to match the running QApplication; returns the value set, or None."""
    value = opengl_platform(app.platformName())
    if value:
        os.environ['PYOPENGL_PLATFORM'] = value
    return value
