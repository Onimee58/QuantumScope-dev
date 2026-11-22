"""Report a problem, and the crash catcher (v0.9.5).

The dialog shows everything a report will contain before anything leaves the computer, and sends
nothing itself: Email opens the user's email program, GitHub opens a new-issue page in the browser,
both filled in. The full report is always copied to the clipboard as well (long reports are
shortened in the links, which have length limits).
"""
import datetime
import os
import sys

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtGui import QDesktopServices, QGuiApplication
from PySide6.QtWidgets import (QCheckBox, QDialog, QFormLayout, QHBoxLayout, QLabel, QMessageBox, QPlainTextEdit,
                               QPushButton, QVBoxLayout)

from quantumscope import report


def support_email():
    """The support address from the last news read ('' until the maintainers publish one)."""
    from quantumscope import news
    from quantumscope.gui import preferences as prefs
    cached = prefs.get('news/cache')
    if not cached:
        return ''
    try:
        return news.parse(cached)['support_email']
    except news.NewsError:
        return ''


def _where(window):
    """The area and tab the user is looking at, by their visible names."""
    try:
        area = window.categories.tabText(window.categories.currentIndex()).strip(' ⚛◈▦◇∑')
        tabs = window.categories.currentWidget()
        return area.strip(), tabs.tabText(tabs.currentIndex()).strip()
    except AttributeError:
        return '', ''


class ReportDialog(QDialog):
    def __init__(self, window=None, error=None, opener=None):
        super().__init__(window)
        self.window_, self.error = window, error
        self.open_url = opener or (lambda url: QDesktopServices.openUrl(QUrl(url)))
        self.screenshot_path = None
        self.setWindowTitle('Report a problem')
        self.resize(640, 620)
        v = QVBoxLayout(self)
        intro = QLabel('Tell us what went wrong. <b>QuantumScope sends nothing itself</b>: it fills in an email or '
                       'a GitHub issue for you to check and send, and copies the report to your clipboard.')
        intro.setWordWrap(True)
        v.addWidget(intro)
        if error:
            crash = QLabel(f'<b>QuantumScope ran into an unexpected error:</b> {error.get("summary", "")}<br>'
                           'Its details are included below. What were you doing when it happened?')
            crash.setWordWrap(True)
            v.addWidget(crash)
        form = QFormLayout()
        self.what = QPlainTextEdit()
        self.what.setPlaceholderText('What did you do, and what happened? The first line becomes the title.')
        self.what.setFixedHeight(90)
        form.addRow('What happened', self.what)
        self.expected = QPlainTextEdit()
        self.expected.setPlaceholderText('Optional')
        self.expected.setFixedHeight(56)
        form.addRow('What you expected', self.expected)
        v.addLayout(form)
        self.screenshot = QCheckBox('Save a screenshot of the QuantumScope window to attach')
        self.screenshot.setChecked(window is not None)
        self.screenshot.setEnabled(window is not None)
        v.addWidget(self.screenshot)
        v.addWidget(QLabel('The report (everything that will be sent):'))
        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        v.addWidget(self.preview, 1)
        self.address = support_email()
        self.note = QLabel()
        self.note.setWordWrap(True)
        self.note.setObjectName('muted')
        v.addWidget(self.note)
        row = QHBoxLayout()
        self.copy_button = QPushButton('Copy report')
        self.email_button = QPushButton('Send by email…')
        self.github_button = QPushButton('Open a GitHub issue…')
        self.email_button.setDefault(bool(self.address))
        self.email_button.setEnabled(bool(self.address))
        self.email_button.setToolTip(f'Opens your email program, addressed to {self.address}' if self.address else
                                     'No support address has been published yet: use GitHub, or copy the report')
        self.github_button.setToolTip('Opens a new issue in your browser. Needs a GitHub account; issues are public.')
        for button in (self.copy_button, self.email_button, self.github_button):
            row.addWidget(button)
        row.addStretch()
        close = QPushButton('Close')
        close.clicked.connect(self.reject)
        row.addWidget(close)
        v.addLayout(row)
        self.copy_button.clicked.connect(lambda: self.copy())
        self.email_button.clicked.connect(lambda: self.send_email())
        self.github_button.clicked.connect(lambda: self.send_github())
        for box in (self.what, self.expected):
            box.textChanged.connect(self._refresh)
        self._refresh()

    # ---- the report ---------------------------------------------------------------------------
    def info(self):
        area, tab = _where(self.window_) if self.window_ is not None else ('', '')
        return report.diagnostics(area, tab)

    def text(self):
        return report.compose(self.what.toPlainText(), self.expected.toPlainText(), self.info(), self.error)

    def title(self):
        return report.title_for(self.what.toPlainText(), self.error)

    def _refresh(self, *_):
        self.preview.setPlainText(self.text())
        self.note.setText('Email goes privately to the QuantumScope team. GitHub issues are public: leave out '
                          'anything private.' if self.address else
                          'GitHub issues are public: leave out anything private. (Email support will appear here '
                          'once an address is published.)')

    # ---- sending ------------------------------------------------------------------------------
    def copy(self):
        QGuiApplication.clipboard().setText(self.text())
        return self.text()

    def save_screenshot(self):
        """Save the main window as a PNG for the user to attach; returns its path (or None)."""
        if self.window_ is None or not self.screenshot.isChecked():
            return None
        from quantumscope.gui import preferences as prefs
        stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        path = os.path.join(prefs.default_folder(), f'QuantumScope-report-{stamp}.png')
        if self.window_.grab().save(path, 'PNG'):
            self.screenshot_path = path
            return path
        return None

    def _send(self, link, shortened, where):
        self.copy()
        shot = self.save_screenshot()
        self.open_url(link)
        lines = [f'Your {where} has been opened with the report filled in. Check it and press Send.']
        if shortened:
            lines.append('The report was too long for the link, so it was shortened: paste the full report (on '
                         'your clipboard) in its place.')
        if shot:
            lines.append(f'A screenshot was saved to:\n{shot}\nAttach it to the {where}'
                         + (' (drag it into the issue).' if where == 'GitHub issue' else '.'))
        self.sent_message = '\n\n'.join(lines)
        QMessageBox.information(self, 'Report a problem', self.sent_message)
        self.accept()
        return link

    def send_email(self):
        if not self.address:
            return None
        link, cut = report.mail_link(self.address, self.title(), self.text())
        return self._send(link, cut, 'email')

    def send_github(self):
        link, cut = report.issue_link(self.title(), self.text())
        return self._send(link, cut, 'GitHub issue')


# ---- the crash catcher -------------------------------------------------------------------------------
CRASH = {'previous': '', 'handle': None}


def crash_log_path():
    from quantumscope.gui.preferences import data_folder
    return os.path.join(data_folder(), 'last-crash.log')


def enable_crash_log():
    """Keep what the last session's crash left (if anything), then record this session's: a crash in
    compiled code (not a Python error) writes its trace to last-crash.log (v1.1.1)."""
    import faulthandler
    path = crash_log_path()
    try:
        with open(path, encoding='utf-8', errors='replace') as f:
            CRASH['previous'] = f.read(64 * 1024).strip()
    except OSError:
        CRASH['previous'] = ''
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        CRASH['handle'] = open(path, 'w', encoding='utf-8')
        faulthandler.enable(CRASH['handle'])
    except (OSError, RuntimeError):
        pass


def offer_crash_report(window):
    """After a session that ended without closing normally: offer to report it."""
    box = QMessageBox(window)
    box.setIcon(QMessageBox.Icon.Warning)
    box.setWindowTitle('QuantumScope closed unexpectedly')
    box.setText('QuantumScope did not close normally last time.')
    box.setInformativeText('If it closed by itself, reporting it helps us fix it: say what you were doing (for '
                           'example, training on a large dataset). A computer that ran out of memory can also stop '
                           'programs without warning.')
    report_button = box.addButton('Report it…', QMessageBox.ButtonRole.AcceptRole)
    box.addButton('Not now', QMessageBox.ButtonRole.RejectRole)
    box.exec()
    if box.clickedButton() is report_button:
        trace = CRASH['previous'] or '(no trace was recorded: the system may have stopped QuantumScope, as it does '\
                                     'when memory runs out)'
        ReportDialog(window, {'summary': 'QuantumScope closed unexpectedly', 'traceback': trace}).exec()


def install_crash_catcher(window):
    """An unexpected error no longer just prints to a hidden console: QuantumScope keeps running and
    offers to report it (once per distinct error, never while a report is already open)."""
    previous = sys.excepthook
    seen = set()
    state = {'open': False}

    def offer(error):
        if state['open']:
            return
        state['open'] = True
        try:
            box = QMessageBox(window)
            box.setIcon(QMessageBox.Icon.Warning)
            box.setWindowTitle('Something went wrong')
            box.setText('QuantumScope ran into an unexpected problem and carried on.')
            box.setInformativeText(f'{error["summary"]}\n\nReporting it helps us fix it. Your work is still open; '
                                   f'if something looks wrong, save it and restart QuantumScope.')
            report_button = box.addButton('Report it…', QMessageBox.ButtonRole.AcceptRole)
            box.addButton('Not now', QMessageBox.ButtonRole.RejectRole)
            box.exec()
            if box.clickedButton() is report_button:
                ReportDialog(window, error).exec()
        finally:
            state['open'] = False

    def hook(kind, value, tb):
        if issubclass(kind, KeyboardInterrupt):
            return previous(kind, value, tb)
        previous(kind, value, tb)                                  # still printed for developers
        error = report.remember_error(kind, value, tb)
        signature = (kind.__name__, error['traceback'].splitlines()[-2:].__str__())
        if signature in seen:
            return
        seen.add(signature)
        QTimer.singleShot(0, lambda: offer(error))

    sys.excepthook = hook
    hook.previous = previous
    hook.offer = offer
    return hook
