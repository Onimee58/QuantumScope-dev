"""Build the user guide PDF from docs/user-guide.md and docs/references.md (an author's tool).

Layout is done by Qt (QTextDocument), page by page, so the builder knows exactly where every
heading and figure lands. That gives:
  - a title page (the logo and the author), then Contents and List of figures with page numbers;
  - figures numbered and captioned from their alt text;
  - blank-spot repair: an image that leaves a large gap at the bottom of a page is shrunk to fit
    it (down to 60%), and a heading stranded at the bottom of a page moves to the next one;
  - page numbers in the footer (not on the title page);
  - PDF bookmarks for every chapter and section, and clickable Contents entries (pypdf, BSD).
"""
import html as htmlmod
import os
import re

try:                                    # the layout needs Qt; the text helpers (figure floats) do not
    from PySide6.QtCore import QMarginsF, QRectF, QSizeF, Qt, QUrl
    from PySide6.QtGui import QFont, QImage, QPageLayout, QPageSize, QPainter, QTextDocument
    from PySide6.QtWidgets import QApplication
    from PySide6.QtPrintSupport import QPrinter
except ImportError:                     # e.g. a CI machine without graphics libraries
    QMarginsF = QRectF = QSizeF = Qt = QUrl = QFont = QImage = QPageLayout = QPageSize = None
    QPainter = QTextDocument = QApplication = QPrinter = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, 'docs')
AUTHOR = 'Md. Saif Hassan Onim, PhD'
AUTHOR_LINES = ('Postdoctoral Fellow, Electrical and Computer Engineering',
                'Southern Methodist University, Dallas, Texas')
REPOSITORY = 'github.com/Onimee58/QuantumScope'
MARK = os.path.join(ROOT, 'src', 'quantumscope', 'assets', 'quantumscope-mark.svg')
NAVY, PANEL, CYAN, MIST, MUTED, ACCENT = '#0b1420', '#13263f', '#5ae6ff', '#e6eef7', '#8fa3ba', '#ff9a5a'
MAX_W, MAX_H = 640, 400                 # largest figure, in document units (96 per inch)
FOOTER = 26                             # room for the page number at the bottom of each page
GAP_LIMIT = 0.25                        # a page ending with more than this share empty is a "blank spot"
MIN_SCALE = 0.6                         # figures shrink at most to this to fill a gap


def _markdown():
    with open(os.path.join(DOCS, 'user-guide.md'), encoding='utf-8') as handle:
        guide = handle.read()
    with open(os.path.join(DOCS, 'references.md'), encoding='utf-8') as handle:
        refs = handle.read()
    number = len(re.findall(r'^## \d+\.', guide, re.M)) + 1
    refs = re.sub(r'^# References', f'## {number}. References', refs, count=1, flags=re.M)
    refs = re.sub(r'^## (?!\d)', '### ', refs, flags=re.M)               # groups become sections
    return guide.rstrip() + '\n\n' + refs


def _float_figures(markdown, floats):
    """Move figure k down past floats[k] paragraphs or lists, never past a heading (like LaTeX floats)."""
    blocks = re.split(r'\n\s*\n', markdown.strip())
    figure_blocks = [i for i, b in enumerate(blocks) if b.lstrip().startswith('![')]
    for k in sorted(floats, reverse=True):
        i = figure_blocks[k]
        steps = 0
        while steps < floats[k] and i + 1 < len(blocks) and not blocks[i + 1].lstrip().startswith(('#', '![')):
            blocks[i], blocks[i + 1] = blocks[i + 1], blocks[i]
            i += 1
            steps += 1
    return '\n\n'.join(blocks) + '\n'


def _can_float(markdown, floats, k):
    """Whether figure k can move one more block down within its section."""
    before = _float_figures(markdown, floats)
    after = _float_figures(markdown, {**floats, k: floats.get(k, 0) + 1})
    return before != after


def _body_html(markdown):
    """The guide as HTML, with numbered, captioned, sized figures. Returns (html, figures)."""
    figures = [(alt, src) for alt, src in re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', markdown)]
    doc = QTextDocument()
    doc.setMarkdown(markdown)
    html = doc.toHtml()
    html = html[html.index('<body'):]
    html = html[html.index('>') + 1:html.rindex('</body>')]
    count = [0]

    def figure(match):
        k = count[0]
        count[0] += 1
        alt, src = figures[k]
        image = QImage(os.path.join(DOCS, src))
        scale = min(1.0, MAX_W / image.width(), MAX_H / image.height())
        w, h = int(image.width() * scale), int(image.height() * scale)
        return (f'<p align="center" style="margin-top:8px; margin-bottom:12px;"><a name="figure-{k}"></a>'
                f'<img src="{src}" width="{w}" height="{h}" /><br />'
                f'<span style="font-size:9pt; color:#4a5568;"><b>Figure {k + 1}.</b> {htmlmod.escape(alt)}</span></p>')
    html = re.sub(r'<p[^>]*><img src="[^"]+"[^>]*/></p>', figure, html)
    assert count[0] == len(figures), 'every figure must be on its own paragraph'
    return html, figures


def _front(headings, figures, pages):
    """Title page, Contents and List of figures (page numbers from `pages`, or placeholders)."""
    def page(key):
        return str(pages.get(key, '000'))
    rows = []
    for k, (level, text) in enumerate(headings):
        indent, weight = (0, 600) if level == 2 else (22, 400)
        rows.append(f'<tr><td style="padding-left:{indent}px; font-weight:{weight};">{htmlmod.escape(text)}</td>'
                    f'<td align="right" style="font-weight:{weight};">{page(("h", k))}</td></tr>')
    fig_rows = [f'<tr><td>Figure {k + 1}. {htmlmod.escape(alt)}</td><td align="right">{page(("f", k))}</td></tr>'
                for k, (alt, _) in enumerate(figures)]
    table = '<table width="100%" cellspacing="0" cellpadding="3">{}</table>'
    return ('<p style="page-break-after:always;">&nbsp;</p>'            # the cover: painted separately
            '<h1>Contents</h1>' + table.format(''.join(rows)) +
            '<p style="page-break-after:always;"></p>'
            '<h1>List of figures</h1>' + table.format(''.join(fig_rows)) +
            '<p style="page-break-after:always;"></p>')


class Guide:
    def __init__(self):
        QApplication.instance() or QApplication([])
        self.printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        self.printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        self.printer.setPageLayout(QPageLayout(QPageSize(QPageSize.PageSizeId.Letter), QPageLayout.Orientation.Portrait,
                                               QMarginsF(18, 18, 18, 18), QPageLayout.Unit.Millimeter))
        area = self.printer.pageLayout().paintRect(QPageLayout.Unit.Inch)
        self.W, self.H = area.width() * 96.0, area.height() * 96.0 - FOOTER
        self.markdown = _markdown()
        self.breaks = set()                       # heading numbers that start a new page
        self.shrink = {}                          # figure number → scale
        self.floats = {}                          # figure number → paragraphs it moves down
        self._rebuild()

    def _rebuild(self):
        self.body, self.figures = _body_html(_float_figures(self.markdown, self.floats))

    def _document(self, pages):
        body = self.body
        for k, scale in self.shrink.items():      # shrink chosen figures
            body = re.sub(rf'(<a name="figure-{k}"></a><img src="[^"]+" width=")(\d+)(" height=")(\d+)',
                          lambda m: f'{m.group(1)}{int(int(m.group(2)) * scale)}{m.group(3)}{int(int(m.group(4)) * scale)}',
                          body)
        heads = list(re.finditer(r'<h([23])([^>]*)>', body))
        for k in sorted(self.breaks, reverse=True):
            m = heads[k]
            body = body[:m.start()] + f'<h{m.group(1)}{m.group(2)} style="page-break-before:always;"' + \
                body[m.start() + 3 + len(m.group(2)):]
        doc = QTextDocument()
        font = QFont(doc.defaultFont())
        font.setPointSizeF(10.5)
        doc.setDefaultFont(font)
        doc.setBaseUrl(QUrl.fromLocalFile(DOCS + os.sep))
        headings = [(int(m.group(1)), htmlmod.unescape(re.sub(r'<[^>]+>', '', m.group(2))).strip())
                    for m in re.finditer(r'<h([23])[^>]*>(.*?)</h\1>', body, re.S)]
        doc.setHtml('<html><body>' + _front(headings, self.figures, pages) + body + '</body></html>')
        doc.setPageSize(QSizeF(self.W, self.H))
        doc.documentLayout().documentSize()                    # lay it out
        return doc, headings

    def _scan(self, doc):
        """Where every block is: (page, top, bottom, kind, index) in layout order. The body starts at
        the guide's title; before it come the title page, Contents and List of figures."""
        layout, out = doc.documentLayout(), []
        heading_k = figure_k = 0
        in_body = False
        self.front_pages = {}
        block = doc.begin()
        while block.isValid():
            rect = layout.blockBoundingRect(block)
            level = block.blockFormat().headingLevel()
            text = block.text().strip()
            kind, index = 'text', None
            if level == 1 and not in_body:
                if text == 'QuantumScope User Guide':
                    in_body = True
                else:
                    self.front_pages[text] = int(rect.top() // self.H)   # Contents, List of figures
            elif in_body and level in (2, 3):
                kind, index = 'heading', heading_k
                heading_k += 1
            elif in_body and any(f.fragment().charFormat().isImageFormat() for f in _fragments(block)):
                kind, index = 'figure', figure_k
                figure_k += 1
            lines = block.layout()
            if lines.lineCount():                                   # pages by line: Qt moves lines, not blocks
                first, last_line = lines.lineAt(0), lines.lineAt(lines.lineCount() - 1)
                top = rect.top() + first.y()
                bottom = rect.top() + last_line.y() + last_line.height()
            else:
                top, bottom = rect.top(), rect.bottom()
            page = int(top // self.H)
            out.append((page, top, bottom, kind, index, level))
            block = block.next()
        return out

    def layout(self, pages=None, repair=True):
        """Lay out, repairing blank spots, until the page numbers are stable."""
        pages = pages or {}
        for _ in range(60):
            doc, headings = self._document(pages)
            scan = self._scan(doc)
            changed = False
            if repair:
                for i, (page, top, bottom, kind, index, level) in enumerate(scan):
                    nxt = scan[i + 1] if i + 1 < len(scan) else None
                    if kind == 'heading' and nxt is not None and nxt[0] > page and index not in self.breaks:
                        if nxt[3] == 'figure' and _can_float(self.markdown, self.floats, nxt[4]):
                            self.floats[nxt[4]] = self.floats.get(nxt[4], 0) + 1   # text first, figure after
                            self._rebuild()
                        else:
                            self.breaks.add(index)                 # a heading alone at the bottom: move it
                        changed = True
                        break
                    if kind == 'figure' and i > 0 and top - page * self.H < 60 and scan[i - 1][0] < page:
                        end = max(b for (pg, t, b, *_r) in scan[:i] if b <= page * self.H)
                        gap = page * self.H - end
                        if gap > GAP_LIMIT * self.H and bottom > top:
                            current = self.shrink.get(index, 1.0)
                            scale = current * max(0.0, gap - 40) / (bottom - top)
                            if scale >= MIN_SCALE:
                                if abs(scale - current) > 0.01:
                                    self.shrink[index] = min(current, scale)
                                    changed = True
                                    break
                            elif _can_float(self.markdown, self.floats, index):
                                self.floats[index] = self.floats.get(index, 0) + 1
                                self._rebuild()
                                changed = True
                                break
            found = {}
            for page, top, bottom, kind, index, level in scan:
                if kind in ('heading', 'figure'):
                    found[(kind[0], index)] = page + 1
            if not changed and found == pages:
                return doc, headings, scan, pages
            pages = found
        return doc, headings, scan, pages

    def blank_spots(self, scan):
        """Pages (1-based) whose content ends early, other than the front matter and the last page."""
        last = {}
        for page, top, bottom, kind, index, level in scan:
            last[page] = max(last.get(page, 0), min(bottom, (page + 1) * self.H) - page * self.H)
        first_body = min(p for p, *_r in [s for s in scan if s[3] in ('heading', 'figure')])
        pages = sorted(last)
        return [(p + 1, 1 - last[p] / self.H) for p in pages
                if first_body <= p < pages[-1] and 1 - last[p] / self.H > GAP_LIMIT]

    def paint(self, doc, path):
        printer = self.printer
        printer.setOutputFileName(path)
        printer.setDocName('QuantumScope User Guide')
        printer.setFullPage(True)                                   # the cover runs to the paper's edges
        margins = printer.pageLayout().marginsPixels(printer.resolution())
        scale = printer.resolution() / 96.0
        total = int(doc.documentLayout().documentSize().height() // self.H) + 1
        painter = QPainter(printer)
        font = QFont(doc.defaultFont())
        font.setPixelSize(12)                                      # in document units: the painter is scaled
        for p in range(total):
            if p:
                printer.newPage()
            if p == 0:
                painter.save()
                painter.scale(printer.resolution() / 72.0, printer.resolution() / 72.0)
                draw_cover(painter, printer.pageLayout().fullRect(QPageLayout.Unit.Point))
                painter.restore()
                continue
            painter.save()
            painter.translate(margins.left(), margins.top())
            painter.scale(scale, scale)
            painter.translate(0, -p * self.H)
            doc.drawContents(painter, QRectF(0, p * self.H, self.W, self.H))
            painter.restore()
            if p:                                                  # no number on the cover
                painter.save()
                painter.translate(margins.left(), margins.top())
                painter.scale(scale, scale)
                painter.setFont(font)
                painter.setPen(Qt.GlobalColor.darkGray)
                painter.drawText(QRectF(0, self.H + 4, self.W, FOOTER - 4), Qt.AlignmentFlag.AlignCenter, str(p + 1))
                painter.restore()
        painter.end()
        return total


def draw_cover(painter, page):
    """The cover, in points on the full page: a double-slit pattern built from single detections (the
    most characteristic picture in quantum physics, as QuantumScope's detector screen shows it), the
    title, the version, and the author."""
    import datetime
    import math
    import numpy as np
    from PySide6.QtCore import QPointF
    from PySide6.QtGui import QColor, QFontDatabase
    from PySide6.QtSvg import QSvgRenderer
    from quantumscope import __version__
    w, h = page.width(), page.height()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.fillRect(QRectF(0, 0, w, h), QColor(NAVY))
    band = h * 0.47                                              # the pattern's height
    # Intensity of two slits: cos² fringes under the single-slit sinc² envelope (x in units of the
    # screen), sampled point by point; each dot is one detected particle.
    rng = np.random.default_rng(1803)                            # Young's double-slit experiment, 1803

    def intensity(x):
        u = (x - 0.5) * 2.0
        envelope = np.sinc(1.6 * u) ** 2
        return envelope * np.cos(math.pi * 7.5 * u) ** 2
    xs = rng.uniform(0, 1, 60000)
    keep = rng.uniform(0, 1, len(xs)) < intensity(xs)
    xs = xs[keep][:5200]
    ys = rng.beta(1.25, 1.0, len(xs))                            # thinning out towards the title
    painter.setPen(Qt.PenStyle.NoPen)
    for x, y in zip(xs, ys):
        fade = 0.25 + 0.75 * (1 - y)
        colour = QColor(CYAN)
        colour.setAlphaF(min(1.0, 0.10 + 0.40 * fade * rng.uniform(0.6, 1.0)))   # texture behind the drawing
        painter.setBrush(colour)
        r = 0.55 + 0.75 * rng.uniform()
        painter.drawEllipse(QPointF(x * w, 26 + y * (band - 40)), r, r)
    from PySide6.QtGui import QLinearGradient                     # the pattern fades into the page
    fade = QLinearGradient(0, band * 0.62, 0, band + 8)
    clear, solid = QColor(NAVY), QColor(NAVY)
    clear.setAlphaF(0.0)
    fade.setColorAt(0.0, clear)
    fade.setColorAt(1.0, solid)
    painter.fillRect(QRectF(0, band * 0.62, w, band * 0.38 + 8), fade)
    _draw_circuit(painter, QRectF(40, band * 0.22, w * 0.43, band * 0.56))
    _draw_bloch(painter, w * 0.735, band * 0.50, min(w, band) * 0.27)

    def font(family, size, bold=False):
        """A font `size` points high. The painter already works in points, so the size is given in its
        units (a point size would be scaled by the printer's resolution a second time)."""
        f = QFont(family if family in QFontDatabase.families() else 'DejaVu Sans')
        f.setPixelSize(max(1, round(size)))
        f.setBold(bold)
        return f

    def text(x, y, value, family, size, colour, bold=False):
        painter.setFont(font(family, size, bold))
        painter.setPen(QColor(colour))
        painter.drawText(QPointF(x, y), value)
    left = 64.0
    top = band + 12
    QSvgRenderer(MARK).render(painter, QRectF(left - 4, top, 58, 58))
    text(left, top + 118, 'QuantumScope', 'Inter Display', 46, MIST, bold=True)
    text(left, top + 156, 'User Guide', 'Inter Display', 24, CYAN)
    painter.setFont(font('Inter', 11))
    painter.setPen(QColor(MUTED))
    painter.drawText(QRectF(left, top + 172, w * 0.62, 48), int(Qt.TextFlag.TextWordWrap),
                     'An interactive studio for hydrogen orbitals, the experiments of quantum mechanics, '
                     'quantum circuits and quantum machine learning.')
    month = datetime.date.today().strftime('%B %Y')
    text(left, top + 236, f'Version {__version__}, {month}', 'Inter', 10.5, MIST)
    painter.setPen(QColor(PANEL))
    painter.drawLine(QPointF(left, h - 132), QPointF(w - left, h - 132))
    text(left, h - 100, AUTHOR, 'Inter', 13, MIST, bold=True)
    for k, line in enumerate(AUTHOR_LINES):
        text(left, h - 80 + 16 * k, line, 'Inter', 10, MUTED)
    painter.setFont(font('Inter', 10))
    painter.setPen(QColor(MUTED))
    right = QRectF(w / 2, h - 113, w / 2 - left, 54)
    painter.drawText(right, int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop),
                     f'{REPOSITORY}\nOpen source, MIT licence')


def _pen(colour, width, alpha=1.0, dashed=False):
    from PySide6.QtGui import QColor, QPen
    c = QColor(colour)
    c.setAlphaF(alpha)
    pen = QPen(c, width)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    if dashed:
        pen.setDashPattern([3, 3])
    return pen


def _draw_circuit(painter, box):
    """A three-qubit GHZ circuit (H, then two CNOTs, then measurements), in the cover's line style."""
    from PySide6.QtCore import QPointF
    from PySide6.QtGui import QColor, QFont, QPainterPath
    wires = [box.top() + box.height() * f for f in (0.2, 0.5, 0.8)]
    x0, x1 = box.left(), box.right()
    painter.setBrush(Qt.BrushStyle.NoBrush)
    label = QFont('Inter')
    label.setPixelSize(11)
    painter.setFont(label)
    for y in wires:                                               # the qubits' wires, starting in |0⟩
        painter.setPen(_pen(MUTED, 1.0, 0.9))
        painter.drawText(QPointF(x0, y + 4), '|0⟩')
        painter.setPen(_pen(MIST, 1.1, 0.75))
        painter.drawLine(QPointF(x0 + 26, y), QPointF(x1, y))
    size = 22.0
    gate = QFont('Inter')
    gate.setPixelSize(13)
    gate.setBold(True)

    def h_gate(x, y):
        painter.setPen(_pen(CYAN, 1.4))
        painter.setBrush(QColor(NAVY))
        painter.drawRoundedRect(QRectF(x - size / 2, y - size / 2, size, size), 3, 3)
        painter.setFont(gate)
        painter.setPen(_pen(CYAN, 1.0))
        painter.drawText(QRectF(x - size / 2, y - size / 2, size, size), int(Qt.AlignmentFlag.AlignCenter), 'H')

    def cnot(x, control, target):
        painter.setPen(_pen(CYAN, 1.4))
        painter.drawLine(QPointF(x, control), QPointF(x, target + (8 if target > control else -8)))
        painter.setBrush(QColor(CYAN))
        painter.drawEllipse(QPointF(x, control), 3.6, 3.6)
        painter.setBrush(QColor(NAVY))
        painter.drawEllipse(QPointF(x, target), 8, 8)
        painter.drawLine(QPointF(x - 8, target), QPointF(x + 8, target))
        painter.drawLine(QPointF(x, target - 8), QPointF(x, target + 8))

    def meter(x, y):
        painter.setPen(_pen(MIST, 1.2, 0.9))
        painter.setBrush(QColor(NAVY))
        painter.drawRoundedRect(QRectF(x - size / 2, y - size / 2, size, size), 3, 3)
        arc = QPainterPath()
        arc.arcMoveTo(QRectF(x - 7, y - 3, 14, 12), 180)
        arc.arcTo(QRectF(x - 7, y - 3, 14, 12), 180, -180)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(arc)
        painter.drawLine(QPointF(x, y + 3), QPointF(x + 5, y - 6))
    span = x1 - (x0 + 26)
    h_gate(x0 + 26 + span * 0.18, wires[0])
    cnot(x0 + 26 + span * 0.42, wires[0], wires[1])
    cnot(x0 + 26 + span * 0.62, wires[1], wires[2])
    for y in wires:
        meter(x0 + 26 + span * 0.88, y)


def _draw_bloch(painter, cx, cy, r):
    """A Bloch sphere in a true 3-D projection (the far halves of its circles dashed), with one state
    vector, the cover's single warm accent."""
    import math
    from PySide6.QtCore import QPointF
    from PySide6.QtGui import QColor, QFont, QPolygonF
    az, el = math.radians(35), math.radians(18)

    def project(x, y, z):
        """(screen point, depth): rotate about z by az, tilt by el; depth > 0 faces the reader."""
        x1, y1 = x * math.cos(az) - y * math.sin(az), x * math.sin(az) + y * math.cos(az)
        up = z * math.cos(el) - y1 * math.sin(el)
        depth = y1 * math.cos(el) + z * math.sin(el)
        return QPointF(cx + r * x1, cy - r * up), depth

    def circle(points, width, alpha):
        for k in range(len(points) - 1):
            (a, da), (b, db) = points[k], points[k + 1]
            back = (da + db) / 2 < 0
            painter.setPen(_pen(MIST, width, alpha * (0.45 if back else 1.0), dashed=back))
            painter.drawLine(a, b)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(_pen(MIST, 1.4, 0.85))
    painter.drawEllipse(QPointF(cx, cy), r, r)                    # the outline
    steps = [2 * math.pi * k / 120 for k in range(121)]
    circle([project(math.cos(t), math.sin(t), 0) for t in steps], 1.0, 0.7)   # equator
    circle([project(0, math.cos(t), math.sin(t)) for t in steps], 0.8, 0.45)  # a meridian
    for end in ((0, 0, 1), (0, 0, -1), (1, 0, 0), (0, 1, 0)):     # axes
        painter.setPen(_pen(MUTED, 0.8, 0.6, dashed=True))
        painter.drawLine(QPointF(cx, cy), project(*end)[0])
    label = QFont('Inter')
    label.setPixelSize(12)
    painter.setFont(label)
    painter.setPen(_pen(MIST, 1.0, 0.9))
    top, bottom = project(0, 0, 1)[0], project(0, 0, -1)[0]
    painter.drawText(QPointF(top.x() - 10, top.y() - 8), '|0⟩')
    painter.drawText(QPointF(bottom.x() - 10, bottom.y() + 18), '|1⟩')
    theta, phi = math.radians(50), -az + math.radians(12)        # the state vector, nearly in the page plane
    tip3 = (math.sin(theta) * math.cos(phi), math.sin(theta) * math.sin(phi), math.cos(theta))
    tip, _ = project(*tip3)
    foot, _ = project(tip3[0], tip3[1], 0)
    painter.setPen(_pen(ACCENT, 0.9, 0.7, dashed=True))           # its shadow on the equator plane
    painter.drawLine(QPointF(cx, cy), foot)
    painter.drawLine(foot, tip)
    painter.setPen(_pen(ACCENT, 2.6))
    painter.drawLine(QPointF(cx, cy), tip)
    dx, dy = tip.x() - cx, tip.y() - cy
    length = math.hypot(dx, dy) or 1.0
    ux, uy = dx / length, dy / length
    head = QPolygonF([tip, QPointF(tip.x() - 11 * ux + 5 * uy, tip.y() - 11 * uy - 5 * ux),
                      QPointF(tip.x() - 11 * ux - 5 * uy, tip.y() - 11 * uy + 5 * ux)])
    painter.setBrush(QColor(ACCENT))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawPolygon(head)
    painter.setBrush(QColor(MIST))
    painter.drawEllipse(QPointF(cx, cy), 2.4, 2.4)


def _fragments(block):
    it = block.begin()
    while not it.atEnd():
        yield it
        it += 1


def bookmarks_and_links(path, guide, doc, headings, scan, pages):
    """PDF outline (chapters with their sections) and clickable Contents / List of figures entries."""
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import ArrayObject, DictionaryObject, Fit, FloatObject, NameObject, NumberObject
    writer = PdfWriter(clone_from=PdfReader(path))
    writer.add_outline_item('Contents', guide.front_pages['Contents'], fit=Fit.fit())
    writer.add_outline_item('List of figures', guide.front_pages['List of figures'], fit=Fit.fit())
    parent = None
    for k, (level, text) in enumerate(headings):
        target = pages[('h', k)] - 1
        if level == 2:
            parent = writer.add_outline_item(text, target, fit=Fit.fit())
        else:
            writer.add_outline_item(text, target, parent=parent, fit=Fit.fit())
    # Links: each Contents / List of figures row points at its page.
    margin_pt = 18 / 25.4 * 72
    page_h_pt = float(writer.pages[0].mediabox.height)
    rows = _table_rows(doc)
    targets = [pages[('h', k)] - 1 for k in range(len(headings))] + [pages[('f', k)] - 1 for k in range(len(guide.figures))]
    for (page, top, bottom), target in zip(rows, targets):
        y0 = page_h_pt - margin_pt - (bottom - page * guide.H) * 0.75
        y1 = page_h_pt - margin_pt - (top - page * guide.H) * 0.75
        link = DictionaryObject({
            NameObject('/Type'): NameObject('/Annot'), NameObject('/Subtype'): NameObject('/Link'),
            NameObject('/Rect'): ArrayObject([FloatObject(v) for v in (margin_pt, y0, margin_pt + guide.W * 0.75, y1)]),
            NameObject('/Border'): ArrayObject([NumberObject(0), NumberObject(0), NumberObject(0)]),   # no box
            NameObject('/Dest'): ArrayObject([writer.pages[target].indirect_reference, NameObject('/Fit')])})
        holder = writer.pages[page]
        if '/Annots' not in holder:
            holder[NameObject('/Annots')] = ArrayObject()
        holder['/Annots'].append(writer._add_object(link))
    writer.page_mode = '/UseOutlines'                              # open with the bookmarks showing
    writer.add_metadata({'/Title': 'QuantumScope User Guide', '/Author': AUTHOR})
    with open(path, 'wb') as handle:
        writer.write(handle)


def _table_rows(doc):
    """(page, top, bottom) of each row of the Contents and List of figures tables, in order."""
    layout, rows = doc.documentLayout(), []
    frame_iter = doc.rootFrame().begin()
    tables = 0
    while not frame_iter.atEnd() and tables < 2:
        frame = frame_iter.currentFrame()
        if frame is not None and hasattr(frame, 'cellAt'):
            table = frame
            tables += 1
            for r in range(table.rows()):
                cell = table.cellAt(r, 0)
                rect = layout.blockBoundingRect(cell.firstCursorPosition().block())
                H = doc.pageSize().height()
                rows.append((int(rect.top() // H), rect.top(), rect.bottom()))
        frame_iter += 1
    return rows


def build(path):
    guide = Guide()
    doc, headings, scan, pages = guide.layout()
    total = guide.paint(doc, path)
    bookmarks_and_links(path, guide, doc, headings, scan, pages)
    gaps = guide.blank_spots(scan)
    return dict(pages=total, headings=len(headings), figures=len(guide.figures), shrunk=dict(guide.shrink),
                moved=sorted(guide.breaks), floated=dict(guide.floats), gaps=gaps)
