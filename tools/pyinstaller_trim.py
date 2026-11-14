"""Leave out the parts of Qt that QuantumScope never uses (v0.9.10).

PyInstaller bundles everything the PySide6 wheel might need. QuantumScope draws with Qt Widgets and
OpenGL; it never uses Qt Quick or QML (pulled in only by the on-screen virtual keyboard plugin),
the PDF image plugin, Qt's data-visualization module, or the platform plugins for embedded Linux
devices without a desktop. Qt's own translations only translate Qt's built-in dialogs, while
QuantumScope's interface is English.

The spec step (added by tools/pyinstaller_compiled.py) calls trim() after the analysis.
"""
import re

# Matched against each bundled file's destination path.
UNUSED = (                                         # Linux libQt6X.so, Windows Qt6X.dll, macOS QtX.framework
    r'qtvirtualkeyboardplugin\.',                  # the virtual keyboard, which needs Qt Quick and QML
    r'(^|/)(lib)?Qt6?VirtualKeyboard',
    r'(^|/)(lib)?Qt6?Quick',
    r'(^|/)(lib)?Qt6?Qml',
    r'imageformats/(lib)?qpdf\.', r'(^|/)(lib)?Qt6?Pdf',      # PDF as an image format
    r'(^|/)(lib)?Qt6?DataVisualization', r'QtDataVisualization\.',
    r'plugins/egldeviceintegrations/',             # embedded Linux without a desktop
    r'plugins/platforms/libq(eglfs|linuxfb|vnc|vkkhrdisplay)\.',
    r'(^|/)libQt6EglFs',
    r'PySide6/Qt/translations/',                   # Qt's own dialog translations
)
# Modules to keep out of the analysis entirely (pyvistaqt's qtpy lists every Qt module).
EXCLUDE_MODULES = ('PySide6.QtDataVisualization', 'qtpy.QtDataVisualization', 'qtpy.tests',
                   'PySide6.QtQuick', 'PySide6.QtQml')
# Never removed, whatever the patterns say: what the app needs to start and draw.
REQUIRED = (r'(^|/)(lib)?Qt6?(Core|Gui|Widgets|OpenGL|OpenGLWidgets|DBus|Network|Svg|PrintSupport)[./]',
            r'plugins/platforms/(lib)?q(xcb|wayland|windows|cocoa|offscreen|minimal)')


def unused(path):
    path = path.replace('\\', '/')
    return any(re.search(p, path) for p in UNUSED) and not any(re.search(p, path) for p in REQUIRED)


def trim(analysis):
    """Drop unused Qt files from the analysis; returns the dropped destination paths."""
    dropped = []
    for toc in (analysis.binaries, analysis.datas):
        kept = [entry for entry in toc if not unused(entry[0])]
        dropped += [entry[0] for entry in toc if unused(entry[0])]
        toc[:] = kept
    print(f'QuantumScope: left out {len(dropped)} unused Qt files')
    return dropped


def exclude_arguments():
    return [f'--exclude-module={name}' for name in EXCLUDE_MODULES]


if __name__ == '__main__':
    print(' '.join(exclude_arguments()))
