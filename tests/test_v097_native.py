"""v0.9.7: installers carry QuantumScope's modules as native code (Cython), not readable bytecode.

Compiling needs Cython and a C compiler, so the release workflow does it; these tests check the
tools that pick, check and bundle the modules, without compiling."""
import os
import sys
from importlib.machinery import EXTENSION_SUFFIXES
from types import SimpleNamespace

import pytest

TOOLS = os.path.join(os.path.dirname(__file__), '..', 'tools')
sys.path.insert(0, TOOLS)
import cython_compile as C  # noqa: E402
import pyinstaller_compiled as P  # noqa: E402
sys.path.remove(TOOLS)


def test_every_module_but_package_files_and_the_start_script_is_compiled():
    names = [dotted for dotted, _ in C.modules()]
    assert 'quantumscope.physics.circuits' in names and 'quantumscope.gui.main_window' in names
    assert 'quantumscope.ml.kernels' in names and 'quantumscope.learn.lessons' in names
    assert not [n for n in names if n.endswith(('__init__', '__main__'))]
    assert len(names) == len(set(names)) > 90


def test_compiled_files_behave_like_python():
    assert C.DIRECTIVES['annotation_typing'] is False and C.DIRECTIVES['language_level'] == 3
    assert C.DIRECTIVES['binding'] is True and C.DIRECTIVES['embedsignature'] is False


def test_powers_of_whole_numbers_that_would_become_decimals_are_found(tmp_path):
    (tmp_path / 'a.c').write_text(
        '/* "quantumscope/physics/noise.py":313\n'
        '  __pyx_t_12 = pow(2.0, ((double)__pyx_t_10));\n'
        '/* "quantumscope/physics/hydrogen.py":97\n'
        '  __pyx_t_2 = PyFloat_FromDouble(pow(__pyx_v_delta, 3.0));\n'       # a decimal already: fine
        '  z.real = pow(a.real, b.real);\n')
    assert C.whole_numbers_as_decimals(str(tmp_path)) == ['quantumscope/physics/noise.py:313']


def fake_build(tmp_path, names):
    for name in names:
        path = tmp_path.joinpath(*name.split('.')[:-1])
        path.mkdir(parents=True, exist_ok=True)
        (path / (name.rsplit('.', 1)[-1] + EXTENSION_SUFFIXES[0])).write_bytes(b'')


def test_the_spec_swaps_bytecode_for_native_modules(tmp_path, monkeypatch):
    monkeypatch.setattr(C, 'modules', lambda: [('quantumscope.physics.circuits', ''), ('quantumscope.resources', ''),
                                               ('quantumscope.physics.circuit', '')])
    fake_build(tmp_path, ['quantumscope.physics.circuits', 'quantumscope.resources', 'quantumscope.physics.circuit'])
    analysis = SimpleNamespace(binaries=[], pure=[('quantumscope', 'x/__init__.py', 'PYMODULE'),
                                                  ('quantumscope.physics.circuits', 'x/circuits.py', 'PYMODULE'),
                                                  ('quantumscope.resources', 'x/resources.py', 'PYMODULE'),
                                                  ('numpy', 'n/__init__.py', 'PYMODULE')])
    swapped = P.swap(analysis, str(tmp_path))
    assert swapped == ['quantumscope.physics.circuits', 'quantumscope.resources']
    assert [e[0] for e in analysis.pure] == ['quantumscope', 'numpy']
    dest, src, kind = analysis.binaries[0]
    assert dest == 'quantumscope/physics/circuits' + EXTENSION_SUFFIXES[0] and kind == 'EXTENSION'
    assert os.path.isfile(src)


def test_a_module_left_uncompiled_stops_the_build(tmp_path, monkeypatch):
    monkeypatch.setattr(C, 'modules', lambda: [('quantumscope.resources', '')])
    analysis = SimpleNamespace(binaries=[], pure=[('quantumscope.resources', 'x/resources.py', 'PYMODULE')])
    with pytest.raises(SystemExit, match='would ship as bytecode'):
        P.swap(analysis, str(tmp_path))


def test_the_step_goes_into_the_spec_once(tmp_path):
    spec = tmp_path / 'QuantumScope.spec'
    spec.write_text('a = Analysis([])\npyz = PYZ(a.pure)\nexe = EXE(pyz)\n')
    P.add_to_spec(str(spec), str(tmp_path / 'out'))
    P.add_to_spec(str(spec), str(tmp_path / 'out'))
    text = spec.read_text()
    assert text.count(P.MARK) == 1 and text.index('_qs_compiled.swap(a,') < text.index('pyz = PYZ(')
    compile(text, 'QuantumScope.spec', 'exec')


def test_the_release_workflow_compiles_and_checks():
    workflow = open('.github/workflows/release.yml').read()
    order = ['python tools/cython_compile.py build/compiled', 'makespec', 'python tools/pyinstaller_compiled.py',
             'PyInstaller --noconfirm --clean QuantumScope.spec']
    assert [workflow.index(step) for step in order] == sorted(workflow.index(step) for step in order)
    assert workflow.count('QUANTUMSCOPE_EXPECT_NATIVE') == 3 and 'cython>=3.1' in workflow


def test_installers_are_not_kept_as_artifacts_on_tagged_releases():
    """Artifacts count against the private repository's storage quota (0.9.9 fix): tagged releases publish
    to the public release only; artifacts are kept for manual runs or a failed publish, for 3 days."""
    workflow = open('.github/workflows/release.yml').read()
    step = workflow[workflow.index('uses: actions/upload-artifact'):]
    assert 'retention-days: 3' in step[:400] and 'continue-on-error: true' in workflow
    head = workflow[:workflow.index('uses: actions/upload-artifact')]
    assert "failure() || !startsWith(github.ref, 'refs/tags/v')" in head[-400:]
    assert workflow.index('gh release upload') < workflow.index('uses: actions/upload-artifact')
