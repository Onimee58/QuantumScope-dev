"""v0.9.9: the experiments and the calculator tell the labs what the student did (QUANTUMSCOPE_GUI_TESTS=1)."""
import os
import time

import pytest

if os.environ.get('QUANTUMSCOPE_GUI_TESTS') != '1':
    pytest.skip('GUI tests are opt-in: set QUANTUMSCOPE_GUI_TESTS=1', allow_module_level=True)

QtWidgets = pytest.importorskip('PySide6.QtWidgets')

from quantumscope.learn import progress  # noqa: E402


@pytest.fixture
def app():
    progress.reset()
    yield QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    progress.reset()


def test_superposition_records_measured_copies(app):
    from quantumscope.gui.quantum_principles import SuperpositionDialog
    d = SuperpositionDialog()
    d.theta.setValue(60)
    d.phi.setValue(0)
    d.axis.setValue(0)
    d.speed.setCurrentIndex(2)                                  # Instant
    d.hits.setValue(2000)
    d._sample()
    assert progress.did('superposition theta=60 phi=0 axis=0 copies=2000 up=0.75±0.05 expected=0.75')[0], progress.EVENTS


def test_double_slit_records_fired_particles(app):
    from quantumscope.gui.double_slit_dialog import DoubleSlitDialog
    d = DoubleSlitDialog()
    d.separation.setValue(200)
    d.which_path.setChecked(True)
    d.speed.setCurrentIndex(2)
    d.batch.setValue(1500)
    d._fire()
    assert progress.did('slit separation=200 width=20 wavelength=500 whichpath=1 particles=1500')[0], progress.EVENTS


def test_entanglement_records_pairs_and_the_bell_test(app):
    from quantumscope.gui.entanglement_experiment import EntanglementDialog
    d = EntanglementDialog()
    d.state.setCurrentIndex(d.state.findData('psi-'))
    d.speed.setCurrentIndex(2)
    d.alice_axis[1].setValue(0)
    d.bob_axis[1].setValue(0)
    d.send_many()
    assert progress.did('pairs state=psi- alice=0 bob=0 E=-1 clean=1')[0], progress.EVENTS
    d.run_bell_test()
    assert progress.did('bell state=psi- clean=1 S>=2.5')[0], progress.EVENTS


def test_dynamics_records_the_played_pair(app):
    from quantumscope.gui.dynamics_dialog import HydrogenDynamicsDialog
    d = HydrogenDynamicsDialog()
    d.a.setCurrentIndex(0)                                      # 1s
    d.b.setCurrentIndex(next(i for i in range(d.b.count()) if tuple(d.b.itemData(i)) == (3, 2, 0)))   # 3d
    d.prob.setValue(90)
    d._rebuild_now()
    d._toggle()
    d.timer.stop()
    assert progress.did('beat pair=1s+3d p=0.9 view=2d period=0.3421±0.0005')[0], progress.EVENTS


def test_calculator_records_results(app):
    from quantumscope.gui.calculator import CalculatorView
    v = CalculatorView()
    v.input.setText('H Z H')
    run = v.evaluate()
    end = time.time() + 20
    while run.running() and time.time() < end:
        app.processEvents()
        time.sleep(0.01)
    app.processEvents()
    assert progress.calc('gives X')[0] and progress.calc('typed H*Z*H')[0], progress.EVENTS
