"""v0.9.6: the resource meter, memory warnings, and check boxes in both themes (QUANTUMSCOPE_GUI_TESTS=1)."""
import os

import pytest

if os.environ.get('QUANTUMSCOPE_GUI_TESTS') != '1':
    pytest.skip('GUI tests are opt-in: set QUANTUMSCOPE_GUI_TESTS=1', allow_module_level=True)

QtWidgets = pytest.importorskip('PySide6.QtWidgets')

from quantumscope import resources as R  # noqa: E402

GB, MB = R.GB, R.MB


@pytest.fixture
def app():
    from quantumscope.gui import preferences as prefs
    prefs._settings().remove('performance/monitor')
    yield QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    prefs._settings().remove('performance/monitor')


def test_the_meter_warns_once_per_episode(app):
    from quantumscope.gui import preferences as prefs
    from quantumscope.gui.resource_monitor import ResourceMonitor
    readings = []
    warnings = []
    window = QtWidgets.QMainWindow()
    monitor = ResourceMonitor(window, interval_ms=3000, sample=lambda: readings[-1], warn=warnings.append)
    monitor.timer.stop()                                         # driven by hand
    readings.append(R.Snapshot(600 * MB, 8 * GB, 4 * GB, 20.0, 4))
    monitor.tick()
    assert monitor.level == 'ok' and monitor.label.text().startswith('QuantumScope 600 MB · memory 50% used')
    assert 'Free memory: 4.0 GB of 8.0 GB' in monitor.label.toolTip() and not warnings
    readings.append(R.Snapshot(600 * MB, 8 * GB, 1 * GB, 20.0, 4))
    monitor.tick()
    assert monitor.level == 'high' and monitor.label.text().startswith('⚠') and 'e0a33a' in monitor.label.styleSheet()
    assert not warnings
    readings.append(R.Snapshot(2 * GB, 8 * GB, 300 * MB, 20.0, 4))
    for _ in range(3):
        monitor.tick()
    assert monitor.level == 'critical' and len(warnings) == 1 and 'Save your work now' in monitor.label.toolTip()
    readings.append(R.Snapshot(600 * MB, 8 * GB, 4 * GB, 20.0, 4))
    monitor.tick()
    readings.append(R.Snapshot(2 * GB, 8 * GB, 300 * MB, 20.0, 4))
    monitor.tick()
    assert len(warnings) == 2                                     # recovered, then nearly full again
    readings.append(R.Snapshot(600 * MB, 8 * GB, 4 * GB, 99.0, 4))
    for _ in range(9):
        monitor.tick()
    assert not monitor.label.text().startswith('⚠')               # 27 s of a busy processor: not yet
    monitor.tick()
    assert monitor.label.text().startswith('⚠') and 'fully busy for 30 s' in monitor.label.toolTip()
    prefs.set('performance/monitor', False)
    monitor.apply_preferences()
    assert monitor.tick() is None and not monitor.label.isVisibleTo(window)


def test_asking_before_a_big_task(app, monkeypatch):
    from quantumscope.gui import preferences as prefs
    from quantumscope.gui.resource_monitor import confirm_memory
    asked = []
    monkeypatch.setattr(QtWidgets.QMessageBox, 'question',
                        lambda *a, **k: asked.append(a[2]) or QtWidgets.QMessageBox.StandardButton.No)
    plenty = lambda: R.Snapshot(500 * MB, 8 * GB, 6 * GB, 5.0, 4)     # noqa: E731
    little = lambda: R.Snapshot(500 * MB, 8 * GB, 1 * GB, 5.0, 4)     # noqa: E731
    assert confirm_memory(None, 500 * MB, 'A grid', plenty) and not asked
    assert not confirm_memory(None, 2 * GB, 'A 160³ grid in both viewers', little)
    assert asked and asked[0].startswith('A 160³ grid in both viewers: This needs about 2.0 GB')
    prefs.set('performance/monitor', False)
    assert confirm_memory(None, 2 * GB, 'A grid', little) and len(asked) == 1    # warnings off: never asks


def test_settings_holds_the_switch(app):
    from quantumscope.gui import preferences as prefs
    from quantumscope.gui.settings_dialog import SECTIONS, SettingsDialog
    calls = []

    class Host:
        def apply_preferences(self):
            calls.append(prefs.get('performance/monitor'))
    d = SettingsDialog(Host())
    assert 'Graphics and performance' in SECTIONS and d.monitor.isChecked()
    d.monitor.setChecked(False)
    assert calls == [False] and prefs.get('performance/monitor') is False


@pytest.mark.parametrize('theme', ['dark', 'light'])
def test_check_boxes_show_in_both_themes(app, theme):
    """The box must stand out from its panel when unticked, and the tick from the box when ticked."""
    from PySide6.QtGui import QColor
    from quantumscope.gui import theme as T
    from quantumscope.gui.theme import contrast_ratio
    sheet = (T.LIGHT_STYLESHEET if theme == 'light' else T.STYLESHEET) + T.indicator_rules(theme)
    # the theme's own style sheet, on this window only: restyling every widget in the app is slow
    host = QtWidgets.QFrame()
    host.setPalette(T.theme_palette(theme))
    host.setStyleSheet(sheet)
    layout = QtWidgets.QVBoxLayout(host)
    box = QtWidgets.QCheckBox('Which-path detectors at the slits')
    layout.addWidget(box)
    host.resize(320, 60)
    host.show()
    app.processEvents()

    def indicator():
        image = box.grab().toImage()
        colours = [QColor(image.pixel(x, y)).name() for x in range(0, 16) for y in range(image.height())]
        return colours
    background = QColor(host.grab().toImage().pixel(300, 5)).name()
    unticked = indicator()
    edge = max(unticked, key=lambda c: contrast_ratio(c, background))
    assert contrast_ratio(edge, background) >= 2.0, (theme, edge, background)
    box.setChecked(True)
    app.processEvents()
    ticked = indicator()
    fill = max(ticked, key=lambda c: contrast_ratio(c, background))
    assert contrast_ratio('#ffffff', fill) >= 3.0 or contrast_ratio(fill, background) >= 3.0, (theme, fill)
    assert any(c in ('#ffffff', '#fefefe', '#fdfdfd') for c in ticked) or theme == 'light'   # the white tick


def test_v0910_short_memory_empties_the_caches(app):
    import numpy as np
    from quantumscope import caching
    from quantumscope.gui.resource_monitor import ResourceMonitor
    cache = caching.Cache('test', 10 ** 7)
    cache.get('grid', lambda: np.zeros(1000))
    readings = [R.Snapshot(600 * MB, 8 * GB, 4 * GB, 20.0, 4)]
    window = QtWidgets.QMainWindow()
    monitor = ResourceMonitor(window, sample=lambda: readings[-1], warn=lambda snap: None)
    monitor.timer.stop()
    monitor.tick()
    assert cache.items                                                 # plenty of memory: kept
    readings.append(R.Snapshot(600 * MB, 8 * GB, 1 * GB, 20.0, 4))
    monitor.tick()
    assert not cache.items                                             # getting full: remembered results go first
