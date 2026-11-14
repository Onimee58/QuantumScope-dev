"""v0.9.6: memory and processor use, estimates and requirements (no window). The VTK bundling checks
went with VTK in v0.9.11."""
import pytest

from quantumscope import resources as R

GB, MB = R.GB, R.MB


def snap(available, total=8 * GB, cpu=10.0, process=500 * MB):
    return R.Snapshot(process, total, available, cpu, 4)


def test_memory_levels():
    assert R.memory_level(snap(4 * GB)) == 'ok'
    assert R.memory_level(snap(1.1 * GB)) == 'high'                    # under 15% of 8 GB
    assert R.memory_level(snap(0.6 * GB)) == 'critical'                # under 8%
    small = 2 * GB                                                     # small computers: the fixed amounts decide
    assert R.memory_level(snap(700 * MB, small)) == 'high' and R.memory_level(snap(300 * MB, small)) == 'critical'
    assert snap(2 * GB).used_share == pytest.approx(0.75)


def test_sizes_in_words():
    assert R.size(850 * MB) == '850 MB' and R.size(1.44 * GB) == '1.4 GB' and R.size(10) == '1 MB'


def test_estimates_follow_measurements():
    assert R.hydrogen_grid(96) == pytest.approx(70 * MB, rel=0.1)       # measured: about 88 MB at 96³
    assert R.hydrogen_grid(160, 2) == 2 * R.hydrogen_grid(160)
    assert R.hydrogen_grid(160) == pytest.approx(310 * MB, rel=0.2)     # measured: about 309 MB at 160³
    assert R.kernel_matrix(750, 250, 10) == pytest.approx(110 * MB, rel=0.25)   # measured: about 119 MB
    assert R.kernel_matrix(300, 100, 4) < 50 * MB


def test_asking_before_a_task_that_may_not_fit():
    assert R.check(1 * GB, snap(4 * GB)) == (True, '')
    fine, message = R.check(3 * GB, snap(4 * GB))
    assert not fine and 'about 3.0 GB' in message and 'about 4.0 GB is free' in message


def test_a_real_snapshot():
    s = R.snapshot()
    assert 0 < s.process < s.total and 0 < s.available <= s.total and 0 <= s.cpu <= 100 and s.cores >= 1


def test_requirements_are_complete():
    assert list(R.REQUIREMENTS) == ['Minimum', 'Recommended', 'Best']
    for level in R.REQUIREMENTS.values():
        assert set(level) == {'cpu', 'memory', 'graphics', 'disk', 'screen', 'note'}
    assert 'Windows 10' in R.SYSTEMS and 'macOS 14.4' in R.SYSTEMS and 'Ubuntu 24.04' in R.SYSTEMS
