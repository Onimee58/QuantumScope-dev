"""v0.8.1 (17b): long computations run in a worker thread; the window never freezes (opt-in GUI tests)."""
import os
import threading
import time

import pytest

if os.environ.get('QUANTUMSCOPE_GUI_TESTS') != '1':
    pytest.skip('GUI tests are opt-in: set QUANTUMSCOPE_GUI_TESTS=1', allow_module_level=True)

QtWidgets = pytest.importorskip('PySide6.QtWidgets')


@pytest.fixture(scope='module')
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def counting(n=40, pause=0.01):
    def work(report, cancelled):
        for k in range(n):
            if cancelled():
                return ('cancelled at', k)
            time.sleep(pause)
            report(k)
        return 'finished'
    return work


def test_the_helper_delivers_on_the_interface_thread_and_cancels(app):
    import shiboken6
    from quantumscope.gui import background as B
    main = threading.current_thread()
    threads, steps = set(), []
    run = B.Run(counting(20), on_progress=lambda v: (threads.add(threading.current_thread() is main), steps.append(v)),
                on_done=lambda v: threads.add(threading.current_thread() is main)).start()
    assert run.wait() == 'finished' and threads == {True} and len(steps) == 20
    run = B.Run(counting()).start()
    time.sleep(0.05)
    run.cancel()
    assert run.wait()[0] == 'cancelled at'
    errors = []
    B.Run(lambda report, cancelled: 1 / 0, on_error=lambda exc, details: errors.append(exc)).start().wait()
    assert isinstance(errors[0], ZeroDivisionError)
    with pytest.raises(ZeroDivisionError):
        B.Run(lambda report, cancelled: 1 / 0).start().wait()
    owner, calls = QtWidgets.QWidget(), []
    run = B.Run(counting(), on_progress=calls.append, owner=owner).start()
    time.sleep(0.05)
    app.processEvents()
    shiboken6.delete(owner)                                            # the window closes mid-run
    before = len(calls)
    assert run.wait()[0] == 'cancelled at' and len(calls) == before and run not in B.ACTIVE


def test_optimize_runs_in_the_background_and_respects_edits(app):
    from quantumscope.gui.circuit_workspace import CircuitWorkspace
    w = CircuitWorkspace()
    w.show()
    w.load_library('qaoa', {'graph': 'ring6', 'layers': 2})
    before = dict(w.model.parameters)
    w.opt_multi.setChecked(True)                                       # a run long enough to edit during,
    w.opt_starts.setValue(20)                                          # on any machine (one start is ~0.2 s)
    dialog = w.optimize_parameters()
    assert not w.opt_button.isEnabled()                                # no second run meanwhile
    turns = 0
    while dialog.run_handle.running() and turns < 5:
        app.processEvents()
        turns += 1
    w.model.set_observable('Z0')                                       # edit the circuit mid-run
    w._changed()
    assert dialog.run_handle.running()                                 # (the edit really came first)
    dialog.waited()
    assert 'circuit changed while optimizing' in dialog.summary.text()
    assert dict(w.model.parameters) == before and w.opt_button.isEnabled()   # nothing applied
    w.load_library('qaoa', {'graph': 'ring6', 'layers': 2})
    dialog = w.optimize_parameters()
    dialog.close()                                                     # closing the window stops it
    dialog.waited()
    assert dialog.run_handle.cancel_requested


def test_the_landscape_shows_only_the_latest_request(app):
    from quantumscope.gui.circuit_workspace import CircuitWorkspace
    w = CircuitWorkspace()
    w.load_library('vqe', {'problem': 'h2', 'layers': 1})
    landscape = w.show_landscape().waited()
    landscape.second.setCurrentIndex(0)                               # one parameter: a curve
    first = landscape.draw()
    landscape.second.setCurrentIndex(landscape.second.findData('θ1'))  # then quickly a 2-D map
    second = landscape.draw()
    first.wait()
    second.wait()
    assert first.cancel_requested and len(landscape.view.data) == 3   # the map, not the stale curve
    assert landscape.windowTitle() == 'Energy landscape'
