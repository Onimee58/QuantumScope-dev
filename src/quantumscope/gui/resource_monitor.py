"""Watching memory and the processor while QuantumScope runs (v0.9.6).

A small meter in the status bar shows QuantumScope's memory and how busy the processor is, every few
seconds. It turns amber when the computer's memory is getting full, and red when it is nearly full;
then QuantumScope also says so once, with what to do, until memory recovers. A processor fully busy
for half a minute is noted in the status bar only: long computations are expected to use it.
Settings → Graphics and performance turns the warnings off.
"""
from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import QLabel, QMessageBox

from quantumscope import resources as R

COLOURS = {'ok': '', 'high': 'color: #e0a33a; font-weight: 600;', 'critical': 'color: #ff6b6b; font-weight: 700;'}
ADVICE = ('Save your work now. Then lower the 3-D grid points or turn off the comparison viewer, use fewer samples '
          'in Quantum ML, or close other programs. Closed tabs keep their contents in memory, so if memory stays '
          'high, restart QuantumScope.')


class ResourceMonitor(QObject):
    def __init__(self, window, interval_ms=3000, sample=None, warn=None):
        super().__init__(window)
        self.window = window
        self.sample = sample or R.snapshot                       # replaced in tests
        self.warn = warn or self._warn_dialog
        self.interval = interval_ms / 1000
        self.label = QLabel()
        self.label.setObjectName('resourceMeter')
        window.statusBar().addPermanentWidget(self.label)
        self.level, self.warned, self.busy_for, self.last = 'ok', False, 0.0, None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.apply_preferences()
        self.timer.start(interval_ms)

    def enabled(self):
        from quantumscope.gui import preferences as prefs
        return prefs.get('performance/monitor')

    def apply_preferences(self):
        self.label.setVisible(self.enabled())

    def tick(self):
        """One reading: update the meter and warn when needed. Returns the snapshot."""
        if not self.enabled():
            return None
        snap = self.sample()
        self.last = snap
        level = R.memory_level(snap)
        self.busy_for = self.busy_for + self.interval if snap.cpu >= R.BUSY_PERCENT else 0.0
        busy = self.busy_for >= R.BUSY_SECONDS
        text = f'QuantumScope {R.size(snap.process)} · memory {snap.used_share:.0%} used · processor {snap.cpu:.0f}%'
        self.label.setText(('⚠ ' if level != 'ok' or busy else '') + text)
        self.label.setStyleSheet(COLOURS['critical' if level == 'critical' else 'high' if level == 'high' or busy else 'ok'])
        tips = [f'Free memory: {R.size(snap.available)} of {R.size(snap.total)}.']
        if level != 'ok':
            tips.append('Memory is ' + ('nearly full. ' if level == 'critical' else 'getting full. ') + ADVICE)
        if busy:
            tips.append(f'The processor has been fully busy for {int(self.busy_for)} s: QuantumScope (or another '
                        f'program) is computing, so everything may respond slowly.')
        self.label.setToolTip('\n\n'.join(tips))
        if level == 'critical' and not self.warned:
            self.warned = True                                    # once, until memory recovers
            self.warn(snap)
        elif level == 'ok':
            self.warned = False
        self.level = level
        return snap

    def _warn_dialog(self, snap):
        QMessageBox.warning(self.window, 'Memory nearly full',
                            f'Your computer has only {R.size(snap.available)} of memory left '
                            f'(QuantumScope is using {R.size(snap.process)}).\n\n{ADVICE}')


def confirm_memory(parent, needed, what, sample=None):
    """Before a task that may need a lot of memory: True to go ahead (asks only if it may not fit)."""
    from quantumscope.gui import preferences as prefs
    if not prefs.get('performance/monitor'):
        return True
    fine, message = R.check(needed, (sample or R.snapshot)())
    if fine:
        return True
    answer = QMessageBox.question(parent, 'Not much memory free', f'{what}: {message}\n\nContinue anyway?',
                                  QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                  QMessageBox.StandardButton.No)
    return answer == QMessageBox.StandardButton.Yes
