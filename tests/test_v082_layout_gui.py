"""v0.8.2: the Quantum ML control columns scroll instead of squashing, and never hide content sideways.

Adding the Model box made the columns taller than short windows; Qt then squashed every control.
The columns now scroll. Their width must also fit every state: a dataset with more than two classes
adds a Classes row, which once pushed the column wider than its view (hidden under the scrollbar).
"""
import os

import pytest

if os.environ.get('QUANTUMSCOPE_GUI_TESTS') != '1':
    pytest.skip('GUI tests are opt-in: set QUANTUMSCOPE_GUI_TESTS=1', allow_module_level=True)

QtWidgets = pytest.importorskip('PySide6.QtWidgets')


@pytest.fixture(scope='module')
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


@pytest.mark.parametrize('experiment', ['KernelExperiment', 'VariationalExperiment', 'DatasetsExperiment'])
def test_columns_never_squash_or_hide_content(app, experiment):
    from PySide6.QtWidgets import QComboBox, QDoubleSpinBox, QPushButton, QScrollArea, QSpinBox
    from quantumscope.gui import qml_experiments as Q
    for dataset in ('circles', 'mnist', 'iris', 'breast_cancer'):
        for height in (950, 640, 520):
            w = getattr(Q, experiment)()
            w.resize(1200, height)
            w.show()
            box = w.source if experiment == 'DatasetsExperiment' else w.data.source
            box.setCurrentIndex(box.findData(dataset))
            app.processEvents()
            app.processEvents()
            area = w.findChildren(QScrollArea)[0]
            controls = [c for kind in (QSpinBox, QDoubleSpinBox, QComboBox, QPushButton) for c in w.findChildren(kind)]
            squashed = [c for c in controls if c.height() < c.sizeHint().height() - 1]
            assert not squashed, (dataset, height, [type(c).__name__ for c in squashed])
            assert area.horizontalScrollBar().maximum() == 0, (dataset, height)          # nothing hidden sideways
            assert area.widget().width() <= area.viewport().width(), (dataset, height)
            assert area.verticalScrollBar().isVisible() == (area.widget().height() > area.viewport().height())
            w.close()
