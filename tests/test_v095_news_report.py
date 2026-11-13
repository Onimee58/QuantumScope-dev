"""v0.9.5: announcements from news.json, and problem reports (no Qt)."""
import datetime
import io
import json
import sys
import urllib.parse

import pytest

from quantumscope import __version__, news, report

TODAY = datetime.date(2027, 2, 1)


def _news(*items, email='help@quantumscope.example'):
    return json.dumps({'support_email': email, 'announcements': list(items)})


def _item(ident='a', **extra):
    return dict(dict(id=ident, title=f'Title {ident}', text='Some text.'), **extra)


# ---- news.json -----------------------------------------------------------------------------------
def test_a_good_news_file():
    n = news.parse(_news(_item('w', link='https://example.org/w', **{'from': '2027-01-01', 'until': '2027-03-01'})))
    assert n['support_email'] == 'help@quantumscope.example'
    a = n['announcements'][0]
    assert (a['id'], a['link'], a['start'], a['end']) == ('w', 'https://example.org/w', datetime.date(2027, 1, 1),
                                                          datetime.date(2027, 3, 1))


@pytest.mark.parametrize('bad', [
    _item('', ),                                                    # no id
    {'id': 'x', 'text': 'no title'},
    _item('x', link='http://example.org'),                          # links must be https
    _item('x', link='javascript:alert(1)'),
    _item('x', **{'from': 'next tuesday'}),
    _item('x', min_version='soon'),
    _item('x', title='T' * 81),
    'not an object',
])
def test_malformed_announcements_are_skipped(bad):
    assert news.parse(_news(bad, _item('ok')))['announcements'][0]['id'] == 'ok'


def test_broken_files_and_bad_addresses():
    for text in ('{not json', '[1, 2]', b'\xff\xfe'):
        with pytest.raises(news.NewsError):
            news.parse(text)
    assert news.parse(_news(email='not an address'))['support_email'] == ''
    assert news.parse('{}') == {'support_email': '', 'announcements': []}


def test_choose_by_date_version_and_dismissal():
    n = news.parse(_news(_item('past', until='2027-01-31'), _item('future', **{'from': '2027-02-02'}),
                         _item('newer', min_version='99.0'), _item('older', max_version='0.1'),
                         _item('now'), _item('later')))
    assert news.choose(n, TODAY, __version__)['id'] == 'now'           # the first current one, in file order
    assert news.choose(n, TODAY, __version__, dismissed=('now',))['id'] == 'later'
    assert news.choose(n, TODAY, __version__, dismissed=('now', 'later')) is None
    edge = news.parse(_news(_item('edge', **{'from': '2027-02-01', 'until': '2027-02-01'})))
    assert news.choose(edge, TODAY, __version__)['id'] == 'edge'        # both dates count
    assert news.choose(None, TODAY, __version__) is None


def test_weekly():
    now = datetime.datetime(2027, 2, 1, 12)
    assert news.due('', now) and news.due('garbage', now)
    assert not news.due((now - datetime.timedelta(days=6)).isoformat(), now)
    assert news.due((now - datetime.timedelta(days=7)).isoformat(), now)
    assert news.due((now + datetime.timedelta(days=1)).isoformat(), now)   # a clock set back: check again


class _Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_fetch_reads_the_public_file_and_refuses_others():
    seen = []

    def opener(request, timeout):
        seen.append((request.full_url, timeout, request.get_header('User-agent')))
        return _Response(_news(_item('a')).encode())
    assert json.loads(news.fetch(opener))['announcements'][0]['id'] == 'a'
    assert seen == [(news.NEWS_URL, news.TIMEOUT, 'QuantumScope-news')]
    assert news.NEWS_URL == 'https://raw.githubusercontent.com/Onimee58/QuantumScope/main/news.json'
    with pytest.raises(news.NewsError):
        news.fetch(lambda request, timeout: _Response(b'<html>not found</html>'))
    with pytest.raises(news.NewsError):
        news.fetch(lambda request, timeout: _Response(b' ' * (65 * 1024)))

    def offline(request, timeout):
        raise OSError('no network')
    with pytest.raises(news.NewsError):
        news.fetch(offline)


def test_the_starter_news_file_is_valid():
    text = open('docs/releases-repository/news.json', encoding='utf-8').read()
    n = news.parse(text)
    assert n == {'support_email': '', 'announcements': []}


# ---- reports ---------------------------------------------------------------------------------------
def test_diagnostics_are_useful_and_not_personal():
    info = report.diagnostics('Quantum ML', 'Kernel Classifier')
    assert info['QuantumScope'] == __version__ and info['Area'] == 'Quantum ML' and info['Open tab'] == 'Kernel Classifier'
    assert set(info) >= {'System', 'Python', 'PySide6', 'NumPy', 'Installed'}
    import getpass
    import os
    text = ' '.join(map(str, info.values()))
    assert getpass.getuser() not in text.split() and os.path.expanduser('~') not in text   # no user name or paths


def test_compose_with_an_error():
    try:
        1 / 0
    except ZeroDivisionError:
        error = report.remember_error(*sys.exc_info())
    text = report.compose('The plot froze\nafter training', 'It should draw', {'QuantumScope': '0.9.5'}, error)
    assert text.startswith('What happened:\nThe plot froze\nafter training\n\nWhat I expected:\nIt should draw')
    assert '- QuantumScope: 0.9.5' in text and 'Error: ZeroDivisionError: division by zero' in text
    assert 'Traceback' in text and report.LAST_ERROR is error
    assert report.title_for('The plot froze\nmore') == 'The plot froze'
    assert report.title_for('', error) == 'ZeroDivisionError: division by zero'
    assert len(report.title_for('x' * 200)) == 70


def test_links_fill_in_the_report_and_stay_short_enough():
    body = report.compose('Crash & burn: 100% wrong?', info={'QuantumScope': '0.9.5'})
    link, cut = report.mail_link('help@quantumscope.example', 'Crash', body)
    assert link.startswith('mailto:help@quantumscope.example?subject=') and not cut
    query = urllib.parse.parse_qs(link.split('?', 1)[1])
    assert query['body'] == [body] and query['subject'] == [f'QuantumScope {__version__}: Crash']
    link, cut = report.issue_link('Crash', body)
    assert link.startswith('https://github.com/Onimee58/QuantumScope/issues/new?title=Crash&body=') and not cut
    assert urllib.parse.parse_qs(link.split('?', 1)[1])['body'] == [body]
    long = body + 'trace line\n' * 2000
    link, cut = report.mail_link('help@quantumscope.example', 'Crash', long)
    assert cut and len(link) <= report.MAX_MAIL and 'full report is on your clipboard' in urllib.parse.unquote(link)
    link, cut = report.issue_link('Crash', long)
    assert cut and len(link) <= report.MAX_ISSUE
