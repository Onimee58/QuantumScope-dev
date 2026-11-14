"""The golden replay: 19 circuit-editor steps must behave exactly as recorded in tests/golden/baseline.json.

Opt-in like the other GUI tests (QUANTUMSCOPE_GUI_TESTS=1). After a deliberate change in behaviour,
review the reported differences, then re-record with: python tests/golden/replay.py --record
"""
import json
import os
import subprocess
import sys

import pytest

if os.environ.get('QUANTUMSCOPE_GUI_TESTS') != '1':
    pytest.skip('GUI tests are opt-in: set QUANTUMSCOPE_GUI_TESTS=1', allow_module_level=True)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def test_the_editor_replays_exactly_as_recorded(tmp_path):
    out = tmp_path / 'replay.json'
    env = dict(os.environ, QT_QPA_PLATFORM='offscreen', QUANTUMSCOPE_SETTINGS_FILE=str(tmp_path / 's.ini'),
               QUANTUMSCOPE_DATA_DIR=str(tmp_path / 'data'),
               PYTHONPATH=os.path.join(ROOT, 'src') + os.pathsep + os.environ.get('PYTHONPATH', ''))
    run = subprocess.run([sys.executable, os.path.join(HERE, 'golden', 'replay.py'), str(out)], env=env,
                         capture_output=True, text=True, timeout=240)
    assert out.exists(), run.stdout[-2000:] + run.stderr[-2000:]
    expected = json.load(open(os.path.join(HERE, 'golden', 'baseline.json'), encoding='utf-8'))
    actual = json.load(open(out, encoding='utf-8'))
    assert [s['step'] for s in actual] == [s['step'] for s in expected]
    differences = [f"step '{e['step']}', {key}: expected {e[key]!r}, got {a[key]!r}"
                   for e, a in zip(expected, actual) for key in e if e[key] != a.get(key)]
    assert not differences, 'The editor behaves differently:\n' + '\n'.join(d[:300] for d in differences)
