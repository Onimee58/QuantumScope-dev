"""Long computations in a worker thread, so the window never freezes (v0.8.1).

    run = Run(work, on_progress=…, on_done=…, on_error=…, owner=widget).start()

work(report, cancelled) runs in a worker thread. It must not touch widgets: it computes on its own
data and calls report(anything) to send progress, and checks cancelled() between steps. Progress,
the result and errors are delivered on the interface thread, where the callbacks may update widgets.

Signals are always delivered to slots of this object, which lives on the interface thread, so Qt
queues them across threads (a plain Python function could otherwise run on the worker thread).
run.wait() processes events until the run has finished and its callbacks have run (for tests and
scripts); it returns the result.

A run is not a child of its owner: Qt would delete it together with the owner, while the worker
thread may still be emitting. Instead, ACTIVE keeps runs alive until they finish, closing the
owner sets the cancel flag, and callbacks are skipped once the owner is gone.
"""
import threading
import time
import traceback

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import QApplication


ACTIVE = set()                                                    # runs in progress, kept alive


class Run(QObject):
    _progress = Signal(object)
    _done = Signal(object)
    _failed = Signal(object)

    def __init__(self, work, on_progress=None, on_done=None, on_error=None, owner=None):
        super().__init__()
        self.work, self.on_progress, self.on_done, self.on_error = work, on_progress, on_done, on_error
        self.cancel_requested = False
        self.finished = False
        self.owner_alive = True
        self.result = self.error = None
        self._progress.connect(self._deliver_progress)
        self._done.connect(self._deliver_done)
        self._failed.connect(self._deliver_error)
        if owner is not None:                                     # the window closed: stop the work
            owner.destroyed.connect(self._owner_gone)
        self._thread = threading.Thread(target=self._main, name='quantumscope-work', daemon=True)

    def start(self):
        ACTIVE.add(self)
        self._thread.start()
        return self

    def _owner_gone(self, *_):
        self.owner_alive = False
        self.cancel_requested = True

    def cancel(self, *_):
        self.cancel_requested = True

    def cancelled(self):
        return self.cancel_requested

    def running(self):
        return not self.finished

    def _main(self):                                              # the worker thread
        try:
            result = self.work(self._progress.emit, self.cancelled)
        except Exception as exc:                                  # noqa: BLE001 - reported on the interface thread
            self._failed.emit((exc, traceback.format_exc()))
        else:
            self._done.emit(result)

    @Slot(object)
    def _deliver_progress(self, value):
        if self.on_progress is not None and not self.finished and self.owner_alive:
            self.on_progress(value)

    @Slot(object)
    def _deliver_done(self, result):
        self.result = result
        try:
            if self.on_done is not None and self.owner_alive:
                self.on_done(result)
        finally:
            self.finished = True
            ACTIVE.discard(self)

    @Slot(object)
    def _deliver_error(self, error):
        self.error = error
        try:
            if self.on_error is not None and self.owner_alive:
                self.on_error(*error)
        finally:
            self.finished = True
            ACTIVE.discard(self)

    def wait(self, timeout=600.0):
        """Process events until the run has finished (callbacks included); return its result."""
        app = QApplication.instance()
        end = time.monotonic() + timeout
        while not self.finished:
            if time.monotonic() > end:
                raise TimeoutError('The background computation did not finish in time')
            if app is not None:
                app.processEvents()
            time.sleep(0.002)
        if self.error is not None and self.on_error is None:
            raise self.error[0]
        return self.result
