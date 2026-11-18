"""v1.0.0: the license window at start and in About (QUANTUMSCOPE_GUI_TESTS=1)."""
import os

import pytest

if os.environ.get('QUANTUMSCOPE_GUI_TESTS') != '1':
    pytest.skip('GUI tests are opt-in: set QUANTUMSCOPE_GUI_TESTS=1', allow_module_level=True)

QtWidgets = pytest.importorskip('PySide6.QtWidgets')
from quantumscope.licensing import check as L  # noqa: E402
from test_v100_licensing import PUBLIC, SECRET  # noqa: E402


@pytest.fixture(scope='module')
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


@pytest.fixture
def setup(tmp_path, monkeypatch):
    monkeypatch.setattr(L, 'PUBLIC_KEY', PUBLIC)
    monkeypatch.setenv('QUANTUMSCOPE_DATA_DIR', str(tmp_path / 'data'))
    monkeypatch.delenv('QUANTUMSCOPE_LICENSE_FILE', raising=False)
    good = tmp_path / 'QuantumScope-license-QS-AQC-S27-001.qslicense'
    good.write_text(L.make(SECRET, 'QS-AQC-S27-001', 'student', course='AQC', expires='2099-06-30'))
    ended = tmp_path / 'ended.qslicense'
    ended.write_text(L.make(SECRET, 'QS-AQC-S27-002', 'student', expires='2020-06-30'))
    return good, ended


def test_the_window_refuses_a_bad_file_and_keeps_a_good_one(app, setup, tmp_path):
    from quantumscope.gui.license_dialog import LicenseDialog, current, require_license
    good, ended = setup
    dialog = LicenseDialog()
    assert not dialog.add(str(ended)) and 'ended on 30 June 2020' in dialog.status.text()
    assert current() == (None, '')
    assert dialog.add(str(good)) and dialog.result() == dialog.DialogCode.Accepted
    assert current()[0].id == 'QS-AQC-S27-001'
    assert require_license().id == 'QS-AQC-S27-001'               # in use: no window at the next start


def test_an_ended_license_in_use_is_explained(app, setup, monkeypatch):
    from quantumscope.gui import license_dialog as D
    _, ended = setup
    L.install(str(setup[0]), D._folder())
    path = L.store_path(D._folder())
    with open(path, 'w') as f:
        f.write(ended.read_text())
    lic, reason = D.current()
    assert lic is None and 'ended on' in reason
    shown = []
    monkeypatch.setattr(D.LicenseDialog, 'exec', lambda self: shown.append(self.status.text()) or 0)
    assert D.require_license() is None and 'ended on' in shown[0]   # closed: QuantumScope quits


def test_about_shows_the_license_in_use(app, setup):
    from quantumscope.gui.main_window import AboutDialog
    L.install(str(setup[0]), os.environ['QUANTUMSCOPE_DATA_DIR'])
    about = AboutDialog()
    assert about.license_label.text().startswith('Student license QS-AQC-S27-001')
    assert about.license_button.text() == 'Change license…'
    about.close()
