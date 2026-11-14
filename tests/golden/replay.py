"""Golden replay: a fixed sequence of circuit-editor operations, fingerprinted after each step.

Each step records the exact final probabilities, the gates, the status line, the verification
panel and the undo depth. tests/test_golden_replay_gui.py runs this script and compares the result
with baseline.json, so any change in how the editor behaves shows up as a readable difference.

    python tests/golden/replay.py out.json         # replay and write the fingerprints
    python tests/golden/replay.py --record          # deliberately replace the baseline

Only re-record after reviewing why the behaviour changed.
"""
import json, sys
import numpy as np
from PySide6.QtWidgets import QApplication
app = QApplication.instance() or QApplication([])
from quantumscope.gui.circuit_workspace import CircuitWorkspace
w = CircuitWorkspace(); w.resize(1400, 900); w.show()
steps = []
def snap(name):
    m = w.model
    try:
        state = m.simulate().column_states[-1]                     # the exact final state
        probs = [round(float(x), 6) for x in (np.abs(np.asarray(state)) ** 2).ravel()[:64]]
    except Exception as exc:
        probs = f'error: {type(exc).__name__}'
    steps.append({'step': name, 'n': m.n, 'gates': sorted(f'{g.name}@{k}' for k, g in m.gates.items()),
                  'status': w.status.text(), 'verify': w.verify_status.text(), 'rows': w.verify_table.rowCount(),
                  'observable': m.observable, 'parameters': {k: round(v, 6) for k, v in m.parameters.items()},
                  'undo': len(m.undo_stack), 'probs': probs})
def run(name, action):
    action(); app.processEvents(); snap(name)
run('start', lambda: None)
run('bell', w.example)
run('add H', lambda: w.place('H', 2, 3))
run('undo', w.undo)
run('redo', w.redo)
run('qubits 3', lambda: w.qubits.setValue(3))
run('ghz', lambda: w.load_example(1))
run('teleport', lambda: w.load_library('teleportation', {'input': '+'}))
run('verify', w.verify_circuit)
run('grover', lambda: w.load_library('grover', {}))
run('qft', lambda: w.load_library('qft', {}))
run('qpe', lambda: w.load_library('qpe', {'t': 3, 'phase': '3/8'}))
run('vqe', lambda: w.load_library('vqe', {'problem': 'h2', 'layers': 1}))
run('vqe verify', w.verify_circuit)
run('qaoa', lambda: w.load_library('qaoa', {'graph': 'ring4', 'layers': 1}))
run('bitflip', lambda: w.load_library('bit_flip_code', {}))
run('clear', w.clear)
run('rx', lambda: (w.qubits.setValue(2), w.place('RX', 0, 0), w.place('X', 1, 1)))
run('undo2', w.undo)
import os as _os
target = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'baseline.json') if sys.argv[1] == '--record' else sys.argv[1]
json.dump(steps, open(target, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(len(steps), 'steps recorded')
import os; os._exit(0)
