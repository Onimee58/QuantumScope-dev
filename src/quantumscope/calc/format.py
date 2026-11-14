"""Showing calculator results (v0.9.0): numbers, matrices, and states in Dirac notation.

Digits mode recognises common exact values (½, 1/√2, √3/2, i/√2, …) and hides rounding noise;
exact mode prints SymPy's results with √, i and π. Both give plain text for each entry, a one-line
summary, and, for states, the Dirac form such as (1/√2)|00⟩ + (1/√2)|11⟩.
"""
import math

import numpy as np

TINY = 1e-10
ROOTS = (1, 2, 3, 5, 6)                 # a/b·√k with small a, b
SUPERSCRIPTS = str.maketrans('0123456789-', '⁰¹²³⁴⁵⁶⁷⁸⁹⁻')


def _real(x):
    """A real number, as a recognised exact value if it is one (to 1e-10), else 4 significant digits."""
    if abs(x) < TINY:
        return '0'
    sign = '-' if x < 0 else ''
    a = abs(x)
    for root in ROOTS:
        for den in range(1, 13):
            num = a * den / math.sqrt(root)
            whole = round(num)
            if whole and abs(num - whole) < TINY * den and whole <= 24:
                g = math.gcd(whole, den)
                n, d = whole // g, den // g
                if root == 1:
                    text = f'{n}' if d == 1 else f'{n}/{d}'
                else:
                    r = f'√{root}'
                    if n == d:
                        text = r
                    elif d == 1:
                        text = f'{n}{r}'
                    else:
                        text = f'{"" if n == 1 else n}{r}/{d}'
                        # a/√k reads better for 1/√2: √2/2 → 1/√2
                        if root in (2, 3) and n == 1 and d == root:
                            text = f'1/{r}'
                return sign + text
    if abs(x - math.pi) < TINY:
        return sign + 'π'
    return f'{x:.4g}'


def number_text(z, mode='digits'):
    """One number as text."""
    if mode == 'exact':
        return _exact(z)
    z = complex(z)
    re, im = z.real, z.imag
    if abs(im) < TINY:
        return _real(re)
    imag = _imaginary(_real(abs(im)))
    if abs(re) < TINY:
        return ('-' if im < 0 else '') + imag
    return f'{_real(re)} {"-" if im < 0 else "+"} {imag}'


def _imaginary(text):
    """'1/√2' → 'i/√2', '√3/2' → 'i√3/2', '2' → '2i', '0.3' → '0.3i'."""
    if text == '1':
        return 'i'
    if text.startswith('1/'):
        return 'i' + text[1:]
    if text.startswith('√'):
        return 'i' + text
    if '/' in text:
        return f'i·{text}'
    return f'{text}i'


def _recognized(text):
    """Whether _real/number_text produced an exact form (no decimal approximation)."""
    return not any(ch == '.' or ch == 'e' for ch in text.replace('e^', ''))


def _exact(e):
    import sympy
    e = sympy.simplify(e)
    if not e.free_symbols:                                     # a constant: the same forms as digits mode
        try:
            text = number_text(complex(e.evalf(30)), 'digits')
            if _recognized(text):
                return text
        except (TypeError, ValueError):
            pass
    text = sympy.sstr(e)
    for old, new in (('**', '^'), ('sqrt(', '√('), ('*I', 'i'), ('I*', 'i·'), ('pi', 'π'), ('exp(', 'e^('), ('*', '·')):
        text = text.replace(old, new)
    text = text.replace('√(2)', '√2').replace('√(3)', '√3').replace('√(5)', '√5').replace('√(6)', '√6')
    if text == 'I':
        return 'i'
    text = ''.join('e' if ch == 'E' and (k == 0 or not text[k - 1].isalpha()) and (k + 1 == len(text) or not text[k + 1].isalpha())
                   else ch for k, ch in enumerate(text))             # Euler's number
    return text.replace(' I', ' i').replace('(I', '(i').replace('-I', '-i')


def entries(value, mode):
    """The entries of a matrix as text, row by row."""
    if mode == 'exact':
        return [[number_text(value[r, c], mode) for c in range(value.cols)] for r in range(value.rows)]
    return [[number_text(value[r, c], mode) for c in range(value.shape[1])] for r in range(value.shape[0])]


def shape(value):
    if hasattr(value, 'cols'):
        return value.rows, value.cols
    if isinstance(value, np.ndarray):
        return value.shape
    return None


def kind(value):
    """'number', 'ket', 'bra', 'operator' or 'matrix'."""
    size = shape(value)
    if size is None:
        return 'number'
    rows, cols = size
    power = lambda n: n >= 2 and n & (n - 1) == 0                                  # noqa: E731
    if cols == 1 and power(rows):
        return 'ket'
    if rows == 1 and power(cols):
        return 'bra'
    if rows == cols:
        return 'operator'
    return 'matrix'


def _top(text, chars):
    """Whether any of `chars` occurs in text outside brackets."""
    depth = 0
    for ch in text:
        depth += (ch == '(') - (ch == ')')
        if depth == 0 and ch in chars:
            return True
    return False


def dirac(value, mode):
    """A ket or bra in Dirac notation: amplitude|bits⟩ terms (None for other values)."""
    k = kind(value)
    if k not in ('ket', 'bra'):
        return None
    flat = [value[i, 0] if k == 'ket' else value[0, i] for i in range(max(shape(value)))]
    bits = int(math.log2(len(flat)))
    terms = []
    for index, amplitude in enumerate(flat):
        text = number_text(amplitude, mode)
        if text in ('0', '0.0'):
            continue
        label = format(index, f'0{bits}b')
        basis = f'|{label}⟩' if k == 'ket' else f'⟨{label}|'
        sign, body = ('-', text[1:]) if text.startswith('-') and not _top(text[1:], ' +-') else ('', text)
        if body == '1':
            coefficient = ''
        elif _top(body, ' +-/'):                                 # a sum or fraction: in brackets
            coefficient = f'({body})'
        else:
            coefficient = body                                  # a number, or cos(θ/2) as it is
        terms.append(f'{sign}{coefficient}{basis}')
    if not terms:
        return '0'
    out = terms[0]
    for term in terms[1:]:
        out += f' - {term[1:]}' if term.startswith('-') else f' + {term}'      # a − b, not a + (−b)
    return out


def special_lines(value, mode):
    """An eigensystem, Bloch vector or Pauli decomposition, as lines of text."""
    if value.kind == 'bloch':
        return ['(' + ', '.join(number_text(x, mode) for x in value.data) + ')']
    if value.kind == 'pauli':
        out = ''
        for k, (word, c) in enumerate(value.data):
            text = number_text(c, mode)
            sign, body = ('-', text[1:]) if text.startswith('-') and not _top(text[1:], ' +-') else ('+', text)
            body = '' if body == '1' else f'({body}) ' if _top(body, ' +-') else f'{body} '
            out += (('-' if sign == '-' else '') if k == 0 else f' {sign} ') + f'{body}{word}'
        return [out or '0']
    lines = []
    for eigenvalue, vector in value.data:                       # eigensystem
        state = dirac(vector, mode) if vector is not None and kind(vector) == 'ket' else (
            '[' + ', '.join(row[0] for row in entries(vector, mode)) + ']' if vector is not None else '')
        lines.append(f'λ = {number_text(eigenvalue, mode)}' + (f':  {state}' if state else ''))
    return lines


def summary(value, mode):
    """One line: the number, the Dirac form of a state, or the matrix's size."""
    if type(value).__name__ == 'Special':
        return '; '.join(special_lines(value, mode))
    k = kind(value)
    if k == 'number':
        return number_text(value, mode)
    if k in ('ket', 'bra'):
        return dirac(value, mode)
    rows, cols = shape(value)
    rows_text = ['[' + ', '.join(row) + ']' for row in entries(value, mode)]
    if rows * cols <= 16:
        return '[' + ', '.join(rows_text) + ']'
    return f'{rows}×{cols} {"operator" if k == "operator" else "matrix"}'
