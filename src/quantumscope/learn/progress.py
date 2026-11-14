"""What the student has done outside the circuit editor, for lab checks (v0.9.9, no Qt).

The experiments record what the student does — an orbital drawn, copies of a spin measured, particles
fired at the slits, a Bell test, a superposition played, a calculator result — and the Learn window
is told, so lab steps tick at once. Every event is kept (the latest 200 of each kind), so a step stays
done after the student moves on to the next one.

Lab conditions (see learn/labs.py):

    did orbital n=3 l=2                  some orbital drawn matched every condition
    did superposition axis=90 up>=0.95   conditions: key=value, key>=value, key<=value, key>, key<,
    did slit separation=200 whichpath=1      key!=value, key~text (contains) and key=value±tolerance
    did bell state=psi- S>=2.2
    did beat pair=1s+2p p=0.5
    calc gives exp(i*pi)                 the calculator gave a result equal to this expression's value
    calc gives 486.3±0.2                 … within a tolerance
    calc typed eig                       an input the calculator evaluated contained this text

Events and their fields:

    orbital        n, l, m, basis (complex, cosine, sine), view (cloud, enclosure, real, imag),
                   enclosed (percent), compare (0 or 1)
    superposition  theta, phi, axis (degrees), copies, up (fraction of +1 results), expected
    slit           wavelength (nm), width, separation (µm), distance (m), whichpath (0 or 1), particles
    bell           state (phi+, psi-, …, classical), clean (fraction), S (|S|), error
    pairs          state, clean, alice, bob (degrees), E, n
    beat           pair (such as 1s+2p, lower state first), a, b, p (probability of a), period (fs), view
    calc           text, mode
"""
import re

import numpy as np

LIMIT = 200
EVENTS = {}                    # kind → [dict, …], oldest first
CALC_VALUES = []               # (text, numeric value) of the calculator's results, oldest first
_listeners = []


def listen(callback):
    if callback not in _listeners:
        _listeners.append(callback)


def _changed():
    for callback in list(_listeners):
        try:
            callback()
        except RuntimeError:                       # a deleted Qt object: forget it
            _listeners.remove(callback)


def record(kind, **fields):
    EVENTS.setdefault(kind, []).append(fields)
    del EVENTS[kind][:-LIMIT]
    _changed()


def record_calc(text, value, mode='digits'):
    """A calculator result. Exact (SymPy) results are kept as numbers too, so either mode can be checked."""
    number = numeric(value)
    if number is not None:
        CALC_VALUES.append((text, number))
        del CALC_VALUES[:-LIMIT]
    record('calc', text=text, mode=mode)


def reset():
    EVENTS.clear()
    CALC_VALUES.clear()
    _changed()


def numeric(value):
    """A complex number or a complex array for a calculator value; None for eigensystems and the like."""
    if getattr(value, 'kind', None) in ('eigen', 'bloch', 'pauli') and hasattr(value, 'data'):
        return None
    try:
        if hasattr(value, 'evalf') and hasattr(value, 'shape'):                   # a SymPy matrix
            return np.array(value.evalf(), dtype=complex)
        if isinstance(value, np.ndarray):
            return value.astype(complex)
        return complex(value.evalf() if hasattr(value, 'evalf') else value)
    except (TypeError, ValueError):
        return None


# ---- checking ------------------------------------------------------------------------------------------
_CONDITION = re.compile(r'^([A-Za-z_]+)(>=|<=|!=|=|>|<|~)(.+)$')


def _number(text):
    try:
        return float(text)
    except ValueError:
        return None


def _matches(event, condition):
    m = _CONDITION.match(condition)
    if not m:
        raise ValueError(f'Unreadable condition: {condition!r}')
    key, op, wanted = m.groups()
    if key not in event:
        return False
    have = event[key]
    if op == '~':
        return wanted.lower() in str(have).lower()
    tolerance = None
    if '±' in wanted:
        wanted, tol = wanted.split('±', 1)
        tolerance = float(tol)
    target, value = _number(wanted), _number(str(have))
    if target is None or value is None:                 # text: equal or not, ignoring case
        same = str(have).lower() == wanted.lower()
        return same if op == '=' else (not same) if op == '!=' else False
    close = abs(value - target) <= (tolerance if tolerance is not None else 1e-6 * max(1.0, abs(target)))
    return {'=': close, '!=': not close, '>=': value >= target or close, '<=': value <= target or close,
            '>': value > target and not close, '<': value < target and not close}[op]


def did(rest):
    """(passed?, explanation) for a 'did KIND condition …' lab check."""
    words = rest.split()
    if not words:
        raise ValueError('Incomplete check: did')
    kind, conditions = words[0], words[1:]
    for condition in conditions:                                                 # reject unreadable ones early
        if not _CONDITION.match(condition):
            raise ValueError(f'Unreadable condition: {condition!r}')
    passed = any(all(_matches(event, c) for c in conditions) for event in EVENTS.get(kind, []))
    return passed, f'{kind}: ' + (', '.join(conditions) if conditions else 'try it')


def calc(rest):
    """(passed?, explanation) for a 'calc gives EXPRESSION' or 'calc typed TEXT' lab check."""
    what, _, argument = rest.strip().partition(' ')
    argument = argument.strip()
    if what == 'typed':
        def squeeze(text):                    # spaces, * and ASCII brackets do not matter: H Z H, H*Z*H; |0>, |0⟩
            return re.sub(r'[\s*]+', '', text).replace('>', '⟩').replace('<', '⟨').lower()
        return (any(squeeze(argument) in squeeze(e['text']) for e in EVENTS.get('calc', [])),
                f'evaluate an expression with {argument}')
    if what == 'gives':                                  # 'calc gives 486.3±0.2' allows a tolerance
        from quantumscope.calc.evaluate import Calculator
        expression, _, tolerance = argument.partition('±')
        target = numeric(Calculator('digits').evaluate(expression.strip()).value)
        tol = float(tolerance) if tolerance else 1e-6
        for _, value in CALC_VALUES:
            if np.shape(value) == np.shape(target) and np.allclose(value, target, atol=tol, rtol=0):
                return True, ''
        return False, f'get the result {expression.strip()}'
    raise ValueError(f'Unknown calculator check: {what}')
