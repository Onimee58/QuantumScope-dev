"""v0.8.0: the user guide PDF's structure, its references, and the builder's figure floats."""
import os
import re
import sys

import pytest

ROOT = os.path.join(os.path.dirname(__file__), '..')
PDF = os.path.join(ROOT, 'src', 'quantumscope', 'assets', 'QuantumScope-User-Guide.pdf')
REFS = os.path.join(ROOT, 'docs', 'references.md')


def test_references_are_numbered_and_well_formed():
    text = open(REFS, encoding='utf-8').read()
    numbers = [int(n) for n in re.findall(r'^(\d+)\. ', text, re.M)]
    assert numbers == list(range(1, len(numbers) + 1)) and len(numbers) >= 41
    for doi in re.findall(r'https://doi\.org/(\S+)', text):
        assert re.match(r'^10\.\d{4,5}/\S+[^.,;]$', doi), doi                    # a DOI, no trailing punctuation
    for must in ('Havlíček', 'Bravo-Prieto', 'Thanasilp', 'Cortes, C. & Vapnik', 'Fisher, R. (1936)', 'MNIST'):
        assert must in text, must


def test_the_pdf_has_a_title_page_bookmarks_links_and_page_numbers():
    pypdf = pytest.importorskip('pypdf')
    reader = pypdf.PdfReader(PDF)
    texts = [re.sub(r'\s+', ' ', page.extract_text() or '') for page in reader.pages]
    from quantumscope import __version__
    for words in ('QuantumScope', 'User Guide', 'Md. Saif Hassan Onim, PhD', 'Postdoctoral Fellow',
                  'Southern Methodist University', f'Version {__version__}', 'github.com/Onimee58/QuantumScope'):
        assert words in texts[0], words                                              # the cover (v0.8.4)
    assert texts[1].startswith('Contents') and 'List of figures' in ' '.join(texts[2:4])

    def walk(items):
        for item in items:
            if isinstance(item, list):
                yield from walk(item)
            else:
                yield item.title, reader.get_destination_page_number(item)
    marks = list(walk(reader.outline))
    titles = [t for t, _ in marks]
    for chapter in ('Quantum ML', 'Quantum Circuits', 'References'):
        assert any(chapter in t for t in titles), chapter
    norm = lambda t: re.sub(r'[^a-z0-9]', '', t.lower())                           # noqa: E731
    assert all(norm(t)[:25] in norm(texts[p]) for t, p in marks)                  # each bookmark on its page
    links = [a.get_object() for page in reader.pages[:4] for a in (page.get('/Annots') or [])]
    assert len(links) >= len(marks) - 2 and all(reader.get_page_number(a['/Dest'][0].get_object()) is not None
                                                 for a in links)
    assert all(re.search(rf'(^|\s){k + 1}\s*$', texts[k]) for k in range(1, len(texts)))   # footers


def test_figures_float_within_their_section_only():
    sys.path.insert(0, os.path.join(ROOT, 'tools'))
    from guide_pdf import _float_figures
    markdown = '## A\n\n![one](a.png)\n\nText 1.\n\nText 2.\n\n## B\n\nText 3.\n'
    assert _float_figures(markdown, {0: 1}).index('![one]') > _float_figures(markdown, {0: 1}).index('Text 1.')
    far = _float_figures(markdown, {0: 9})
    assert far.index('Text 2.') < far.index('![one]') < far.index('## B')          # never past the next heading


def test_guide_text_is_dark_even_when_the_app_uses_its_dark_theme():
    """v0.8.4: the guide tool switches to the dark theme for its screenshots, and text without its own
    colour then came out near-white on white paper (v0.8.2 to v0.8.4). Pages now print in a fixed
    palette."""
    QtWidgets = pytest.importorskip('PySide6.QtWidgets', exc_type=ImportError)
    from PySide6.QtCore import QRectF
    from PySide6.QtGui import QColor, QImage, QPainter, QTextDocument
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    from quantumscope.gui.theme import apply_theme
    apply_theme('dark')                                                         # as the guide tool does
    sys.path.insert(0, os.path.join(ROOT, 'tools'))
    import guide_pdf
    doc = QTextDocument()
    doc.setHtml('<p>' + 'Plain body text without its own colour. ' * 20 + '</p>')
    doc.setTextWidth(400)
    image = QImage(400, 200, QImage.Format.Format_RGB32)
    image.fill(QColor('white'))
    painter = QPainter(image)
    guide_pdf.draw_text(painter, doc, QRectF(0, 0, 400, 200))
    painter.end()
    darkest = min(QColor(image.pixel(x, y)).lightness() for x in range(0, 400, 2) for y in range(0, 120, 2))
    assert darkest < 80, f'the text is too pale (darkest lightness {darkest})'
    assert app is not None


def test_the_committed_guide_has_dark_body_text():
    import shutil
    import subprocess
    if not shutil.which('pdftoppm'):
        pytest.skip('needs pdftoppm to render the PDF')
    PIL = pytest.importorskip('PIL.Image')
    import tempfile
    with tempfile.TemporaryDirectory() as folder:
        subprocess.run(['pdftoppm', '-r', '40', '-f', '2', '-l', '2', '-png', PDF, os.path.join(folder, 'p')], check=True)
        page = PIL.open(os.path.join(folder, sorted(os.listdir(folder))[0])).convert('L')      # the contents page
    import numpy as np
    values = np.asarray(page)                                         # measured: broken 0 dark pixels, darkest
    ink, darkest = int(np.sum(values < 110)), int(values.min())       # 168; fixed 1013, darkest 24
    assert darkest < 80 and ink > 300, f'the contents page has no dark text ({ink} dark pixels, darkest {darkest})'
