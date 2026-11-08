"""v0.9.0 (20a): the calculator's parser, its exact and digits evaluation, and its display."""
import numpy as np
import pytest

from quantumscope.calc import format as F
from quantumscope.calc.evaluate import Calculator
from quantumscope.calc.parser import CalcError, parse

sympy = pytest.importorskip('sympy')
S2 = 1 / np.sqrt(2)


def numeric(value):
    """Any result as a NumPy array (or complex number), for comparing the two modes."""
    if isinstance(value, sympy.MatrixBase):
        return np.array(value.evalf(), complex)
    if isinstance(value, np.ndarray):
        return value
    return complex(sympy.N(value)) if not isinstance(value, (int, float, complex)) else complex(value)


@pytest.mark.parametrize('text, expected', [
    ('H ⊗ I |00⟩', '*(⊗(H, I), |00⟩)'), ('2 X ⊗ Y', '*(2, ⊗(X, Y))'), ('⟨0|1⟩', '*(⟨0|, |1⟩)'),
    ('<0|X|1>', '*(*(⟨0|, X), |1⟩)'), ("A' + B†", '+(†(A), †(B))'), ('-X^2', '-(^(X, 2))'),
    ('(H (x) H)|01>', '*(⊗(H, H), |01⟩)'), ('A^†', '†(A)')])
def test_parsing_and_precedence(text, expected):
    def show(n):
        if n.kind == 'ket':
            return f'|{n.value}⟩'
        if n.kind == 'bra':
            return f'⟨{n.value}|'
        if n.kind in ('number', 'name'):
            return str(n.value)
        return f'{n.value}(' + ', '.join(show(a) for a in n.args) + ')'
    assert show(parse(text).expr) == expected


@pytest.mark.parametrize('text, where, words', [
    ('H|0', 1, 'closing ⟩'), ('(X', 2, "Expected ')'"), ('X +', 3, 'Expected a number'), ('⟨0', 0, 'closing bar'),
    ('3..2', 0, 'not a number'), ('$', 0, 'not something')])
def test_errors_say_what_and_where(text, where, words):
    with pytest.raises(CalcError) as error:
        parse(text)
    assert error.value.at == where and words in str(error.value)


EXPRESSIONS = ['H|0⟩', '⟨0|1⟩', '⟨+|-⟩', '<0|X|1>', 'CNOT (H ⊗ I)|00⟩', 'comm(X, Y)', 'acomm(X, Y)', 'X^2', 'H^-1',
               '(1+i)/2', 'T^2 - S', 'RX(pi)', 'exp(-i*pi/4*Z)', 'RY(pi/3)|0⟩', 'U(pi/2, 0, pi)', 'S|+⟩',
               '(X - i Y)/2', 'det(H)', 'tr(X Z)', 'inv([1, 2; 3, 4])', 'kron(X, Y, Z)', 'norm(|0⟩ + |1⟩)',
               'normalize(|0⟩ + i|1⟩)', '⟨+|Z|+⟩', 'SWAP |01⟩', 'CZ |++⟩', 'Id(4) - CNOT^2', 'X†', "Y'", '[[1, 2], [3, 4]]^3']


@pytest.mark.parametrize('text', EXPRESSIONS)
def test_exact_and_digits_agree(text):
    exact = numeric(Calculator('exact').evaluate(text).value)
    digits = numeric(Calculator('digits').evaluate(text).value)
    assert np.allclose(exact, digits, atol=1e-12)


def test_textbook_identities():
    c = Calculator('digits')
    assert np.allclose(c.evaluate('CNOT (H ⊗ I)|00⟩').value.ravel(), [S2, 0, 0, S2])          # Bell state
    assert np.allclose(c.evaluate('comm(X, Y)').value, 2j * np.diag([1, -1]))                # [X, Y] = 2iZ
    assert np.allclose(c.evaluate('H X H').value, np.diag([1, -1]))                           # HXH = Z
    assert np.allclose(c.evaluate('exp(-i*0.7/2*X)').value, c.evaluate('RX(0.7)').value)       # exp = RX
    assert c.evaluate('⟨+|-⟩').value == pytest.approx(0, abs=1e-15)
    e = Calculator('exact')
    assert sympy.simplify(e.evaluate('exp(-i θ X / 2)').value - e.evaluate('RX(θ)').value) == sympy.zeros(2)


def test_variables_names_and_modes():
    c = Calculator('digits')
    c.evaluate('ψ = H|0⟩')
    assert c.evaluate('⟨ψ|X|ψ⟩').value == pytest.approx(1)
    c.set_mode('exact')                                                                        # carried across
    assert c.evaluate('⟨ψ|X|ψ⟩').value == 1
    with pytest.raises(CalcError, match='built in'):
        c.evaluate('H = X')
    with pytest.raises(CalcError, match='no value'):
        Calculator('digits').evaluate('RX(θ)')
    for bad, words in (('X + 1', 'cannot be added'), ('X ⊗ 2', 'joins two'), ('H|01⟩', 'Cannot multiply a 2×2'),
                       ('X^0.5', 'whole number'), ('|abc⟩', 'not a known state'), ('foo(1)', 'not a known function'),
                       ('inv([1, 1; 1, 1])', 'no inverse'), ('X(1, 2)', 'not a function')):
        with pytest.raises(CalcError, match=words):
            Calculator('digits').evaluate(bad)


def test_steps_record_the_working():
    result = Calculator('exact').evaluate('CNOT (H ⊗ I)|00⟩')
    texts = [text for text, _ in result.steps]
    assert 'H ⊗ I' in texts and texts[-1] == 'CNOT (H ⊗ I)|00⟩'


@pytest.mark.parametrize('mode', ['exact', 'digits'])
def test_display(mode):
    c = Calculator(mode)
    show = lambda text: F.summary(c.evaluate(text).value, mode)                               # noqa: E731
    assert show('CNOT (H ⊗ I)|00⟩') == '(1/√2)|00⟩ + (1/√2)|11⟩'
    assert show('|-i⟩') == '(1/√2)|0⟩ - (i/√2)|1⟩'
    assert show('H ⊗ H |01⟩') == '(1/2)|00⟩ - (1/2)|01⟩ + (1/2)|10⟩ - (1/2)|11⟩'
    assert show('RX(pi)') == '[[0, -i], [-i, 0]]' and show('exp(i*pi/4)') == '1/√2 + i/√2'
    assert show('RY(pi/3)|0⟩') == '(√3/2)|0⟩ + (1/2)|1⟩' and show('⟨+|-⟩') == '0'
    assert F.kind(c.evaluate('⟨0|H').value) == 'bra' and F.kind(c.evaluate('H').value) == 'operator'


def test_symbolic_display():
    c = Calculator('exact')
    assert F.summary(c.evaluate('RY(θ)|0⟩').value, 'exact') == 'cos(θ/2)|0⟩ + sin(θ/2)|1⟩'
    assert F.summary(c.evaluate('e').value, 'exact') == 'e'
