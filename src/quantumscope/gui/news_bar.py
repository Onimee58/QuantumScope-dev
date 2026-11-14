"""The announcement bar under the header (v0.9.5).

The first time QuantumScope starts, the bar asks once whether it may read the QuantumScope news (a
public file on github.com) once a week. If allowed, the newest current announcement appears here,
one at a time; closing it hides it for good. Settings → Updates and news changes the choice.
"""
import datetime

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QToolButton

from quantumscope import __version__, news
from quantumscope.gui import preferences as prefs

ASK = ('Allow QuantumScope to read its news on github.com once a week? You will see announcements of new '
       'courses, workshops and features here, and Report a problem learns the support email address. '
       'Nothing about you is sent.')


class NewsBar(QFrame):
    def __init__(self, parent=None, opener=None, now=None, open_url=None):
        super().__init__(parent)
        self.setObjectName('newsBar')
        self.opener = opener                                       # replaced in tests
        self.now = now or datetime.datetime.now
        self.open_url = open_url or (lambda url: QDesktopServices.openUrl(QUrl(url)))
        self.shown = None
        self.run = None
        row = QHBoxLayout(self)
        row.setContentsMargins(14, 6, 8, 6)
        self.message = QLabel()
        self.message.setWordWrap(True)
        self.message.setTextFormat(Qt.TextFormat.PlainText)    # announcements are text, never markup
        row.addWidget(self.message, 1)
        self.allow = QPushButton('Allow')
        self.decline = QPushButton('No thanks')
        self.more = QPushButton('Learn more ↗')
        self.close_button = QToolButton()
        self.close_button.setText('✕')
        self.close_button.setToolTip('Close this announcement (it will not come back)')
        for widget in (self.allow, self.decline, self.more, self.close_button):
            row.addWidget(widget)
        self.allow.clicked.connect(lambda: self.choose('weekly'))
        self.decline.clicked.connect(lambda: self.choose('never'))
        self.more.clicked.connect(lambda: self.shown and self.shown['link'] and self.open_url(self.shown['link']))
        self.close_button.clicked.connect(self.dismiss)
        self.hide()

    # ---- what the bar shows -----------------------------------------------------------------------
    def _mode(self, mode):
        asking = mode == 'ask'
        self.allow.setVisible(asking)
        self.decline.setVisible(asking)
        self.more.setVisible(mode == 'news' and bool(self.shown and self.shown['link']))
        self.close_button.setVisible(mode == 'news')
        self.setVisible(mode in ('ask', 'news'))

    def refresh(self):
        """Show the consent question, the current announcement, or nothing."""
        choice = prefs.get('news/check')
        if choice == 'ask':
            self.shown = None
            self.message.setText(ASK)
            self._mode('ask')
            return 'ask'
        self.shown = None
        cached = prefs.get('news/cache')
        if choice == 'weekly' and cached:
            try:
                self.shown = news.choose(news.parse(cached), self.now().date(), __version__,
                                         prefs.get('news/dismissed'))
            except news.NewsError:
                self.shown = None
        if self.shown:
            text = self.shown['title'] + (f'  ·  {self.shown["text"]}' if self.shown['text'] else '')
            self.message.setText(text)
            self._mode('news')
            return 'news'
        self._mode('none')
        return 'none'

    def choose(self, choice):
        prefs.set('news/check', choice)
        self.refresh()
        if choice == 'weekly':
            return self.start(force=True)
        return None

    def dismiss(self):
        if self.shown:
            prefs.set('news/dismissed', tuple(prefs.get('news/dismissed')) + (self.shown['id'],))
        return self.refresh()

    # ---- reading the news -------------------------------------------------------------------------
    def start(self, force=False):
        """Read the news in the background if allowed and a week has passed (or force); returns the run."""
        self.refresh()
        if prefs.get('news/check') != 'weekly':
            return None
        if not force and not news.due(prefs.get('news/last_checked'), self.now()):
            return None
        from quantumscope.gui.background import Run
        self.run = Run(lambda report, cancelled: news.fetch(self.opener), owner=self,
                       on_done=self._received, on_error=lambda *_: None).start()   # offline: keep the cache
        return self.run

    def _received(self, text):
        prefs.set('news/cache', text)
        prefs.set('news/last_checked', self.now().isoformat(timespec='seconds'))
        self.refresh()
