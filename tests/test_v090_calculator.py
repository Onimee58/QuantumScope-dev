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


# ---- 20b: the quantum functions -------------------------------------------------------------------
BELL = 'CNOT (H ⊗ I)|00⟩'


def special_numbers(value):
    """A Special result as numbers, for comparing the modes."""
    if value.kind == 'eigen':
        return [(complex(numeric(v)), numeric(vec)) for v, vec in value.data]
    if value.kind == 'bloch':
        return [complex(numeric(x)) for x in value.data]
    return [(word, complex(numeric(c))) for word, c in value.data]


@pytest.mark.parametrize('text', ['eig(X)', 'eig(Y)', 'eig(H)', 'eig(Z ⊗ Z)', 'bloch(|i⟩)', 'bloch(RY(pi/3)|0⟩)',
                                  'pauli(CNOT)', 'pauli(SWAP)', 'pauli(H)'])
def test_special_results_agree_between_modes(text):
    a = special_numbers(Calculator('exact').evaluate(text).value)
    b = special_numbers(Calculator('digits').evaluate(text).value)
    assert len(a) == len(b)
    for x, y in zip(a, b):
        if isinstance(x, tuple):
            assert x[0] == y[0] or np.allclose(x[0], y[0])
            assert np.allclose(x[1], y[1], atol=1e-12)                       # the same vectors, same phase
        else:
            assert np.isclose(x, y)


@pytest.mark.parametrize('mode', ['exact', 'digits'])
def test_quantum_functions(mode):
    c = Calculator(mode)
    value = lambda text: numeric(c.evaluate(text).value)                     # noqa: E731
    assert np.allclose(value(f'ptrace({BELL}, 1)'), np.eye(2) / 2)        # each half of a Bell pair is mixed
    assert np.isclose(value(f'entropy(ptrace({BELL}, 0))'), 1)            # one bit of entanglement
    assert np.isclose(value(f'purity(ptrace({BELL}, 1))'), 0.5)
    assert np.isclose(value(f'expect(X ⊗ X, {BELL})'), 1) and np.isclose(value('expect(Z, |1⟩)'), -1)
    assert np.isclose(value('fidelity(|0⟩, |+⟩)'), 0.5) and np.isclose(value('fidelity(|0⟩, dm(|0⟩))'), 1)
    assert np.isclose(value('entropy(Id(2)/2)'), 1) and np.isclose(value('entropy(dm(|0⟩))'), 0)
    assert np.allclose(value('ptrace(|0⟩ ⊗ |+⟩, 0)'), np.full((2, 2), 0.5))  # q0 traced out: |+⟩⟨+| is left
    assert np.allclose(value('ptrace(|0⟩ ⊗ |+⟩, 1)'), np.diag([1, 0]))     # q1 traced out: |0⟩⟨0| is left
    bloch = c.evaluate('bloch(RY(pi/3)|0⟩)').value.data
    assert np.allclose([complex(numeric(x)) for x in bloch], [np.sqrt(3) / 2, 0, 0.5])
    assert F.summary(c.evaluate('pauli(CNOT)').value, mode) == '1/2 II + 1/2 IX + 1/2 ZI - 1/2 ZX'
    assert F.summary(c.evaluate('pauli(SWAP)').value, mode) == '1/2 II + 1/2 XX + 1/2 YY + 1/2 ZZ'
    assert F.summary(c.evaluate('eig(Y)').value, mode) == 'λ = -1:  (1/√2)|0⟩ - (i/√2)|1⟩; λ = 1:  (1/√2)|0⟩ + (i/√2)|1⟩'
    assert F.summary(c.evaluate('bloch(|i⟩)').value, mode) == '(0, 1, 0)'


def test_quantum_function_errors():
    c = Calculator('digits')
    for bad, words in (('ptrace(|0⟩, 0)', 'at least two'), ('ptrace(dm(|00⟩), 2)', 'must be 0 to 1'),
                       ('bloch(|00⟩)', 'one qubit'), ('eig([1, 2])', 'square'), ('eig(X) + 1', 'not computed with'),
                       ('pauli(Id(3))', 'power of 2'), ('expect(Z, |00⟩)', 'different sizes')):
        with pytest.raises(CalcError, match=words):
            c.evaluate(bad)
    with pytest.raises(CalcError, match='cannot be given a name'):
        c.evaluate('v = eig(X)')
    with pytest.raises(CalcError, match='digits mode only'):
        Calculator('exact').evaluate('fidelity(Id(2)/2, dm(|0⟩)/2 + dm(|1⟩)/2)')


# ---- 20d: the lessons' calculator links -----------------------------------------------------------
def test_every_math_lesson_has_a_working_calculator_link():
    import re
    from quantumscope.learn import actions
    from quantumscope.learn.lessons import builtin_lessons
    from quantumscope.learn.render import to_html
    lessons = [lesson for lesson in builtin_lessons() if lesson.area == 'math']
    assert len(lessons) == 12
    for lesson in lessons:
        links = re.findall(r'<a href="(qs:calc[^"]*)"', to_html(lesson, 'dark'))
        assert len(links) == 1, lesson.key                                   # rendered (no [ ] in its text)
        action = actions.parse(links[0].replace('&amp;', '&'))
        for mode in [action.params['mode']] if action.params.get('mode') else ['exact', 'digits']:
            Calculator(mode).evaluate(action.target)                         # evaluates without an error
    shift = actions.parse('qs:calc?expr=' + __import__('urllib.parse').parse.quote(
        '(expect(Z, RY(pi/3 + pi/2)|0⟩) - expect(Z, RY(pi/3 - pi/2)|0⟩))/2', safe=''))
    assert F.summary(Calculator('exact').evaluate(shift.target).value, 'exact') == '-√3/2'   # parameter shift


def test_calculator_links_are_checked_when_parsed():
    from quantumscope.learn import actions
    assert actions.parse('qs:calc?expr=H%7C0%E2%9F%A9').target == 'H|0⟩'
    assert actions.parse('qs:calc?expr=RX(%CE%B8)&mode=exact').params == {'mode': 'exact'}
    for bad in ('qs:calc', 'qs:calc?expr=H%7C0', 'qs:calc?expr=X&mode=fast'):
        with pytest.raises(ValueError):
            actions.parse(bad)
