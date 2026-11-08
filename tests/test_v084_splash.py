"""v0.8.4: the start-up splash waits until the window system shows it (it only appeared on Windows).

On Linux and macOS a new window appears asynchronously: the window manager shows it a moment later.
v0.8.3 handled events three times and moved on, so the slow imports began before the splash ever
painted. Reproduced under X11 with a window manager: the old code painted in 0 of 5 starts.
"""
import os
import shutil
import subprocess
import sys
import textwrap
import time

import pytest

QtWidgets = pytest.importorskip('PySide6.QtWidgets', exc_type=ImportError)   # present but unloadable: skip too


@pytest.fixture(scope='module')
def app():
    try:
        return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    except Exception as exc:                                          # noqa: BLE001
        pytest.skip(f'no Qt display: {exc}')


def test_the_splash_is_painted_before_show_splash_returns(app):
    from quantumscope.gui import splash
    shown = splash.show_splash(app)
    assert shown is not None and shown.painted
    shown.close()


def test_a_window_system_that_never_shows_it_costs_at_most_the_limit(app, monkeypatch):
    from quantumscope.gui import splash

    class Never(splash.Splash):
        def paintEvent(self, event):
            pass
    monkeypatch.setattr(splash, 'Splash', Never)
    start = time.perf_counter()
    shown = splash.show_splash(app, wait=0.2)
    assert shown is not None and time.perf_counter() - start < 0.6
    shown.close()


@pytest.mark.skipif(not (shutil.which('xvfb-run') and shutil.which('openbox')),
                    reason='needs xvfb-run and the openbox window manager')
def test_under_x11_with_a_window_manager(tmp_path):
    probe = tmp_path / 'probe.py'
    probe.write_text(textwrap.dedent('''
        import time
        from PySide6.QtWidgets import QApplication
        app = QApplication([])
        print('STARTED', app.platformName(), flush=True)
        from quantumscope.gui.splash import show_splash
        painted = 0
        for _ in range(3):
            shown = show_splash(app)
            painted += shown.painted             # the slow imports would start now
            shown.close(); app.processEvents(); time.sleep(0.1)
        print('PAINTED', painted)
    '''))
    script = tmp_path / 'run.sh'
    script.write_text(f'#!/bin/bash\nopenbox >/dev/null 2>&1 &\nsleep 1.5\n{sys.executable} {probe}\nkill %1\n')
    script.chmod(0o755)
    env = dict(os.environ, QT_QPA_PLATFORM='xcb',
               PYTHONPATH=os.path.join(os.path.dirname(__file__), '..', 'src'))
    out = subprocess.run(['xvfb-run', '-a', str(script)], env=env, capture_output=True, text=True, timeout=90)
    if 'STARTED xcb' not in out.stdout:                                  # only a missing X11 is a reason to skip
        pytest.skip('X11 could not start here: ' + out.stderr[-300:])
    lines = [line for line in out.stdout.splitlines() if line.startswith('PAINTED')]
    assert lines == ['PAINTED 3'], out.stdout + out.stderr[-500:]
