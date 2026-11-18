"""v0.9.19: Import data… shows a .csv first, to choose its label column and the columns to use
(QUANTUMSCOPE_GUI_TESTS=1)."""
import os

import pytest

if os.environ.get('QUANTUMSCOPE_GUI_TESTS') != '1':
    pytest.skip('GUI tests are opt-in: set QUANTUMSCOPE_GUI_TESTS=1', allow_module_level=True)

QtWidgets = pytest.importorskip('PySide6.QtWidgets')
from test_v0919_import import CSV  # noqa: E402


@pytest.fixture(scope='module')
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


@pytest.fixture
def path(tmp_path):
    p = tmp_path / 'plants.csv'
    p.write_text(CSV)
    return str(p)


def test_the_preview_guesses_and_leaves_out_ids(app, path):
    from quantumscope.gui.import_dialog import ImportDialog
    d = ImportDialog(path)
    assert d.preview.rowCount() == 5 and d.preview.columnCount() == 5
    assert d.label() == 4 and d.dataset is None and not d.import_button.isEnabled()  # width has a '?'
    assert 'empty cells' in d.warning.text()
    d.choose_label(3)                                                # a click on the column's name
    assert d.dataset.classes == ['A', 'B'] and d.import_button.isEnabled()
    assert d.leave_out() == [0] and d.dataset.features == ['height', 'colour', 'width']
    assert d.preview.horizontalHeaderItem(3).text() == '★ group'
    d.set_used(2, False)
    assert d.dataset.features == ['height', 'width'] and 'left out: id, colour' in d.summary.text()
    d.choose_label(1)
    assert d.dataset is not None and len(d.dataset.classes) == 5          # any column can be chosen
    d.header_box.setChecked(False)                                   # the names become a data row
    assert d.preview.rowCount() == 6 and d.table.names[0] == 'column 1'
    d.close()


def test_import_asks_when_the_file_is_chosen_there(app, path, monkeypatch):
    from quantumscope.gui import import_dialog
    from quantumscope.gui.qml_experiments import DatasetsExperiment

    def chosen(dialog):
        dialog.choose_label(3)
        return True
    monkeypatch.setattr(import_dialog.ImportDialog, 'exec', chosen)
    view = DatasetsExperiment()
    ds = view.import_file(path, ask=True)
    assert ds.label_name == 'group' and view.dataset is ds
    monkeypatch.setattr(import_dialog.ImportDialog, 'exec', lambda dialog: False)
    assert view.import_file(path, ask=True) is None and view.dataset is ds   # cancelled: nothing changes
    view.close()
