"""What the student has done in the Quantum annealing experiment, for lab checks (v0.9.2, no Qt).

The experiment records each anneal and each success-against-time curve here; listeners (the Learn
window) are told, so lab steps tick as soon as their condition is met.
"""
STATE = {'anneal': None, 'curve': None}
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


def annealed(problem, T, success, gap):
    STATE['anneal'] = dict(problem=problem, time=float(T), success=float(success), gap=float(gap))
    _changed()


def curve(problem, gap):
    STATE['curve'] = dict(problem=problem, gap=float(gap))
    _changed()


def reset():
    for key in STATE:
        STATE[key] = None
    _changed()


def _compare(value, rest):
    op, number = rest.split()[0], float(rest.split()[1])
    return {'>=': value >= number, '<=': value <= number, '>': value > number, '<': value < number}[op]


def check(rest):
    """(passed?, explanation) for an 'anneal …' lab condition:
        anneal problem maxcut-ring6    the last anneal was of this problem (a Problem key)
        anneal success >= 0.95         its probability of finding the answer (also time, gap; <=, <, >)
        anneal curve glass-8-0         success against T was computed for this problem
    """
    words = rest.split()
    if len(words) < 2:
        raise ValueError(f'Incomplete annealing check: {rest!r}')
    what = words[0]
    if what == 'curve':
        last = STATE['curve']
        return last is not None and last['problem'] == words[1], f'press Success against T for {words[1]}'
    last = STATE['anneal']
    if what == 'problem':
        return last is not None and last['problem'] == words[1], f'anneal the problem {words[1]}'
    if what in ('success', 'time', 'gap'):
        return last is not None and _compare(last[what], ' '.join(words[1:])), f'anneal so that {rest}'
    raise ValueError(f'Unknown annealing check: {what}')
