"""Announcements and the support address, read from the public releases repository (v0.9.5, no Qt).

The maintainers edit one file, news.json, in github.com/Onimee58/QuantumScope; no new release is
needed. QuantumScope reads it at most once a week, and only if the user allowed it (Settings →
Updates and news). Nothing about the user is sent: it is a plain download of a public file.

news.json:
    {
      "support_email": "help@example.org",            # where Report a problem sends email ('' = none yet)
      "announcements": [
        {"id": "spring-workshop",                      # unique; a dismissed id never comes back
         "title": "Quantum computing for professionals",
         "text": "A two-day workshop, March 3–4.",
         "link": "https://example.org/workshop",      # optional, https only
         "from": "2027-01-10", "until": "2027-03-04",  # optional dates (inclusive)
         "min_version": "0.9.5", "max_version": ""}    # optional: only for these versions
      ]
    }
Anything malformed is skipped, never shown half-right: a broken file means no announcement.
"""
import datetime
import json
import re
import urllib.request

from quantumscope.updater import REPOSITORY, parse_version

NEWS_URL = f'https://raw.githubusercontent.com/{REPOSITORY}/main/news.json'
TIMEOUT = 10
INTERVAL = datetime.timedelta(days=7)
MAX_TITLE, MAX_TEXT = 80, 400
EMAIL = re.compile(r'^[^@\s<>"]+@[^@\s<>"]+\.[A-Za-z]{2,}$')


class NewsError(Exception):
    """The news could not be read (no connection, or not a news file)."""


def _date(text):
    if not text:
        return None
    try:
        return datetime.date.fromisoformat(str(text))
    except ValueError:
        raise ValueError(f'not a date: {text!r}') from None


def _announcement(item):
    """One announcement, checked, or None if it is malformed."""
    if not isinstance(item, dict):
        return None
    try:
        ident, title, text = str(item['id']).strip(), str(item['title']).strip(), str(item.get('text', '')).strip()
        link = str(item.get('link') or '').strip()
        if not ident or not title or len(title) > MAX_TITLE or len(text) > MAX_TEXT:
            return None
        if link and not link.startswith('https://'):
            return None
        start, end = _date(item.get('from')), _date(item.get('until'))
        low = parse_version(item['min_version']) if item.get('min_version') else None
        high = parse_version(item['max_version']) if item.get('max_version') else None
        if (item.get('min_version') and low is None) or (item.get('max_version') and high is None):
            return None
    except (KeyError, ValueError, TypeError):
        return None
    return dict(id=ident, title=title, text=text, link=link, start=start, end=end, low=low, high=high)


def parse(data):
    """news.json (bytes or text) → {'support_email': str, 'announcements': [checked announcements]}."""
    try:
        raw = json.loads(data.decode('utf-8') if isinstance(data, bytes) else data)
    except (ValueError, UnicodeDecodeError) as exc:
        raise NewsError('The news file could not be read') from exc
    if not isinstance(raw, dict):
        raise NewsError('The news file has an unexpected shape')
    email = str(raw.get('support_email') or '').strip()
    items = raw.get('announcements') or []
    return dict(support_email=email if EMAIL.match(email) else '',
                announcements=[a for a in map(_announcement, items if isinstance(items, list) else []) if a])


def choose(news, today, version, dismissed=()):
    """The one announcement to show now: the first in the file that is current, meant for this
    version, and not dismissed. None if there is none."""
    current = parse_version(version)
    for a in (news or {}).get('announcements', []):
        if a['id'] in dismissed:
            continue
        if (a['start'] and today < a['start']) or (a['end'] and today > a['end']):
            continue
        if (a['low'] and current < a['low']) or (a['high'] and current > a['high']):
            continue
        return a
    return None


def due(last_checked, now):
    """Whether a week has passed since the last check (an unknown or future time counts as due)."""
    try:
        last = datetime.datetime.fromisoformat(str(last_checked))
    except ValueError:
        return True
    return not (last <= now < last + INTERVAL)


def fetch(opener=None):
    """Download news.json (raw text): one request, no retries. Raises NewsError."""
    request = urllib.request.Request(NEWS_URL, headers={'User-Agent': 'QuantumScope-news'})
    try:
        with (opener or urllib.request.urlopen)(request, timeout=TIMEOUT) as response:
            data = response.read(64 * 1024 + 1)
    except OSError as exc:                                    # includes URLError, HTTPError and timeouts
        raise NewsError('Could not reach github.com') from exc
    if len(data) > 64 * 1024:
        raise NewsError('The news file is too large')
    parse(data)                                               # refuse anything that is not a news file
    return data.decode('utf-8')
