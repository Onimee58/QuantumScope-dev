"""v0.9.5: the news bar, Report a problem and the crash catcher (QUANTUMSCOPE_GUI_TESTS=1)."""
import datetime
import io
import json
import os
import sys
import urllib.parse

import pytest

if os.environ.get('QUANTUMSCOPE_GUI_TESTS') != '1':
    pytest.skip('GUI tests are opt-in: set QUANTUMSCOPE_GUI_TESTS=1', allow_module_level=True)

QtWidgets = pytest.importorskip('PySide6.QtWidgets')

NOW = datetime.datetime(2027, 2, 1, 9, 0)


@pytest.fixture
def app():
    from quantumscope.gui import preferences as prefs
    keys = ('news/check', 'news/last_checked', 'news/cache', 'news/dismissed')
    for key in keys:
        prefs._settings().remove(key)
    yield QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    for key in keys:                                    # never leave 'weekly' behind for later tests
        prefs._settings().remove(key)


class _Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _file(email='help@quantumscope.example'):
    return json.dumps({'support_email': email, 'announcements': [
        {'id': 'workshop', 'title': 'Quantum computing for professionals', 'text': 'Two days, March 3–4.',
         'link': 'https://example.org/workshop'},
        {'id': 'path', 'title': 'A new learning path', 'text': ''}]}).encode()


def _wait(app, run):
    while run is not None and run.running():
        app.processEvents()
    app.processEvents()


def test_the_bar_asks_once_then_shows_one_announcement_at_a_time(app):
    from quantumscope.gui import preferences as prefs
    from quantumscope.gui.news_bar import NewsBar
    requests, opened = [], []

    def opener(request, timeout):
        requests.append(request.full_url)
        return _Response(_file())
    bar = NewsBar(opener=opener, now=lambda: NOW, open_url=opened.append)
    bar.show()
    assert bar.start() is None and bar.refresh() == 'ask' and not requests      # nothing read before consent
    assert bar.allow.isVisible() and 'Nothing about you is sent' in bar.message.text()
    _wait(app, bar.choose('weekly'))
    assert requests == ['https://raw.githubusercontent.com/Onimee58/QuantumScope/main/news.json']
    assert prefs.get('news/check') == 'weekly' and prefs.get('news/last_checked') == NOW.isoformat()
    assert bar.isVisible() and bar.message.text().startswith('Quantum computing for professionals')
    bar.more.click()
    assert opened == ['https://example.org/workshop']
    assert bar.start() is None and len(requests) == 1                          # not again within a week
    bar.close_button.click()
    assert bar.message.text() == 'A new learning path' and not bar.more.isVisible()   # no link, no button
    bar.close_button.click()
    assert not bar.isVisible() and prefs.get('news/dismissed') == ('workshop', 'path')
    later = NewsBar(opener=opener, now=lambda: NOW + datetime.timedelta(days=8))
    _wait(app, later.start())
    assert len(requests) == 2 and later.refresh() == 'none'                     # dismissed stays dismissed


def test_declining_or_being_offline(app):
    from quantumscope.gui import preferences as prefs
    from quantumscope.gui.news_bar import NewsBar
    calls = []

    def offline(request, timeout):
        calls.append(1)
        raise OSError('no network')
    bar = NewsBar(opener=offline, now=lambda: NOW)
    bar.show()
    bar.refresh()
    bar.decline.click()
    assert prefs.get('news/check') == 'never' and not bar.isVisible() and bar.start() is None and not calls
    prefs.set('news/cache', _file().decode())
    prefs.set('news/check', 'weekly')
    _wait(app, bar.start())
    assert calls == [1] and bar.refresh() == 'news'                             # offline: the last news still shows
    assert prefs.get('news/last_checked') == ''                                 # and it tries again next time


def test_report_dialog_shows_everything_and_sends_nothing_itself(app, monkeypatch, tmp_path):
    from quantumscope.gui import preferences as prefs
    from quantumscope.gui import report_dialog as R
    monkeypatch.setattr(QtWidgets.QMessageBox, 'information', lambda *a, **k: None)
    monkeypatch.setattr(prefs, 'default_folder', lambda store=None: str(tmp_path))
    opened = []
    dialog = R.ReportDialog(None, opener=opened.append)
    assert not dialog.email_button.isEnabled() and 'once an address is published' in dialog.note.text()
    prefs.set('news/cache', _file().decode())
    host = QtWidgets.QWidget()
    host.resize(300, 200)
    dialog = R.ReportDialog(host, opener=opened.append)
    assert dialog.email_button.isEnabled() and 'help@quantumscope.example' in dialog.email_button.toolTip()
    dialog.what.setPlainText('The 3-D view is blank\nafter training')
    assert 'The 3-D view is blank' in dialog.preview.toPlainText() and 'QuantumScope:' in dialog.preview.toPlainText()
    link = dialog.send_email()
    assert opened == [link] and link.startswith('mailto:help@quantumscope.example?subject=')
    assert urllib.parse.parse_qs(link.split('?', 1)[1])['body'] == [dialog.text()]
    assert QtWidgets.QApplication.clipboard().text() == dialog.text()
    assert dialog.screenshot_path and os.path.getsize(dialog.screenshot_path) > 0
    assert 'Attach it to the email' in dialog.sent_message
    issue = R.ReportDialog(host, opener=opened.append)
    issue.screenshot.setChecked(False)
    link = issue.send_github()
    assert link.startswith('https://github.com/Onimee58/QuantumScope/issues/new?title=') and issue.screenshot_path is None


def test_the_crash_catcher_offers_a_report_once_per_error(app, monkeypatch):
    from quantumscope.gui import report_dialog as R
    shown, reports = [], []

    class FakeBox:
        Icon = QtWidgets.QMessageBox.Icon
        ButtonRole = QtWidgets.QMessageBox.ButtonRole

        def __init__(self, parent):
            self.buttons = []

        def __getattr__(self, name):
            return lambda *a, **k: None

        def setInformativeText(self, text):
            shown.append(text)

        def addButton(self, text, role):
            self.buttons.append(text)
            return text

        def exec(self):
            return 0

        def clickedButton(self):
            return self.buttons[0]                                             # 'Report it…'
    monkeypatch.setattr(R, 'QMessageBox', FakeBox)
    monkeypatch.setattr(R.ReportDialog, 'exec', lambda self: reports.append(self.error))
    printed = []
    monkeypatch.setattr(sys, 'excepthook', lambda *args: printed.append(args[0]))
    hook = R.install_crash_catcher(None)
    try:
        for _ in range(2):                                                     # the same error twice
            try:
                {}['missing']
            except KeyError:
                hook(*sys.exc_info())
        app.processEvents()
        assert printed == [KeyError, KeyError]                                  # still printed for developers
        assert len(shown) == 1 and "KeyError: 'missing'" in shown[0]
        assert len(reports) == 1 and 'Traceback' in reports[0]['traceback']
        hook(KeyboardInterrupt, KeyboardInterrupt(), None)
        app.processEvents()
        assert len(shown) == 1 and printed[-1] is KeyboardInterrupt
    finally:
        sys.excepthook = hook.previous


def test_settings_page_holds_the_news_choice(app):
    from quantumscope.gui import preferences as prefs
    from quantumscope.gui.settings_dialog import SECTIONS, SettingsDialog
    calls = []

    class Host:
        def apply_preferences(self):
            calls.append(prefs.get('news/check'))
    d = SettingsDialog(Host())
    d.nav.setCurrentRow(SECTIONS.index('Updates and news'))
    d.news.setCurrentIndex(d.news.findData('never'))
    assert prefs.get('news/check') == 'never' and calls == ['never']
    prefs.set('news/dismissed', ('workshop',))
    prefs.restore_defaults()
    assert prefs.get('news/check') == 'ask' and prefs.get('news/dismissed') == ('workshop',)   # history is kept
