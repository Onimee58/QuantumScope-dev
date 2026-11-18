"""v0.9.17: from the beta tester's second review (no window): run times, window sizes that fit the
screen, and visible arrows on number boxes."""
from importlib.resources import files
from types import SimpleNamespace

import pytest

pytest.importorskip('PySide6')
from quantumscope.gui.background import duration  # noqa: E402
from quantumscope.gui.main_window import fitted_size  # noqa: E402
from quantumscope.gui.theme import arrow_rules  # noqa: E402


def test_durations_read_naturally():
    assert duration(3.4) == '3 s'
    assert duration(125) == '2 min 05 s'
    assert duration(3725) == '1 h 02 min'


def screen(width, height):
    free = SimpleNamespace(width=lambda: width, height=lambda: height)
    return SimpleNamespace(availableGeometry=lambda: free)


def test_the_window_opens_within_the_screen():
    assert fitted_size(1420, 920, screen(1366, 728)) == (1350, 680)   # a 768-pixel laptop, with its taskbar
    assert fitted_size(1420, 920, screen(2560, 1400)) == (1420, 920)   # room enough: as before


@pytest.mark.parametrize('theme', ['dark', 'light'])
def test_number_boxes_and_groups_draw_their_arrows(theme):
    rules = arrow_rules(theme)
    for name in ('arrow-up', 'arrow-down', 'arrow-right'):
        asset = files('quantumscope').joinpath(f'assets/{name}-{theme}.svg')
        assert asset.is_file() and str(asset).replace('\\', '/') in rules
    for part in ('QSpinBox::up-button', 'QDoubleSpinBox::down-arrow', 'QComboBox::down-arrow',
                 'QGroupBox[fold="true"]::indicator:unchecked'):
        assert part in rules
