"""v0.9.14: long circuits are exported to PDF in readable parts, across pages, instead of being
shrunk to one unreadable line (QUANTUMSCOPE_GUI_TESTS=1)."""
import os
import re
from types import SimpleNamespace

import pytest

if os.environ.get('QUANTUMSCOPE_GUI_TESTS') != '1':
    pytest.skip('GUI tests are opt-in: set QUANTUMSCOPE_GUI_TESTS=1', allow_module_level=True)

QtWidgets = pytest.importorskip('PySide6.QtWidgets')
from quantumscope.gui import circuit_pdf as P  # noqa: E402
from quantumscope.physics.circuits import Gate  # noqa: E402

AVAILABLE = 1123 - 2 * 48 - 125                     # the drawing's width on an A3 page


@pytest.fixture(scope='module')
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def pages(path):
    return len(re.findall(rb'/Type\s*/Page\b(?!s)', open(path, 'rb').read()))


def long_circuit(n=10, columns=600):
    """Like a digitized anneal: CX–RZ–CX ladders, one gate per column."""
    gates = {}
    for c in range(columns):
        q = c % (n - 1)
        gates[(q + 1 if c % 3 == 1 else q, c)] = Gate('RZ', (q + 1,), 0.1) if c % 3 == 1 else Gate('CX', (q, q + 1))
    return gates


def test_short_circuits_stay_on_one_line():
    parts, scale = P.column_segments(5, AVAILABLE)
    assert parts == [(0, 5)] and scale == 1.0
    parts, scale = P.column_segments(12, AVAILABLE)
    assert parts == [(0, 12)] and P.MIN_SCALE <= scale < 1


def test_long_circuits_are_split_at_a_readable_size():
    parts, scale = P.column_segments(2343, AVAILABLE)
    assert scale >= P.MIN_SCALE and parts[0][0] == 0 and parts[-1][1] == 2343
    assert all(a[1] == b[0] for a, b in zip(parts, parts[1:]))                # no column lost or repeated
    assert max(c1 - c0 for c0, c1 in parts) * 110 * scale <= AVAILABLE + 1


def test_blocks_are_never_cut_in_two():
    per = P.column_segments(100, AVAILABLE)[0][0][1]
    block = SimpleNamespace(col=per - 2, end=per + 1)                         # straddles the first break
    parts, _ = P.column_segments(100, AVAILABLE, [block])
    assert all(not (c0 <= block.col < c1 < block.end + 1) for c0, c1 in parts)
    assert parts[0][1] == block.col


def test_the_pdf_has_the_pages_predicted(app, tmp_path):
    gates = long_circuit()
    path = tmp_path / 'long.pdf'
    P.write_circuit_pdf(path, 10, gates, {q: 600 for q in range(10)})
    assert pages(path) == P.pages_needed(10, 601) > 1
    small = tmp_path / 'small.pdf'
    P.write_circuit_pdf(small, 2, {(0, 0): Gate('H', (0,)), (0, 1): Gate('CX', (0, 1))}, {0: 2, 1: 2},
                        include_report=True)
    assert pages(small) == 1 == P.pages_needed(2, 3)


def test_a_long_export_asks_first(app, monkeypatch):
    from PySide6.QtWidgets import QFileDialog, QMessageBox
    from quantumscope.gui.circuit_workspace import CircuitWorkspace
    w = CircuitWorkspace()
    ops = [g for _, g in sorted(long_circuit(columns=3000).items(), key=lambda kv: kv[0][1])]
    w.show_generated_circuit(10, ops, '', 'test')            # packed into fewer columns, still > 10 pages
    asked, chose = [], []
    monkeypatch.setattr(QMessageBox, 'question', lambda *a, **k: asked.append(a[2]) or QMessageBox.StandardButton.No)
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *a, **k: chose.append(1) or ('', ''))
    w.export_pdf()
    assert asked and 'A3' in asked[0] and not chose                           # declined: no file dialog
    w.close()
