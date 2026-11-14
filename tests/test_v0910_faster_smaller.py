"""v0.9.10: remembered results (hydrogen grids, kernel matrices) and smaller installers (no window)."""
import os
import sys
from types import SimpleNamespace

import numpy as np
import pytest

from quantumscope import caching

TOOLS = os.path.join(os.path.dirname(__file__), '..', 'tools')
sys.path.insert(0, TOOLS)
import pyinstaller_trim as T  # noqa: E402
sys.path.remove(TOOLS)


# ---- caching ---------------------------------------------------------------------------------------------
def test_the_cache_remembers_the_newest_within_its_budget():
    calls = []
    cache = caching.Cache('test', limit=3 * 8000, entries=10)

    def make(k):
        calls.append(k)
        return np.full(1000, k, float)                      # 8,000 bytes
    for k in (1, 2, 3):
        cache.get(k, lambda k=k: make(k))
    assert cache.get(1, lambda: make(1))[0] == 1 and calls == [1, 2, 3]        # remembered
    cache.get(4, lambda: make(4))                                             # over budget: 2 goes (least recent)
    assert list(cache.items) == [3, 1, 4] and cache.hits == 1 and cache.misses == 4
    big = cache.get('big', lambda: np.zeros(10_000))                          # larger than the budget: not kept
    assert big.shape == (10_000,) and 'big' not in cache.items
    cache.clear()
    assert not cache.items


def test_remembered_results_cannot_be_changed_by_a_caller():
    cache = caching.Cache('test', limit=10 ** 6)
    value = cache.get('k', lambda: (np.ones(3), np.zeros(2)))
    with pytest.raises(ValueError):
        value[0][0] = 5
    caching.clear_all()
    assert not cache.items


def test_fingerprints_follow_contents_shape_and_type():
    a = np.arange(6.0)
    assert caching.fingerprint(a) == caching.fingerprint(a.copy())
    assert caching.fingerprint(a) != caching.fingerprint(a.reshape(2, 3))
    assert caching.fingerprint(a) != caching.fingerprint(a.astype(np.float32))
    b = a.copy()
    b[3] += 1e-12
    assert caching.fingerprint(a) != caching.fingerprint(b)


def test_kernel_matrices_are_remembered_and_identical():
    from quantumscope.ml import kernels as K
    K.KERNELS.clear()
    X = np.random.default_rng(1).uniform(0, np.pi, (40, 3))
    hits = K.KERNELS.hits
    first = K.kernel(X, kind='zz', bandwidth=0.5)
    again = K.kernel(X.copy(), kind='zz', bandwidth=0.5)
    assert again is first and K.KERNELS.hits == hits + 1 and not first.flags.writeable
    other = K.kernel(X, kind='zz', bandwidth=1.0)
    assert other is not first and not np.allclose(other, first)
    S = K.states(X, 'zz', 2, 0.5)
    assert np.allclose(first, np.abs(S.conj() @ S.T) ** 2)                   # the same numbers as before
    noisy = K.estimate(first, shots=100, rng=np.random.default_rng(0), symmetric=True)
    assert noisy.flags.writeable and not np.allclose(noisy, first)             # shots are never remembered
    K.KERNELS.clear()


# ---- smaller installers ------------------------------------------------------------------------------------
UNUSED_FILES = ['PySide6/Qt/lib/libQt6Quick.so.6', 'PySide6/Qt6Quick.dll', 'PySide6/Qt/lib/QtQuick.framework/Versions/A/QtQuick',
                'PySide6/Qt/lib/libQt6QmlModels.so.6', 'PySide6/Qt/lib/libQt6VirtualKeyboard.so.6',
                'PySide6/Qt/plugins/platforminputcontexts/libqtvirtualkeyboardplugin.so', 'PySide6/Qt/lib/libQt6Pdf.so.6',
                'PySide6\\Qt\\plugins\\imageformats\\qpdf.dll', 'PySide6/QtDataVisualization.abi3.so',
                'PySide6/Qt/plugins/platforms/libqeglfs.so', 'PySide6/Qt/translations/qtbase_de.qm']
NEEDED_FILES = ['PySide6/Qt/lib/libQt6Core.so.6', 'PySide6/Qt6Gui.dll', 'PySide6/Qt/lib/QtWidgets.framework/Versions/A/QtWidgets',
                'PySide6/Qt/lib/libQt6OpenGL.so.6', 'PySide6/Qt/lib/libQt6Network.so.6', 'PySide6/Qt/lib/libQt6Svg.so.6',
                'PySide6/Qt/plugins/platforms/libqxcb.so', 'PySide6/Qt/plugins/platforms/qwindows.dll',
                'PySide6/Qt/plugins/platforms/libqcocoa.dylib', 'PySide6/Qt/plugins/imageformats/libqjpeg.so',
                'PySide6/Qt/plugins/imageformats/libqsvg.so', 'pyqtgraph/colors/maps/viridis.csv', 'quantumscope/assets/check.svg']


@pytest.mark.parametrize('path', UNUSED_FILES)
def test_unused_qt_files_are_left_out(path):
    assert T.unused(path)


@pytest.mark.parametrize('path', NEEDED_FILES)
def test_what_the_app_needs_stays(path):
    assert not T.unused(path)


def test_trim_edits_the_analysis():
    analysis = SimpleNamespace(binaries=[(p, '/x/' + p, 'BINARY') for p in UNUSED_FILES[:3] + NEEDED_FILES[:2]],
                               datas=[('PySide6/Qt/translations/qt_fr.qm', '/x', 'DATA'), ('quantumscope/assets/check.svg', '/x', 'DATA')])
    dropped = T.trim(analysis)
    assert len(dropped) == 4 and [e[0] for e in analysis.binaries] == NEEDED_FILES[:2]
    assert [e[0] for e in analysis.datas] == ['quantumscope/assets/check.svg']


def test_the_workflow_strips_and_trims():
    workflow = open('.github/workflows/release.yml').read()
    assert '--strip' in workflow and 'RUNNER_OS" = "Windows"' in workflow
    assert 'TRIM_ARGS="$(python tools/pyinstaller_trim.py)"' in workflow and '$STRIP $TRIM_ARGS' in workflow
    assert T.exclude_arguments() == [f'--exclude-module={m}' for m in T.EXCLUDE_MODULES]
    sys.path.insert(0, TOOLS)
    try:
        import pyinstaller_compiled as P
    finally:
        sys.path.remove(TOOLS)
    import tempfile
    with tempfile.TemporaryDirectory() as folder:
        spec = os.path.join(folder, 'QuantumScope.spec')
        open(spec, 'w').write('a = Analysis([])\npyz = PYZ(a.pure)\n')
        P.add_to_spec(spec, folder)
        text = open(spec).read()
        assert text.index('_qs_compiled.swap(a,') < text.index('_qs_trim.trim(a)') < text.index('pyz = PYZ(')
