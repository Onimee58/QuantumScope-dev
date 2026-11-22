"""v1.1.1: a crash in compiled code leaves a trace for the next start to offer in a report."""
import pytest

pytest.importorskip('PySide6')


def test_the_last_sessions_trace_is_kept_and_a_new_log_started(tmp_path, monkeypatch):
    monkeypatch.setenv('QUANTUMSCOPE_DATA_DIR', str(tmp_path))
    from quantumscope.gui import report_dialog as R
    (tmp_path / 'last-crash.log').write_text('Fatal Python error: Segmentation fault\n')
    R.enable_crash_log()
    try:
        assert R.CRASH['previous'] == 'Fatal Python error: Segmentation fault'
        assert (tmp_path / 'last-crash.log').read_text() == ''          # this session starts clean
    finally:
        import faulthandler
        import sys
        faulthandler.enable(sys.__stderr__)                              # back to where pytest had it
        R.CRASH['handle'].close()
