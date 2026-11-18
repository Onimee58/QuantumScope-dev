"""v0.9.18: the double-slit drawing stretches to fill its place, but its words and dots keep their
shape (QUANTUMSCOPE_GUI_TESTS=1)."""
import os

import pytest

if os.environ.get('QUANTUMSCOPE_GUI_TESTS') != '1':
    pytest.skip('GUI tests are opt-in: set QUANTUMSCOPE_GUI_TESTS=1', allow_module_level=True)

QtWidgets = pytest.importorskip('PySide6.QtWidgets')


@pytest.fixture(scope='module')
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def ink(width, height, scene_box):
    """The box (width, height) of the light pixels in a part of the drawing given in scene units."""
    from quantumscope.gui.double_slit_apparatus import DoubleSlitApparatus
    view = DoubleSlitApparatus()
    view.resize(width, height)
    image = view.grab().toImage()
    x0, y0, x1, y1 = (round(v * s) for v, s in zip(scene_box, (width / 700, height / 300) * 2))
    xs, ys = [], []
    for y in range(y0, y1):
        for x in range(x0, x1):
            if image.pixelColor(x, y).lightness() > 150:
                xs.append(x)
                ys.append(y)
    view.close()
    return max(xs) - min(xs), max(ys) - min(ys)


def test_words_keep_their_shape_when_the_drawing_is_stretched(app):
    normal = ink(700, 300, (27, 6, 132, 30))                  # 'Source'
    wide = ink(1400, 300, (27, 6, 132, 30))                   # twice as wide, as tall
    assert abs(wide[0] - normal[0]) <= 2 and abs(wide[1] - normal[1]) <= 2


def test_the_source_stays_round(app):
    w, h = ink(1400, 300, (50, 130, 90, 175))
    assert abs(w - h) <= 2
