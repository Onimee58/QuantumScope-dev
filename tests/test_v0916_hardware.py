"""v0.9.16: ready-to-paste code for IBM Quantum hardware (no window)."""
import pytest

from quantumscope.physics import hardware_code as H

QASM = ('OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[3];\ncreg m0[1];\ncreg c[3];\nh q[0];\ncx q[0],q[1];\n'
        'measure q[0] -> m0[0];\nif(m0==1) x q[2];\nmeasure q[0] -> c[0];\nmeasure q[2] -> c[2];\n')
KEY = 'A' * 44
CRN = 'crn:v1:bluemix:public:quantum-computing:us-east:a/123:456::'


def made(**kw):
    return H.blocks(QASM, 3, [0, 2], dynamic=True, **kw)


@pytest.mark.parametrize('credentials', [key for key, _ in H.CREDENTIALS])
def test_every_python_block_is_valid_python(credentials):
    for block in made(credentials=credentials, api_key=KEY, crn=CRN):
        if block.language == 'python':
            compile(block.text, block.title, 'exec')
        assert block.title[0].isdigit() and block.text.strip()


def test_the_key_goes_only_where_it_was_asked():
    saved = made(credentials='saved', api_key=KEY, crn=CRN)
    assert [b.title[:2] for b in saved] == ['1.', '2.', '3.', '4.']
    assert KEY in saved[1].text and KEY not in saved[2].text + saved[3].text
    assert 'QiskitRuntimeService()' in saved[3].text and f'channel="{H.CHANNEL}"' in saved[1].text
    environment = made(credentials='environment', api_key=KEY, crn=CRN)
    assert environment[1].language == 'shell' and 'setx IBM_QUANTUM_API_KEY' in environment[1].text
    assert KEY not in environment[3].text and 'os.environ["IBM_QUANTUM_API_KEY"]' in environment[3].text
    assert environment[3].text.count('import os') == 1
    code = made(credentials='code', api_key=KEY, crn=CRN)
    assert [b.title[:2] for b in code] == ['1.', '3.', '4.'] and KEY in code[2].text and CRN in code[2].text
    empty = made(credentials='saved')
    assert H.KEY_HOLDER in empty[1].text and H.CRN_HOLDER in empty[1].text


def test_the_circuit_and_settings_are_in_the_code():
    run = made(shots=500, backend='ibm_torino')[3].text
    assert QASM.rstrip() in run and 'SHOTS = 500' in run and 'MEASURED = [0, 2]' in run
    assert 'service.backend("ibm_torino")' in run and 'least_busy' not in run
    assert 'executor_sampler import Sampler' in run and 'SamplerV2 as Sampler' in run       # new and older versions
    auto = made()[3].text
    assert 'least_busy(operational=True, simulator=False, min_num_qubits=circuit.num_qubits)' in auto
    assert 'dynamic circuits' in made()[3].note and 'dynamic circuits' not in H.blocks(QASM, 3, [0])[3].note
    local = made()[2].text
    assert H.FAKE_DEVICE in local and 'IdealSampler' in local and 'QiskitRuntimeService' not in local


def test_nothing_measured_measures_everything():
    plain = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\nh q[0];\n'
    run = H.blocks(plain, 2, [])[3].text
    assert 'MEASURED = []' in run and 'circuit.measure_all()' in run and 'REGISTER = "c" if "creg c[" in QASM' in run


def test_quotes_in_the_credentials_cannot_break_the_code():
    blocks = H.blocks(QASM, 3, [0], api_key='a"b\\c', credentials='code')
    compile(blocks[2].text, 'run', 'exec')
    assert 'token="a\\"b\\\\c"' in blocks[2].text


def test_credential_checks_and_bad_settings():
    assert H.check_credentials(KEY, CRN) == []
    notes = H.check_credentials('short', 'abc')
    assert len(notes) == 2 and '44 characters' in notes[0] and 'crn:' in notes[1]
    with pytest.raises(ValueError):
        H.blocks(QASM, 3, [0], credentials='email it')
    with pytest.raises(ValueError):
        H.blocks(QASM, 3, [0], shots=0)


def test_the_local_check_runs_when_qiskit_is_installed(capsys):
    pytest.importorskip('qiskit_aer')
    pytest.importorskip('qiskit_ibm_runtime')
    exec(compile(made(shots=300)[2].text, 'step 3', 'exec'), {'__name__': '__main__'})
    out = capsys.readouterr().out
    assert 'Ideal' in out and '|00>' in out and '|11>' in out and '|01>' not in out.split('With')[0]
