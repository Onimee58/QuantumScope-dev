"""v1.0.1: your own file is a choice in the Datasets tab's list, which always says what is loaded
(QUANTUMSCOPE_GUI_TESTS=1)."""
import os

import pytest

if os.environ.get('QUANTUMSCOPE_GUI_TESTS') != '1':
    pytest.skip('GUI tests are opt-in: set QUANTUMSCOPE_GUI_TESTS=1', allow_module_level=True)

QtWidgets = pytest.importorskip('PySide6.QtWidgets')
CSV = 'height,width,group\n1.5,2,A\n2.0,2.1,B\n1.7,2.5,A\n2.2,3,B\n1.9,2.8,A\n2.1,2.2,B\n'


@pytest.fixture(scope='module')
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_your_own_file_is_chosen_in_the_list(app, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QFileDialog
    from quantumscope.gui.qml_experiments import OWN_FILE, DatasetsExperiment
    path = tmp_path / 'plants.csv'
    path.write_text(CSV)
    d = DatasetsExperiment()
    builtin = d.source.currentData()
    assert d.source.itemText(0) == OWN_FILE and not d.import_button.isEnabled()
    asked = []
    monkeypatch.setattr(QFileDialog, 'getOpenFileName', lambda *a, **k: asked.append(1) or ('', ''))
    d.source.setCurrentIndex(d.source.findData('imported'))           # cancelled: back to what is loaded
    assert asked and d.source.currentData() == builtin and not d.import_button.isEnabled()
    ds = d.import_file(str(path))
    assert d.source.currentData() == 'imported' and d.source.currentText() == 'Your file: plants.csv'
    assert d.dataset is ds and d.import_button.isEnabled()
    d.source.setCurrentIndex(d.source.findData('iris'))
    assert d.dataset is not ds and not d.import_button.isEnabled() and d.source_key == 'iris'
    asked.clear()
    d.source.setCurrentIndex(d.source.findData('imported'))           # the file again, without asking
    assert not asked and d.dataset is ds and d.source_key == 'imported'
    d.close()
