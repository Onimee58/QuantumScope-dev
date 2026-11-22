"""The license window (v1.0.0): QuantumScope opens only with a valid license file.

Shown at start when there is no license in use, or the one in use has ended, and from About →
Change license…. The file chosen is checked, then a copy is kept in QuantumScope's data folder, so
it is asked for once per computer.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QFileDialog, QFrame, QLabel, QPushButton, QVBoxLayout)

from quantumscope.licensing import check as L


def _folder():
    from quantumscope.gui.preferences import data_folder
    return data_folder()


def current():
    """(License, reason) for the license in use; License is None when there is none that works."""
    return L.installed(_folder())


class LicenseDialog(QDialog):
    def __init__(self, reason='', parent=None, change=False):
        super().__init__(parent)
        self.license = None
        self.setWindowTitle('QuantumScope license')
        self.setMinimumWidth(520)
        self.setAcceptDrops(True)
        root = QVBoxLayout(self)
        root.setContentsMargins(26, 22, 26, 18)
        root.setSpacing(12)
        title = QLabel('Change the license' if change else 'Add your QuantumScope license')
        title.setStyleSheet('font-size: 19px; font-weight: 700;')
        root.addWidget(title)
        text = QLabel('QuantumScope opens with a license file, which your instructor gives you: a file named '
                      '<b>QuantumScope-license-….qslicense</b>. Choose it below, or drop it on this window. '
                      'It is checked on this computer, without the internet, and asked for only once.')
        text.setWordWrap(True)
        root.addWidget(text)
        self.status = QLabel(reason)
        self.status.setWordWrap(True)
        self.status.setObjectName('licenseStatus')
        self.status.setStyleSheet('color: #e8a33d;')
        self.status.setVisible(bool(reason))
        root.addWidget(self.status)
        line = QFrame()
        line.setObjectName('divider')
        root.addWidget(line)
        self.choose = QPushButton('Choose the license file…')
        self.choose.setDefault(True)
        self.choose.clicked.connect(lambda: self.add())
        root.addWidget(self.choose, 0, Qt.AlignmentFlag.AlignLeft)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel if change
                                   else QDialogButtonBox.StandardButton.Close)
        if not change:
            buttons.button(QDialogButtonBox.StandardButton.Close).setText('Quit')
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def add(self, path=None):
        """Check and keep the license at `path` (asks for it when not given); True if accepted."""
        if path is None:
            path, _ = QFileDialog.getOpenFileName(self, 'Choose your QuantumScope license', '',
                                                  f'QuantumScope license (*{L.SUFFIX});;All files (*)')
            if not path:
                return False
        try:
            self.license = L.install(path, _folder())
        except L.LicenseError as exc:
            self.status.setText(str(exc))
            self.status.setVisible(True)
            return False
        self.accept()
        return True

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        if urls:
            self.add(urls[0])


def require_license(splash=None):
    """At start: the license in use, or the license window until one is added. None: quit."""
    lic, reason = current()
    if lic is not None:
        return lic
    if splash is not None:
        splash.close()
    dialog = LicenseDialog(reason)
    dialog.exec()
    return dialog.license


def open_main_window(app, splash, window_class):
    """Check the license (asking for one if needed), then open QuantumScope's window; None when no
    license was added. Kept here, in a compiled module, rather than in the start script."""
    lic = require_license(splash)
    if lic is None:
        return None
    window = window_class()
    window.license = lic
    try:   # follow the operating system's light/dark switch when "Follow system" is chosen
        app.styleHints().colorSchemeChanged.connect(window._follow_system_theme)
    except AttributeError:
        pass
    from quantumscope.gui.report_dialog import install_crash_catcher
    install_crash_catcher(window)                     # unexpected errors offer a report (v0.9.5)
    window.show()
    if splash is not None:
        splash.close()
    window.offer_recovery()
    if getattr(window, 'previous_session_crashed', False):   # v1.1.1: it closed unexpectedly last time
        from quantumscope.gui.report_dialog import offer_crash_report
        offer_crash_report(window)
    window.start_news()                               # asks once; then reads the news weekly, if allowed
    return window
