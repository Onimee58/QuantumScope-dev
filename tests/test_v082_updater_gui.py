"""v0.8.2: the update window never freezes while GitHub is slow, and Cancel works (opt-in GUI tests)."""
import os
import time

import pytest

from test_v070_updater import Response, github

if os.environ.get('QUANTUMSCOPE_GUI_TESTS') != '1':
    pytest.skip('GUI tests are opt-in: set QUANTUMSCOPE_GUI_TESTS=1', allow_module_level=True)

QtWidgets = pytest.importorskip('PySide6.QtWidgets')


@pytest.fixture(scope='module')
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

def slow(seconds, then):
    def opener(request, timeout=None):
        time.sleep(seconds)
        return then(request, timeout)
    return opener

def cancel_when(label, after_ticks=4):
    """Press Cancel on the progress window whose text starts with `label`, once it has been visible
    for a few ticks (a repeating check: the window may appear only after an earlier step)."""
    from PySide6.QtCore import QTimer
    seen = []

    def look():
        for widget in QtWidgets.QApplication.topLevelWidgets():
            if (isinstance(widget, QtWidgets.QProgressDialog) and widget.isVisible()
                    and widget.labelText().startswith(label)):
                seen.append(1)
                if len(seen) == after_ticks:
                    widget.cancel()
    timer = QTimer()
    timer.timeout.connect(look)
    timer.start(100)
    return timer, seen

@pytest.fixture
def quiet(monkeypatch):
    """Answer Yes to questions; record (never block on) information and warnings."""
    shown = []
    monkeypatch.setattr(QtWidgets.QMessageBox, 'question',
                        staticmethod(lambda *a, **k: QtWidgets.QMessageBox.StandardButton.Yes))
    for kind in ('information', 'warning'):
        monkeypatch.setattr(QtWidgets.QMessageBox, kind, staticmethod(lambda *a, **k: shown.append(a[2])))
    return shown

def test_the_window_stays_responsive_while_github_is_slow(app, monkeypatch, quiet):
    from PySide6.QtCore import QTimer
    from quantumscope.gui import update_dialog
    monkeypatch.setattr(update_dialog, '__version__', '99.0.0')         # nothing newer: "up to date"
    ticks = []
    timer = QTimer()
    timer.timeout.connect(lambda: ticks.append(1))
    timer.start(50)
    start = time.perf_counter()
    outcome = update_dialog.check_for_updates(None, opener=slow(1.5, github()), platform='linux')
    timer.stop()
    assert outcome == 'up to date' and time.perf_counter() - start >= 1.5
    assert len(ticks) >= 15                                            # the event loop kept running

def test_cancel_while_checking_and_while_downloading(app, monkeypatch, quiet, tmp_path):
    from quantumscope.gui import update_dialog
    monkeypatch.setattr(update_dialog, '__version__', '0.6.2')          # an older version is installed
    timer, seen = cancel_when('Contacting GitHub', after_ticks=3)
    start = time.perf_counter()
    assert update_dialog.check_for_updates(None, opener=slow(5, github()), platform='linux') == 'cancelled'
    timer.stop()
    assert seen and time.perf_counter() - start < 2                    # no waiting for GitHub's late answer
    monkeypatch.setattr(update_dialog, '_release_dialog',
                        lambda parent, release: type('D', (), {'exec': lambda self: QtWidgets.QDialog.DialogCode.Accepted})())

    def trickle(request, timeout=None):                                # a slow but finite download
        if 'api.github.com' in request.full_url or request.full_url.endswith('.sha'):
            return github()(request, timeout)

        class Slow(Response):
            def read(self, n=-1):
                time.sleep(0.05)
                return b'y' * 1024
        return Slow(b'', {'Content-Length': str(400 * 1024)})
    timer, seen = cancel_when('Downloading')
    outcome = update_dialog.check_for_updates(None, opener=trickle, platform='linux', frozen=True,
                                              folder=str(tmp_path))
    timer.stop()
    assert seen, 'the download window never appeared'
    assert outcome == 'cancelled' and os.listdir(tmp_path) == []        # no partial file left behind
