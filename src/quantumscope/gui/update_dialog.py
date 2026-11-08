"""The update check, step by step, only when the user asks (Settings → Updates or the ⓘ menu)."""
import subprocess
import tempfile
import time

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication, QDialog, QDialogButtonBox, QLabel, QMessageBox, QProgressDialog,
                               QTextBrowser, QVBoxLayout)

from quantumscope import __version__, updater

PERMISSION = ('QuantumScope will contact github.com to look for a newer release.\n\n'
              'Nothing about you or your files is sent. Continue?')


CANCELLED = object()


def _in_background(parent, title, text, work, maximum=0, on_progress=None, wait_after_cancel=False):
    """Run a network step in a worker thread behind a progress window with Cancel, so the window never
    freezes while GitHub is slow (v0.8.2). Returns the step's result, or CANCELLED; re-raises its error.
    wait_after_cancel: let the step finish its own clean-up after Cancel (a download deletes its file)."""
    from quantumscope.gui.background import Run
    dialog = QProgressDialog(text, 'Cancel', 0, maximum, parent)
    dialog.setWindowTitle(title)
    dialog.setWindowModality(Qt.WindowModality.WindowModal)
    dialog.setMinimumDuration(0)
    dialog.setValue(0)
    run = Run(work, on_progress=(lambda value: on_progress(dialog, value)) if on_progress else None).start()
    cancelled = False
    while run.running():
        if dialog.wasCanceled() and not cancelled:
            cancelled = True
            run.cancel()
            if not wait_after_cancel:
                break                                          # an answer arriving later is ignored
        QApplication.processEvents()
        time.sleep(0.01)
    dialog.close()
    if cancelled:
        if wait_after_cancel:
            while run.running():
                QApplication.processEvents()
                time.sleep(0.01)
        return CANCELLED
    if run.error is not None:
        raise run.error[0]
    return run.result


def _release_dialog(parent, release):
    dialog = QDialog(parent)
    dialog.setWindowTitle('Update available')
    layout = QVBoxLayout(dialog)
    layout.addWidget(QLabel(f'<b>QuantumScope {release.label}</b> is available (you have {__version__}).'))
    notes = QTextBrowser()
    notes.setOpenExternalLinks(True)
    notes.setMarkdown(release.notes or 'No release notes.')
    layout.addWidget(notes, 1)
    buttons = QDialogButtonBox()
    update = buttons.addButton('Update now', QDialogButtonBox.ButtonRole.AcceptRole)
    buttons.addButton('Not now', QDialogButtonBox.ButtonRole.RejectRole)
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)
    dialog.resize(640, 480)
    dialog.update_button = update
    return dialog


def check_for_updates(parent, opener=None, platform=None, frozen=None, folder=None, run=None, relaunch=None):
    """The whole flow. Returns a short outcome string (also used by tests)."""
    if QMessageBox.question(parent, 'Check for updates', PERMISSION,
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                            QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
        return 'declined'
    current = updater.parse_version(__version__)
    try:
        release = _in_background(parent, 'Check for updates', 'Contacting GitHub…',
                                 lambda report, cancelled: updater.check(current, platform, opener))
    except updater.UpdateError as exc:
        QMessageBox.warning(parent, 'Check for updates', str(exc))
        return 'error'
    if release is CANCELLED:
        return 'cancelled'
    if release is None:
        QMessageBox.information(parent, 'Check for updates', f'QuantumScope {__version__} is the latest version.')
        return 'up to date'
    if _release_dialog(parent, release).exec() != QDialog.DialogCode.Accepted:
        return 'not now'
    kind, _, message = updater.install_plan('', platform, frozen)
    if kind == 'source':                                   # running from a git checkout: nothing to download
        QMessageBox.information(parent, 'Update QuantumScope', message)
        return 'source'
    if not release.installer:
        QMessageBox.information(parent, 'Update QuantumScope', 'This release has no installer for your system. '
                                f'Download it from the release page:\n{release.page}')
        return 'no installer'
    target = folder or tempfile.mkdtemp(prefix='quantumscope-update-')

    def fetch(report, cancelled):                              # the worker: downloads and verifies
        def each(done, total):
            report((done, total))
            return not cancelled()
        return updater.download(release, target, each, opener)

    def show(dialog, value):
        done, total = value
        dialog.setValue(int(100 * done / total) if total else 0)
    try:
        path = _in_background(parent, 'Update QuantumScope', f'Downloading {release.installer["name"]}…', fetch,
                              maximum=100, on_progress=show, wait_after_cancel=True)
    except updater.UpdateError as exc:
        QMessageBox.warning(parent, 'Update QuantumScope', str(exc))
        return 'download failed'
    if path is CANCELLED:
        return 'cancelled'
    kind, command, message = updater.install_plan(path, platform, frozen)
    if QMessageBox.question(parent, 'Install the update',
                            f'The download was verified against the release checksum.\n\n{message}\n\nInstall now?',
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                            QMessageBox.StandardButton.Yes) != QMessageBox.StandardButton.Yes:
        return 'downloaded'
    try:
        process = (run or subprocess.Popen)(command)
    except OSError as exc:
        QMessageBox.warning(parent, 'Update QuantumScope', f'The installer could not be started ({exc}). '
                            f'It is saved at:\n{path}\n\nOn a managed computer you may need an administrator.')
        return 'install failed'
    key = updater.platform_key(platform)
    if kind == 'run' and key == 'windows':
        QApplication.instance().quit()                     # the installer replaces the running app
        return 'installing'
    if kind == 'run' and key == 'linux' and hasattr(process, 'poll'):
        return _wait_for_linux_install(parent, process, release, path, relaunch)
    return 'installing'


def _wait_for_linux_install(parent, process, release, path, relaunch=None):
    """Wait for pkexec/apt-get (collecting its result: no 'defunct' process is left behind),
    then offer to restart into the new version or explain what went wrong."""
    waiting = QProgressDialog(f'Installing QuantumScope {release.label}…\n'
                              'Enter your password if Ubuntu asks for it.', None, 0, 0, parent)
    waiting.setWindowTitle('Update QuantumScope')
    waiting.setMinimumDuration(0)
    waiting.show()
    while process.poll() is None:
        QApplication.processEvents()
        time.sleep(0.05)
    waiting.close()
    code = process.returncode
    if code == 0:
        if QMessageBox.question(parent, 'Update QuantumScope',
                                f'QuantumScope {release.label} is installed.\n\nRestart now to use it?',
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                QMessageBox.StandardButton.Yes) == QMessageBox.StandardButton.Yes:
            (relaunch or _relaunch)()
            return 'restarting'
        QMessageBox.information(parent, 'Update QuantumScope',
                                f'QuantumScope {release.label} will be used the next time you start it.')
        return 'installed'
    if code in (126, 127):                                 # pkexec: password dialog dismissed or not allowed
        QMessageBox.information(parent, 'Update QuantumScope',
                                'The installation was cancelled (no password was given), so nothing changed.\n\n'
                                f'The verified download is saved at:\n{path}')
        return 'install cancelled'
    QMessageBox.warning(parent, 'Update QuantumScope',
                        f'The installer stopped with an error (code {code}), so nothing changed.\n\n'
                        f'You can install the verified download yourself:\n    sudo apt install {path}')
    return 'install failed'


def _relaunch():
    """Start the newly installed QuantumScope and close this one (as Settings' restart does)."""
    import sys
    from pathlib import Path
    from quantumscope.gui import preferences as prefs
    command = [sys.executable] if getattr(sys, 'frozen', False) else [sys.executable, '-m', 'quantumscope']
    subprocess.Popen(command, env=prefs.restart_environment(), start_new_session=True, cwd=str(Path.home()),
                     close_fds=True)
    QApplication.instance().quit()
