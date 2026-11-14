"""v0.8.2: the updater retries GitHub's temporary errors and never freezes the window.

Reported: updating from 0.8.0, the window stopped responding ("Wait / Force Quit"), then showed
"GitHub answered with an error (504)". A 504 is GitHub's own, temporary gateway timeout.
"""
import hashlib
import time
import urllib.error

import pytest

from quantumscope import updater
from test_v070_updater import INSTALLER, github


def failing(codes, then=None):
    """An opener that fails with these HTTP codes (or 'offline') in turn, then answers like `then`."""
    calls = []

    def opener(request, timeout=None):
        calls.append(request.full_url)
        if len(calls) <= len(codes):
            code = codes[len(calls) - 1]
            if code == 'offline':
                raise urllib.error.URLError('connection reset')
            raise urllib.error.HTTPError(request.full_url, code, 'error', {}, None)
        return then(request, timeout)
    opener.calls = calls
    return opener


@pytest.fixture
def waits(monkeypatch):
    slept = []
    monkeypatch.setattr(updater, 'SLEEP', slept.append)
    return slept


def test_temporary_errors_are_retried_then_succeed(waits):
    opener = failing([504, 502], then=github())
    found = updater.check((0, 6, 2), 'win32', opener)
    assert found.label == '0.7.0' and len(opener.calls) == 3 and waits == [1.0, 3.0]
    opener = failing(['offline'], then=github())
    assert updater.check((0, 6, 2), 'win32', opener).label == '0.7.0' and len(opener.calls) == 2


def test_lasting_trouble_is_explained_with_the_release_page(waits):
    with pytest.raises(updater.UpdateError) as error:
        updater.check((0, 6, 2), 'linux', failing([504, 504, 504]))
    message = str(error.value)
    assert 'error 504, the server timed out' in message and "temporary problem on GitHub's side" in message
    assert 'after 3 tries' in message and updater.RELEASES_PAGE in message
    with pytest.raises(updater.UpdateError, match='Could not reach GitHub after 3 tries'):
        updater.check((0, 6, 2), 'linux', failing(['offline'] * 3))


def test_errors_that_retrying_cannot_fix_are_not_retried(waits):
    opener = failing([404])
    with pytest.raises(updater.UpdateError, match=r'error \(404\).*release page'):
        updater.check((0, 6, 2), 'linux', opener)
    assert len(opener.calls) == 1 and waits == []

    def limited(request, timeout=None):
        limited.calls += 1
        raise urllib.error.HTTPError(request.full_url, 403, 'limited',
                                     {'X-RateLimit-Remaining': '0', 'X-RateLimit-Reset': str(int(time.time()) + 600)}, None)
    limited.calls = 0
    with pytest.raises(updater.UpdateError, match='limit'):
        updater.check((0, 6, 2), 'linux', limited)
    assert limited.calls == 1


def test_a_retried_download_still_verifies(tmp_path, waits):
    release = updater.check((0, 6, 2), 'linux', github())
    path = updater.download(release, str(tmp_path), opener=failing([503, 'offline'], then=github()))
    assert updater.sha256_of(path) == hashlib.sha256(INSTALLER).hexdigest()           # the genuine installer
