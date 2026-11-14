"""Problem reports (v0.9.5, no Qt): what goes into one, and the links that send it.

QuantumScope never sends a report itself. Report a problem builds the text, shows all of it, and
opens the user's own email program or browser with it filled in; the user presses Send there.
"""
import platform
import sys
import traceback
import urllib.parse

from quantumscope import __version__
from quantumscope.updater import REPOSITORY

ISSUES_URL = f'https://github.com/{REPOSITORY}/issues/new'
MAX_MAIL = 1800             # mailto: links longer than this fail in some email programs (Windows)
MAX_ISSUE = 6000            # GitHub refuses very long new-issue links
LAST_ERROR = {}             # the most recent unexpected error, kept for the next report


def diagnostics(area='', experiment='', extra=None):
    """What helps find a problem, and nothing personal: versions, system, where the user was."""
    try:
        from PySide6 import __version__ as pyside
    except ImportError:
        pyside = 'not loaded'
    import numpy
    info = {
        'QuantumScope': __version__,
        'Installed': 'installer' if getattr(sys, 'frozen', False) else 'from source',
        'System': f'{platform.system()} {platform.release()} ({platform.machine()})',
        'Python': platform.python_version(),
        'PySide6': pyside,
        'NumPy': numpy.__version__,
    }
    if area:
        info['Area'] = area
    if experiment:
        info['Open tab'] = experiment
    info.update(extra or {})
    return info


def remember_error(kind, value, tb):
    """Keep an unexpected error's summary and traceback for the report (a crash catcher calls this)."""
    LAST_ERROR.clear()
    LAST_ERROR.update(summary=f'{kind.__name__}: {value}',
                      traceback=''.join(traceback.format_exception(kind, value, tb)))
    return LAST_ERROR


def compose(what, expected='', info=None, error=None):
    """The report as plain text, in the order a maintainer reads it."""
    parts = ['What happened:', what.strip() or '(not described)', '']
    if expected.strip():
        parts += ['What I expected:', expected.strip(), '']
    parts.append('About this computer:')
    parts += [f'- {k}: {v}' for k, v in (info or {}).items()]
    if error:
        parts += ['', f'Error: {error.get("summary", "")}', '', error.get('traceback', '').rstrip()]
    return '\n'.join(parts).rstrip() + '\n'


def title_for(what, error=None):
    first = (what.strip().splitlines() or [''])[0]
    title = first if first else (error or {}).get('summary', '') or 'Problem report'
    return title if len(title) <= 70 else title[:69] + '…'


def _shorten(body, limit, quote):
    """Cut the body so the encoded link stays under `limit` characters, saying so."""
    note = '\n\n[Shortened: the full report is on your clipboard; paste it here.]'
    if len(quote(body)) <= limit:
        return body, False
    low, high = 0, len(body)
    while low < high:                                         # the longest prefix that fits
        middle = (low + high + 1) // 2
        if len(quote(body[:middle] + note)) <= limit:
            low = middle
        else:
            high = middle - 1
    return body[:low].rstrip() + note, True


def mail_link(address, title, body):
    """(mailto: link, shortened?) with the subject and body filled in."""
    def quote(text):
        return urllib.parse.quote(text, safe='')
    subject = f'QuantumScope {__version__}: {title}'
    room = MAX_MAIL - len(f'mailto:{address}?subject={quote(subject)}&body=')
    body, cut = _shorten(body, max(200, room), quote)
    return f'mailto:{address}?subject={quote(subject)}&body={quote(body)}', cut


def issue_link(title, body):
    """(GitHub new-issue link, shortened?) with the title and body filled in."""
    def quote(text):
        return urllib.parse.quote(text, safe='')
    room = MAX_ISSUE - len(f'{ISSUES_URL}?title={quote(title)}&body=')
    body, cut = _shorten(body, max(500, room), quote)
    return f'{ISSUES_URL}?title={quote(title)}&body={quote(body)}', cut
