"""Ready-to-paste Python that runs a QuantumScope circuit on IBM Quantum hardware (v0.9.16).

QuantumScope never contacts IBM and never stores an API key: it writes the code, and the student
runs it with their own account. The circuit travels as OpenQASM 2 (as Export OpenQASM 2 writes it)
and is loaded with Qiskit's OpenQASM 2 reader, so mid-circuit measurements, resets and conditions
come through as dynamic-circuit operations.

Checked against qiskit 2.6 and qiskit-ibm-runtime 0.52 (November 2026): the account channel is
'ibm_quantum_platform', and the Sampler is qiskit_ibm_runtime.executor_sampler.Sampler from 0.50 on
(SamplerV2 before). No Qt here.
"""
from dataclasses import dataclass

CHANNEL = 'ibm_quantum_platform'
FAKE_DEVICE = 'FakeTorino'             # a real IBM device's layout and noise, simulated on your computer
CREDENTIALS = (('saved', 'Save them once on this computer (recommended)'),
               ('environment', 'Read them from environment variables'),
               ('code', 'Write them into the script (do not share it)'))
KEY_HOLDER, CRN_HOLDER = '<your API key>', '<your instance CRN>'


@dataclass
class Block:
    title: str
    text: str
    note: str = ''
    language: str = 'python'           # or 'shell'


def _quoted(text):
    return text.replace('\\', '\\\\').replace('"', '\\"')


def check_credentials(api_key, crn):
    """Gentle warnings about what was typed (nothing is sent anywhere)."""
    notes = []
    if api_key and (len(api_key.strip()) != 44 or ' ' in api_key.strip()):
        notes.append('IBM Quantum API keys are 44 characters with no spaces: check that the whole key was copied.')
    if crn and not crn.strip().startswith('crn:'):
        notes.append('An instance CRN starts with "crn:" (IBM Quantum Platform → Instances → copy the CRN).')
    return notes


def blocks(qasm, n, measured, *, shots=1024, backend='', credentials='saved', api_key='', crn='',
           dynamic=False, title='QuantumScope circuit', version=''):
    """The code blocks to show, in order: install, account, test on this computer, run on hardware."""
    if credentials not in dict(CREDENTIALS):
        raise ValueError(f'Unknown credentials choice {credentials!r}')
    if not 1 <= int(shots) <= 100_000:
        raise ValueError('Shots must be between 1 and 100,000')
    key, instance = (api_key.strip() or KEY_HOLDER), (crn.strip() or CRN_HOLDER)
    measured = sorted(int(q) for q in measured)
    result = [Block('1. Install Qiskit (once)', 'pip install qiskit qiskit-ibm-runtime qiskit-aer', language='shell',
                    note='In a terminal, ideally inside a Python virtual environment. qiskit-aer is only for step 3.')]
    if credentials == 'saved':
        result.append(Block('2. Save your IBM Quantum account (once)', '\n'.join((
            'from qiskit_ibm_runtime import QiskitRuntimeService',
            '',
            'QiskitRuntimeService.save_account(',
            f'    channel="{CHANNEL}",',
            f'    token="{_quoted(key)}",          # your API key (IBM Quantum Platform → API key)',
            f'    instance="{_quoted(instance)}",  # your instance CRN (Instances → copy the CRN)',
            '    set_as_default=True,',
            '    overwrite=True,',
            ')',
            'print("Saved. You can delete this script now.")')),
            note='Run once, then delete it: the key is then stored in your user folder by Qiskit, not in your '
                 'scripts. Anyone with your API key can spend your quantum time.'))
    elif credentials == 'environment':
        result.append(Block('2. Put your account in environment variables', '\n'.join((
            '# Linux and macOS (bash, zsh): add these lines to ~/.bashrc or ~/.zshrc',
            f'export IBM_QUANTUM_API_KEY="{_quoted(key)}"',
            f'export IBM_QUANTUM_CRN="{_quoted(instance)}"',
            '',
            '# Windows (PowerShell): run once, then open a new terminal',
            f'setx IBM_QUANTUM_API_KEY "{_quoted(key)}"',
            f'setx IBM_QUANTUM_CRN "{_quoted(instance)}"')), language='shell',
            note='The script reads them when it runs, so the key never appears in the code.'))
    shared = _circuit_code(qasm, measured, int(shots))
    result.append(Block('3. Try it on your computer first (no account needed)', '\n'.join((
        f'"""{title}: ideal, then with the noise of a simulated IBM device ({FAKE_DEVICE})."""',
        'from qiskit import qasm2',
        'from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager',
        'from qiskit_aer.primitives import SamplerV2 as IdealSampler',
        'from qiskit_ibm_runtime import SamplerV2',
        f'from qiskit_ibm_runtime.fake_provider import {FAKE_DEVICE}',
        '',
        shared,
        '',
        'ideal = IdealSampler().run([circuit], shots=SHOTS).result()[0]',
        'show("Ideal (as QuantumScope computes it)", ideal)',
        f'device = {FAKE_DEVICE}()',
        'isa = generate_preset_pass_manager(backend=device, optimization_level=1).run(circuit)',
        'show(f"With {device.name}\'s noise (simulated)", SamplerV2(mode=device).run([isa], shots=SHOTS).result()[0])')),
        note='Free and quick: check the circuit and the code before spending hardware time.'))
    if credentials == 'saved':
        service = 'service = QiskitRuntimeService()                 # the account saved in step 2'
    elif credentials == 'environment':
        service = '\n'.join(('service = QiskitRuntimeService(', f'    channel="{CHANNEL}",',
                             '    token=os.environ["IBM_QUANTUM_API_KEY"],',
                             '    instance=os.environ["IBM_QUANTUM_CRN"],', ')'))
    else:
        service = '\n'.join(('service = QiskitRuntimeService(', f'    channel="{CHANNEL}",',
                             f'    token="{_quoted(key)}",          # do not share this script',
                             f'    instance="{_quoted(instance)}",', ')'))
    chosen = backend.strip()
    pick = (f'backend = service.backend("{_quoted(chosen)}")' if chosen else
            'backend = service.least_busy(operational=True, simulator=False, min_num_qubits=circuit.num_qubits)')
    result.append(Block('4. Run it on IBM Quantum hardware', '\n'.join((
        f'"""{title} on IBM Quantum hardware.' + (f' Written by QuantumScope {version}.' if version else ''),
        '',
        'The job waits in a queue and uses your plan\'s quantum time; IBM Quantum Platform → Workloads',
        'shows it. Run step 3 first."""',
        *(('import os',) if credentials == 'environment' else ()),
        'from qiskit import qasm2',
        'from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager',
        'from qiskit_ibm_runtime import QiskitRuntimeService',
        'try:',
        '    from qiskit_ibm_runtime.executor_sampler import Sampler   # qiskit-ibm-runtime 0.50 and later',
        'except ImportError:',
        '    from qiskit_ibm_runtime import SamplerV2 as Sampler       # earlier versions',
        '',
        shared,
        '',
        service,
        pick,
        'print("Running on", backend.name)',
        '# Rewrite the circuit in the gates and connections this device has (its "ISA")',
        'isa = generate_preset_pass_manager(backend=backend, optimization_level=1).run(circuit)',
        'job = Sampler(mode=backend).run([isa], shots=SHOTS)',
        'print("Job ID:", job.job_id(), "(waiting in the queue…)")',
        'show(f"On {backend.name}", job.result()[0])')),
        note='Compare it with step 3: the differences are the hardware\'s noise. '
             + ('Mid-circuit measurements, resets and conditions run as dynamic circuits, which IBM devices '
                'support. ' if dynamic else '')
             + 'The free Open Plan includes a few minutes of quantum time per 28 days.'))
    return result


def _circuit_code(qasm, measured, shots):
    """The circuit (from OpenQASM 2), the shots, and show(): counts in QuantumScope's order."""
    reading = ('MEASURED = ' + repr(measured) + '   # the qubits QuantumScope measures at the end, q0 first'
               if measured else
               'MEASURED = []   # QuantumScope measured nothing at the end: measure every qubit')
    lines = [f'QASM = """{qasm.rstrip()}\n"""', '', f'SHOTS = {shots}', reading,
             'circuit = qasm2.loads(QASM, custom_instructions=qasm2.LEGACY_CUSTOM_INSTRUCTIONS)',
             'if not MEASURED:',
             '    circuit.measure_all()',
             '    MEASURED = list(range(circuit.num_qubits))',
             'REGISTER = "c" if "creg c[" in QASM else "meas"',
             '',
             '',
             'def show(heading, result):',
             '    """Counts with q0 first, as in QuantumScope (Qiskit writes qubit 0 on the right)."""',
             '    counts = getattr(result.data, REGISTER).get_counts()',
             '    ours = {}',
             '    for bits, count in counts.items():',
             '        key = "".join(bits[::-1][q] for q in MEASURED)',
             '        ours[key] = ours.get(key, 0) + count',
             '    print(heading)',
             '    for key, count in sorted(ours.items(), key=lambda kv: -kv[1])[:16]:',
             '        print(f"  |{key}>  {count:6d}  {count / SHOTS:7.2%}")']
    return '\n'.join(lines)

