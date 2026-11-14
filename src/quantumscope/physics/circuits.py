"""Small exact statevector simulator and intentionally restricted OpenQASM 2 reader.

Bit order: qubit zero is the most significant tensor factor, |q0 q1 ...>.
"""
from dataclasses import dataclass
import math
import re
import numpy as np

MAX_QUBITS = 10
SINGLE = ('H', 'X', 'Y', 'Z', 'S', 'T', 'SDG', 'TDG', 'SX', 'P', 'RX', 'RY', 'RZ', 'U')
DUAL = ('CX', 'CZ', 'SWAP', 'CP')
# Gates with an angle parameter (CP(λ) is the controlled phase, diag(1, 1, 1, e^{iλ})).
PARAMETERIZED = ('RX', 'RY', 'RZ', 'P', 'U', 'CP')
TRIPLE = ('CCX', 'CSWAP')
ALL = SINGLE + DUAL + TRIPLE

@dataclass(frozen=True)
class Gate:
    name: str
    targets: tuple[int, ...]
    angle: float = 0.0
    phi: float = 0.0
    lam: float = 0.0


def unitary(gate):
    name, a = gate.name, gate.angle
    if name == 'H': return np.array([[1, 1], [1, -1]], complex) / math.sqrt(2)
    if name == 'X': return np.array([[0, 1], [1, 0]], complex)
    if name == 'Y': return np.array([[0, -1j], [1j, 0]], complex)
    if name == 'Z': return np.diag([1, -1]).astype(complex)
    if name == 'S': return np.diag([1, 1j]).astype(complex)
    if name == 'T': return np.diag([1, np.exp(1j*math.pi/4)]).astype(complex)
    if name == 'SDG': return np.diag([1, -1j]).astype(complex)
    if name == 'TDG': return np.diag([1, np.exp(-1j*math.pi/4)]).astype(complex)
    if name == 'SX': return .5*np.array([[1+1j,1-1j],[1-1j,1+1j]],complex)
    if name == 'P': return np.diag([1,np.exp(1j*a)]).astype(complex)
    if name == 'U':
        c,s=math.cos(a/2),math.sin(a/2)
        return np.array([[c,-np.exp(1j*gate.lam)*s],[np.exp(1j*gate.phi)*s,np.exp(1j*(gate.phi+gate.lam))*c]],complex)
    if name == 'RX': return math.cos(a/2)*np.eye(2)-1j*math.sin(a/2)*unitary(Gate('X',(0,)))
    if name == 'RY': return math.cos(a/2)*np.eye(2)-1j*math.sin(a/2)*unitary(Gate('Y',(0,)))
    if name == 'RZ': return np.diag([np.exp(-1j*a/2),np.exp(1j*a/2)])
    raise ValueError('Unknown gate: ' + name)


_FIXED = {}                                                    # matrices of gates without parameters


def gate_matrix(gate):
    """The gate's matrix on its own targets (2×2, 4×4 or 8×8), targets[0] the most significant.
    Controlled gates: the first target(s) control. Fixed gates are built once and cached."""
    name = gate.name.upper()
    cached = _FIXED.get(name)
    if cached is not None:
        return cached
    if name in SINGLE:
        u = unitary(gate)
    elif name == 'CP':
        u = np.diag([1, 1, 1, np.exp(1j * gate.angle)]).astype(complex)
    elif name == 'CX':
        u = np.eye(4, dtype=complex)[[0, 1, 3, 2]]
    elif name == 'CZ':
        u = np.diag([1, 1, 1, -1]).astype(complex)
    elif name == 'SWAP':
        u = np.eye(4, dtype=complex)[[0, 2, 1, 3]]
    elif name == 'CCX':
        u = np.eye(8, dtype=complex)[[0, 1, 2, 3, 4, 5, 7, 6]]
    elif name == 'CSWAP':
        u = np.eye(8, dtype=complex)[[0, 1, 2, 3, 4, 6, 5, 7]]
    else:
        raise ValueError('Unsupported gate ' + name)
    if name not in PARAMETERIZED:
        u.setflags(write=False)
        _FIXED[name] = u
    return u


def apply_matrix(state, n, matrix, targets):
    """Apply a 2ᵏ×2ᵏ matrix to qubits `targets` of an n-qubit state: one tensor contraction over the
    target axes of the state viewed as a 2×2×…×2 array (qubit 0 is axis 0, the most significant)."""
    k = len(targets)
    psi = np.asarray(state, complex).reshape((2,) * n)
    out = np.tensordot(matrix.reshape((2,) * (2 * k)), psi, axes=(list(range(k, 2 * k)), list(targets)))
    return np.moveaxis(out, list(range(k)), list(targets)).reshape(-1)


_PERMUTATION = {'X': (1, 0), 'CX': (0, 1, 3, 2), 'SWAP': (0, 2, 1, 3),       # new local pattern → old one
                'CCX': (0, 1, 2, 3, 4, 5, 7, 6), 'CSWAP': (0, 1, 2, 3, 4, 6, 5, 7)}
_DIAGONAL = ('Z', 'S', 'T', 'SDG', 'TDG', 'P', 'RZ', 'CZ', 'CP')
_INDEX = {}                                                    # cached per (n, targets)


def _local_index(n, targets):
    """For every basis state, the value of its target bits (targets[0] the most significant)."""
    key = (n, targets)
    if key not in _INDEX:
        i = np.arange(1 << n)
        local = np.zeros(1 << n, np.int64)
        for q in targets:
            local = (local << 1) | ((i >> (n - 1 - q)) & 1)
        _INDEX[key] = local
    return _INDEX[key]


def _permutation(n, name, targets):
    """For each basis state, the index of the amplitude it receives, for a gate that only reorders
    basis states: the target bits are replaced by the gate's table entry, the other bits kept."""
    key = (n, name, targets)
    if key not in _INDEX:
        k = len(targets)
        source = np.array(_PERMUTATION[name])[_local_index(n, targets)]
        index = np.arange(1 << n)
        for pos, q in enumerate(targets):
            bit = 1 << (n - 1 - q)
            index = (index & ~bit) | (((source >> (k - 1 - pos)) & 1) * bit)
        _INDEX[key] = index
    return _INDEX[key]


def apply_gate(state, n, gate):
    name = gate.name.upper()
    ids = gate.targets
    if name not in ALL: raise ValueError('Unsupported gate ' + name)
    if len(ids) != (3 if name in TRIPLE else 2 if name in DUAL else 1) or len(set(ids)) != len(ids) or any(q < 0 or q >= n for q in ids):
        raise ValueError('Invalid target qubits')
    state = np.asarray(state, complex)
    ids = tuple(ids)
    if name in _PERMUTATION:                                       # X, CX, SWAP, CCX, CSWAP: reorder
        return state[_permutation(n, name, ids)]
    matrix = gate_matrix(gate if gate.name == name else Gate(name, ids, gate.angle, gate.phi, gate.lam))
    if name in _DIAGONAL:                                          # a phase per basis state
        return state * np.diagonal(matrix)[_local_index(n, ids)]
    if len(ids) == 1:                                              # a 2×2 butterfly on one qubit
        q = ids[0]
        view = state.reshape(1 << q, 2, 1 << (n - q - 1))
        out = np.empty_like(view)
        out[:, 0, :] = matrix[0, 0] * view[:, 0, :] + matrix[0, 1] * view[:, 1, :]
        out[:, 1, :] = matrix[1, 0] * view[:, 0, :] + matrix[1, 1] * view[:, 1, :]
        return out.reshape(-1)
    return apply_matrix(state, n, matrix, ids)


def zero(n):
    if not 1 <= n <= MAX_QUBITS: raise ValueError(f'Qubits must be 1–{MAX_QUBITS}')
    v=np.zeros(1<<n,complex); v[0]=1; return v


def evolution(n, gates, initial=None):
    """States after each gate, starting from |0…0⟩ or the given initial state."""
    if initial is None:
        start=zero(n)
    else:
        start=np.asarray(initial,dtype=complex)
        if start.shape!=(1<<n,):raise ValueError('Initial state has the wrong dimension')
    states=[start]
    for g in gates: states.append(apply_gate(states[-1],n,g))
    return states


def bloch(state,n,q):
    """Bloch coordinates of reduced qubit, including mixed local states."""
    axis = np.asarray(state).reshape((2,)*n)
    v=np.moveaxis(axis,q,0).reshape(2,-1)
    rho=v@v.conj().T
    return (float(2*rho[0,1].real),float(-2*rho[0,1].imag),float((rho[0,0]-rho[1,1]).real))


def distribution(state):
    return np.abs(state)**2


def sample(state,shots,seed=None):
    if not 1 <= shots <= 100000: raise ValueError('Shots out of range')
    return np.random.default_rng(seed).multinomial(shots,distribution(state))


def parse_qasm(text):
    """OpenQASM 2 subset: qreg + H/X/Y/Z/S/T, rotations, CX/CZ/SWAP, barriers.

    Reject measurements, custom gates, conditionals, multi-register circuits etc.
    rather than silently change semantics. Returns (n, gates); use
    parse_qasm_detailed for barrier positions and import notices.
    """
    n,gates,_,_=parse_qasm_detailed(text)
    return n,gates


def _qasm_angle(expr):
    from .expressions import parse_angle
    return parse_angle(expr)


def parse_qasm_detailed(text):
    """Like parse_qasm, but also returns (fences, notes).

    fences: sorted gate indices at which a barrier occurred (a barrier before
    gates[i] is recorded as i). Barriers have no unitary effect; QuantumScope
    uses them only as column separators and reports that in notes, so they
    are never dropped silently.
    """
    text=re.sub(r'//[^\n]*','',text)
    statements=[x.strip() for x in text.split(';') if x.strip()]
    n=None; gates=[]; reg=None; header=False; fences=[]; barriers=0
    for statement in statements:
        s=' '.join(statement.split())
        if re.fullmatch(r'OPENQASM\s+2\.0',s,re.I): header=True; continue
        if re.fullmatch(r'include\s+"qelib1\.inc"',s,re.I): continue
        m=re.fullmatch(r'qreg\s+(\w+)\[(\d+)\]',s,re.I)
        if m:
            if n is not None: raise ValueError('Only one quantum register supported')
            reg,n=m.group(1),int(m.group(2)); zero(n);continue
        if s.lower().startswith('barrier ') or s.lower()=='barrier':
            barriers+=1
            if not fences or fences[-1]!=len(gates):fences.append(len(gates))
            continue
        if not header or n is None: raise ValueError(f'Expected OPENQASM 2.0 and qreg before: {s}')
        pat=rf'({re.escape(reg)})\[(\d+)\]'
        m=re.fullmatch(r'(h|x|y|z|s|t|sdg|tdg|sx|cx|cz|swap|ccx|cswap)\s+(.+)',s,re.I)
        if m:
            name=m.group(1).upper()
            args=[a.strip() for a in m.group(2).split(',')]
            indexes=[]
            for arg in args:
                mq=re.fullmatch(pat,arg)
                if not mq:raise ValueError('Invalid QASM qubit operand: '+arg)
                indexes.append(int(mq.group(2)))
            g=Gate(name,tuple(indexes));apply_gate(zero(n),n,g);gates.append(g);continue
        m=re.fullmatch(r'(rx|ry|rz|p)\s*\(([^()]*)\)\s*'+pat,s,re.I)
        if m:
            try: angle=_qasm_angle(m.group(2))
            except ValueError as exc: raise ValueError('Invalid rotation angle: '+str(exc)) from exc
            g=Gate(m.group(1).upper(),(int(m.group(4)),),angle);apply_gate(zero(n),n,g);gates.append(g);continue
        m=re.fullmatch(r'(cp|cu1)\s*\(([^()]*)\)\s*'+pat+r'\s*,\s*'+pat,s,re.I)
        if m:
            try: angle=_qasm_angle(m.group(2))
            except ValueError as exc: raise ValueError('Invalid controlled-phase angle: '+str(exc)) from exc
            g=Gate('CP',(int(m.group(4)),int(m.group(6))),angle);apply_gate(zero(n),n,g);gates.append(g);continue
        m=re.fullmatch(r'(u3|u)\s*\(([^()]*)\)\s*'+pat,s,re.I)
        if m:
            exprs=[v.strip() for v in m.group(2).split(',')]
            if len(exprs)!=3:raise ValueError('U requires three angles')
            vals=[]
            for expr in exprs:
                try:val=_qasm_angle(expr)
                except ValueError as exc:raise ValueError('Invalid U angle: '+str(exc)) from exc
                vals.append(val)
            g=Gate('U',(int(m.group(4)),),*vals);gates.append(g);continue
        raise ValueError('Unsupported OpenQASM statement: '+s)
    if not header or n is None: raise ValueError('Missing OPENQASM 2.0 or qreg')
    fences=[f for f in fences if 0<f<len(gates)]
    notes=[]
    if barriers:
        notes.append(f'{barriers} barrier statement(s) were used only to separate circuit columns. '
                     'QuantumScope has no barrier operation, so barriers are not saved or exported.')
    return n,gates,fences,notes


def measurement_marginal(probabilities, n, measured, counts=None):
    """Marginalize q0-first computational-basis distributions to selected wires.

    Returns (theoretical probabilities, sampled counts or None). This does not
    collapse a state and is intended for terminal measurements only.
    """
    measured=tuple(sorted(measured))
    if not measured or len(set(measured))!=len(measured) or any(q<0 or q>=n for q in measured):
        raise ValueError('Choose distinct valid measured qubits')
    probs=np.asarray(probabilities,dtype=float)
    if probs.shape!=(1<<n,):raise ValueError('Invalid state probability vector length')
    if counts is not None:
        counts=np.asarray(counts)
        if counts.shape!=probs.shape:raise ValueError('Invalid counts vector length')
    marginal=np.zeros(1<<len(measured),dtype=float)
    sampled=np.zeros(1<<len(measured),dtype=int) if counts is not None else None
    for index,prob in enumerate(probs):
        outcome=0
        for q in measured:outcome=(outcome<<1)|((index>>(n-1-q))&1)
        marginal[outcome]+=prob
        if sampled is not None:sampled[outcome]+=int(counts[index])
    return marginal,sampled
