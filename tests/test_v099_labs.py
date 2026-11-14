"""v0.9.9: labs for Quantum Principles, Hydrogen and Mathematics, checked from what the student does.

Each lab is solved here the way the lab describes, with the same events the experiments record (or the
same calculator inputs), and every step must tick — and none before the student has done anything."""
import math

import pytest

from quantumscope.calc.evaluate import Calculator
from quantumscope.editor.circuit_model import CircuitModel
from quantumscope.learn import labs, progress
from quantumscope.learn.lessons import builtin_lessons
from quantumscope.learn.render import steps_of
from quantumscope.physics.circuits import Gate

LESSONS = {l.key: l for l in builtin_lessons()}


def calc(*inputs, mode='digits'):
    calculator = Calculator(mode)
    for text in inputs:
        progress.record_calc(text, calculator.evaluate(text).value, mode)


def orbital(n, l, m=0, basis='complex', view='cloud', enclosed=90):
    progress.record('orbital', n=n, l=l, m=m, basis=basis, view=view, enclosed=enclosed, compare=0)


def spin(theta, phi, axis, copies=500):
    """Measure fresh copies as the Superposition experiment does (exact Born-rule fraction, rounded)."""
    up = (1 + math.cos(math.radians(theta)) * math.cos(math.radians(axis))
          + math.sin(math.radians(theta)) * math.cos(math.radians(phi)) * math.sin(math.radians(axis))) / 2
    progress.record('superposition', theta=theta, phi=phi, axis=axis, copies=copies, up=round(up * copies) / copies,
                    expected=up)


def slit(**changes):
    fields = dict(wavelength=500, width=20, separation=100, distance=1, whichpath=0, particles=3000)
    fields.update(changes)
    progress.record('slit', **fields)


def beat(pair, p=0.5):
    first, second = pair.split('+')
    progress.record('beat', pair=pair, a=first, b=second, p=p, period=0.4, view='2d')


def circuit(n, *gates, noise=None):
    m = CircuitModel(n)
    m.set_circuit(n, [Gate(name, qubits, *angle) for name, qubits, *angle in gates])
    if noise:
        m.place_noise(noise, 1, m.columns - 1, 0.1)
    return m


SOLUTIONS = {
    'principles/90-lab-bloch-sphere': lambda: (spin(90, 0, 0), spin(90, 0, 90), spin(60, 0, 0), spin(60, 0, 60)),
    'principles/91-lab-interference': lambda: (slit(), slit(separation=200), slit(width=10), slit(whichpath=1)),
    'principles/92-lab-bell-test': lambda: (
        progress.record('pairs', state='psi-', clean=1.0, alice=0.0, bob=0.0, E=-1.0, n=500),
        progress.record('bell', state='psi-', clean=1.0, S=2.83, error=0.06),
        progress.record('bell', state='psi-', clean=0.6, S=1.70, error=0.08),
        progress.record('bell', state='classical', clean=1.0, S=1.41, error=0.07)),
    'hydrogen/90-lab-orbital-tour': lambda: (orbital(1, 0), orbital(2, 1, 1), orbital(2, 1, 1, basis='cosine'),
                                             orbital(3, 2, view='real'), orbital(4, 0, view='real')),
    'hydrogen/91-lab-where-is-the-electron': lambda: (orbital(1, 0, view='enclosure', enclosed=50),
                                                      orbital(1, 0, view='enclosure', enclosed=99),
                                                      orbital(2, 0), orbital(2, 1)),
    'hydrogen/92-lab-quantum-beats': lambda: (beat('1s+2p'), beat('1s+3d'), beat('2s+2p'), beat('1s+2p', 0.9)),
    'hydrogen/93-lab-predict-a-spectral-line': lambda: (orbital(2, 0), orbital(4, 0), orbital(1, 0),
                                                        calc('1239.84/(3.3996 - 0.8499)', '1239.84/3.3996',
                                                             '1239.84/(13.598 - 3.3996)')),
    'math/90-lab-complex-numbers': lambda: calc('(1+2i)(3-i)', 'abs((1+i)/2)^2', 'exp(i*pi)',
                                                'abs(1/2 + exp(i*pi)/2)^2', 'abs(1/2 + exp(i*pi/2)/2)^2'),
    'math/91-lab-states-and-gates': lambda: calc('normalize((1+i)|0> + |1>)', 'abs(⟨+|normalize((1+i)|0⟩ + |1⟩))^2',
                                                 'X*Z', 'Z*X', 'H Z H'),
    'math/92-lab-unitary-and-eigen': lambda: calc('U = [1, i; i, 1]/sqrt(2)', 'U† U', 'U*U', 'eig(Z + X)',
                                                  '(Z+X)*[1+sqrt(2); 1]'),
    'math/93-lab-tensor-products': lambda: calc('|+⟩ ⊗ |0⟩', 'CNOT (H ⊗ I)|00⟩', 'purity(ptrace(CNOT (H ⊗ I)|00⟩, 1))',
                                                'purity(ptrace(|+> ⊗ |0>, 1))'),
    'math/94-lab-pauli-and-rotations': lambda: calc('X*Y', 'commutator(X, Z)', 'exp(-i*(pi/2)*X/2)|0⟩', 'RX(pi)'),
    'math/95-lab-parameter-shift': lambda: calc(
        'expect(Z, RY(pi/3)|0⟩)', '(expect(Z, RY(pi/3 + pi/2)|0⟩) - expect(Z, RY(pi/3 - pi/2)|0⟩))/2', '-sin(pi/3)',
        '(expect(Z, RY(pi + pi/2)|0⟩) - expect(Z, RY(pi - pi/2)|0⟩))/2'),
}
CIRCUIT_LABS = {
    'principles/93-lab-hidden-phase': lambda: circuit(1, ('H', (0,)), ('RZ', (0,), math.pi), ('H', (0,))),
    'principles/94-lab-pure-mixed-entangled': lambda: circuit(2, ('H', (0,)), ('H', (1,)), ('CZ', (0, 1))),
}
SOLVED = set(SOLUTIONS) | set(CIRCUIT_LABS)


@pytest.fixture(autouse=True)
def fresh():
    progress.reset()
    yield
    progress.reset()


def test_fifteen_new_labs_in_the_three_areas_that_had_none():
    new = {k for k, l in LESSONS.items() if l.kind == 'lab' and l.area in ('principles', 'hydrogen', 'math')}
    assert new == SOLVED and len(new) == 15
    for key in new:
        assert LESSONS[key].body.count('```quiz') >= 1 and len(steps_of(LESSONS[key].body)) >= 3


@pytest.mark.parametrize('key', sorted(SOLUTIONS))
def test_doing_the_lab_ticks_every_step(key):
    steps = steps_of(LESSONS[key].body)
    model = CircuitModel(1)
    assert not any(labs.progress(model, steps).values())
    SOLUTIONS[key]()
    done = labs.progress(model, steps)
    assert all(done.values()), {i: labs.step_done(model, s) for i, s in enumerate(steps)}


@pytest.mark.parametrize('key', sorted(SOLUTIONS))
def test_each_step_needs_its_own_action(key):
    """Doing only the first step does not tick the last one: the checks are specific."""
    steps = steps_of(LESSONS[key].body)
    model = CircuitModel(1)
    assert not labs.step_done(model, steps[-1])[0]


@pytest.mark.parametrize('key', sorted(CIRCUIT_LABS))
def test_circuit_labs_complete(key):
    steps = steps_of(LESSONS[key].body)
    assert all(labs.progress(CIRCUIT_LABS[key](), steps).values())


def test_circuit_lab_middle_steps():
    steps = steps_of(LESSONS['principles/94-lab-pure-mixed-entangled'].body)
    noisy = circuit(2, ('H', (0,)), ('CX', (0, 1)), noise='depolarizing')
    assert labs.step_done(noisy, steps[1])[0] and not labs.step_done(circuit(2, ('H', (0,)), ('CX', (0, 1))), steps[1])[0]
    hidden = steps_of(LESSONS['principles/93-lab-hidden-phase'].body)
    assert labs.step_done(circuit(1, ('H', (0,)), ('T', (0,)), ('H', (0,))), hidden[2])[0]


def test_wrong_answers_do_not_tick():
    steps = steps_of(LESSONS['hydrogen/93-lab-predict-a-spectral-line'].body)
    calc('1239.84/(3.3996 + 0.8499)')                                  # a sign error: 291.7 nm
    assert not labs.step_done(CircuitModel(1), steps[1])[0]
    spin(60, 0, 0, copies=500)
    progress.record('superposition', theta=60, phi=0, axis=0, copies=500, up=0.6, expected=0.75)
    bloch = steps_of(LESSONS['principles/90-lab-bloch-sphere'].body)
    assert labs.step_done(CircuitModel(1), bloch[2])[0]               # one good run is enough …
    progress.reset()
    progress.record('superposition', theta=60, phi=0, axis=0, copies=500, up=0.6, expected=0.75)
    assert not labs.step_done(CircuitModel(1), bloch[2])[0]           # … but 0.6 is not 0.75 ± 0.06


def test_conditions_and_calculator_checks():
    progress.record('orbital', n=3, l=2, m=0, basis='cosine', view='real', enclosed=90, compare=0)
    assert progress.did('orbital n=3 l>=1 basis=COSINE view~rea')[0]
    assert not progress.did('orbital n=3 l>2')[0] and progress.did('orbital enclosed=91±1')[0]
    assert not progress.did('slit whichpath=1')[0]
    with pytest.raises(ValueError):
        progress.did('orbital n:3')
    calc('H Z H', mode='exact')                                       # exact (SymPy) results count too
    assert progress.calc('gives X')[0] and progress.calc('typed H*Z*H')[0] and not progress.calc('gives Z')[0]
    calc('1239.84/3.3996')
    assert progress.calc('gives 364.71±0.3')[0] and not progress.calc('gives 364.71')[0]
    with pytest.raises(ValueError):
        progress.calc('equals 3')


def test_listeners_hear_every_event():
    heard = []
    progress.listen(lambda: heard.append(1))
    progress.record('beat', pair='1s+2p')
    assert heard
