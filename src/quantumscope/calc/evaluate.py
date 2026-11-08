"""Evaluating calculator expressions exactly (SymPy) or in digits (NumPy), from one tree (v0.9.0).

Both backends implement the same small set of operations, so an expression means the same in both
modes; tests compare them. A 1 × 1 result (such as ⟨0|1⟩) is a plain number. In exact mode a name
with no value (θ, φ, t, …) is a real symbol, so exp(-i θ X / 2) gives the rotation matrix in θ.
"""
import cmath
import math
from dataclasses import dataclass, field

import numpy as np

from quantumscope.calc.parser import CalcError, Node, parse

MAX_DIMENSION = 64                      # 6 qubits; exact mode is slower, see EXACT_LIMIT
EXACT_LIMIT = 16                        # exact eigen-decompositions and exponentials: up to 4 qubits

SINGLE_STATES = {'0', '1', '+', '-', 'i', '+i', '-i', 'r', 'l'}


# ---- the two backends ---------------------------------------------------------------------------
class Numeric:
    name = 'digits'

    def number(self, text):
        return float(text) if any(c in text for c in '.eE') else int(text)

    def constant(self, name):
        return {'i': 1j, 'pi': math.pi, 'π': math.pi, 'e': math.e}.get(name)

    def symbol(self, name):
        raise CalcError(f'{name} has no value. Give it one first ({name} = 0.3), or switch to exact '
                        f'mode, where names without values stay as symbols')

    def matrix(self, rows):
        return np.array(rows, complex)

    def is_matrix(self, v):
        return isinstance(v, np.ndarray)

    def shape(self, v):
        return v.shape

    def simplify(self, v):
        return v

    def sqrt(self, x):
        return cmath.sqrt(x) if not isinstance(x, (int, float)) or x < 0 else math.sqrt(x)

    def scalar_function(self, name, x):
        f = {'exp': cmath.exp, 'sin': cmath.sin, 'cos': cmath.cos, 'tan': cmath.tan, 'log': cmath.log,
             'conj': lambda z: complex(z).conjugate(), 're': lambda z: complex(z).real,
             'im': lambda z: complex(z).imag, 'abs': abs, 'sqrt': self.sqrt}[name]
        value = f(x)
        if isinstance(value, complex) and abs(value.imag) < 1e-15:
            value = value.real
        return value

    def matmul(self, a, b):
        return a @ b

    def kron(self, a, b):
        return np.kron(a, b)

    def dagger(self, a):
        return a.conj().T if self.is_matrix(a) else complex(a).conjugate()

    def transpose(self, a):
        return a.T

    def identity(self, n):
        return np.eye(n, dtype=complex)

    def expm(self, a):
        from scipy.linalg import expm
        return expm(a)

    def power(self, a, n):
        return np.linalg.matrix_power(a, n)

    def trace(self, a):
        return complex(np.trace(a))

    def det(self, a):
        return complex(np.linalg.det(a))

    def inverse(self, a):
        if abs(np.linalg.det(a)) < 1e-12:
            raise CalcError('This matrix has no inverse (its determinant is 0)')
        return np.linalg.inv(a)

    def norm(self, a):
        return float(np.linalg.norm(a))

    def entries(self, a):
        return [[a[r, c] for c in range(a.shape[1])] for r in range(a.shape[0])]


class Exact:
    name = 'exact'

    def __init__(self):
        import sympy
        self.sp = sympy

    def number(self, text):
        return self.sp.Rational(text) if any(c in text for c in '.eE') else self.sp.Integer(text)

    def constant(self, name):
        sp = self.sp
        return {'i': sp.I, 'pi': sp.pi, 'π': sp.pi, 'e': sp.E}.get(name)

    def symbol(self, name):
        return self.sp.Symbol(name, real=True)

    def matrix(self, rows):
        return self.sp.Matrix(rows)

    def is_matrix(self, v):
        return isinstance(v, self.sp.MatrixBase)

    def shape(self, v):
        return v.shape

    def simplify(self, v):
        sp = self.sp
        if self.is_matrix(v):
            return v.applyfunc(lambda e: sp.simplify(e))
        return sp.simplify(v)

    def sqrt(self, x):
        return self.sp.sqrt(x)

    def scalar_function(self, name, x):
        sp = self.sp
        return {'exp': sp.exp, 'sin': sp.sin, 'cos': sp.cos, 'tan': sp.tan, 'log': sp.log,
                'conj': sp.conjugate, 're': sp.re, 'im': sp.im, 'abs': sp.Abs, 'sqrt': sp.sqrt}[name](x)

    def matmul(self, a, b):
        return a * b

    def kron(self, a, b):
        sp = self.sp
        rows = []
        for r in range(a.rows):
            for rr in range(b.rows):
                rows.append([a[r, c] * b[rr, cc] for c in range(a.cols) for cc in range(b.cols)])
        return sp.Matrix(rows)

    def dagger(self, a):
        return a.H if self.is_matrix(a) else self.sp.conjugate(a)

    def transpose(self, a):
        return a.T

    def identity(self, n):
        return self.sp.eye(n)

    def expm(self, a):
        if a.rows > EXACT_LIMIT:
            raise CalcError(f'Exact matrix exponentials are limited to {EXACT_LIMIT}×{EXACT_LIMIT}; use digits mode')
        return self.simplify(a.exp())

    def power(self, a, n):
        return a ** n

    def trace(self, a):
        return a.trace()

    def det(self, a):
        return a.det()

    def inverse(self, a):
        if self.sp.simplify(a.det()) == 0:
            raise CalcError('This matrix has no inverse (its determinant is 0)')
        return a.inv()

    def norm(self, a):
        return self.sp.sqrt(sum(self.sp.Abs(e) ** 2 for e in a))

    def entries(self, a):
        return [[a[r, c] for c in range(a.cols)] for r in range(a.rows)]


# ---- evaluation ---------------------------------------------------------------------------------
@dataclass
class Result:
    value: object                       # a number, or a matrix of the backend
    mode: str
    steps: list = field(default_factory=list)   # (expression text, value) for each operation
    assigned: str = None


class Calculator:
    """Evaluates statements and keeps the named values (ψ = H|0⟩) of one session."""

    def __init__(self, mode='exact'):
        self.variables = {}
        self.set_mode(mode)

    def set_mode(self, mode):
        if mode not in ('exact', 'digits'):
            raise ValueError(mode)
        self.mode = mode
        self.backend = Exact() if mode == 'exact' else Numeric()
        self._library = None

    def evaluate(self, text):
        statement = parse(text)
        self.steps = []
        value = self._eval(statement.expr)
        if not isinstance(value, Special):
            value = self._scalar_if_1x1(self.backend.simplify(value))
        elif statement.assign:
            raise CalcError('An eigensystem, Bloch vector or Pauli decomposition cannot be given a name')
        if statement.assign:
            if statement.assign in ('i', 'pi', 'π', 'e') or statement.assign in self.library():
                raise CalcError(f'{statement.assign} is built in and cannot be changed; choose another name')
            self.variables[statement.assign] = (self.mode, value)
        return Result(value, self.mode, self.steps, statement.assign)

    # -- the building blocks -------------------------------------------------------------------
    def library(self):
        """Named gates in the current backend."""
        if self._library is None:
            b = self.backend
            h = 1 / b.sqrt(2)
            i = b.constant('i')
            m = b.matrix
            self._library = {
                'I': m([[1, 0], [0, 1]]), 'X': m([[0, 1], [1, 0]]), 'Y': m([[0, -i], [i, 0]]),
                'Z': m([[1, 0], [0, -1]]), 'H': m([[h, h], [h, -h]]), 'S': m([[1, 0], [0, i]]),
                'T': m([[1, 0], [0, (1 + i) * h]]),
                'CNOT': m([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]]),
                'CZ': m([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, -1]]),
                'SWAP': m([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]]),
            }
            self._library['CX'] = self._library['CNOT']
        return self._library

    def _single(self, label):
        b = self.backend
        h, i = 1 / b.sqrt(2), b.constant('i')
        return {'0': [[1], [0]], '1': [[0], [1]], '+': [[h], [h]], '-': [[h], [-h]],
                'i': [[h], [i * h]], '+i': [[h], [i * h]], 'r': [[h], [i * h]],
                '-i': [[h], [-i * h]], 'l': [[h], [-i * h]]}[label]

    def ket(self, label):
        """|label⟩: a basis or named single-qubit state, a string of them (|01⟩, |+-⟩), or a variable."""
        b = self.backend
        if label in self.variables:
            value = self._variable(label)
            if not (b.is_matrix(value) and b.shape(value)[1] == 1):
                raise CalcError(f'|{label}⟩ needs {label} to be a column vector (a ket)')
            return value
        if label in SINGLE_STATES:
            return b.matrix(self._single(label))
        if all(ch in '01+-' for ch in label):
            if len(label) > 6:
                raise CalcError('Kets are limited to 6 qubits here')
            value = b.matrix(self._single(label[0]))
            for ch in label[1:]:
                value = b.kron(value, b.matrix(self._single(ch)))
            return value
        raise CalcError(f'|{label}⟩ is not a known state: use 0, 1, +, -, i, -i (or strings such as 01), '
                        f'or a name you gave a value')

    def _variable(self, name):
        mode, value = self.variables[name]
        if mode != self.mode:                                  # convert between the modes
            value = self._convert(value, mode)
        return value

    def _convert(self, value, mode):
        """A value saved in the other mode, in the current one."""
        import sympy
        if mode == 'exact':                                    # exact → digits
            try:
                if isinstance(value, sympy.MatrixBase):
                    return np.array(value.evalf(), complex)
                return complex(value.evalf())
            except (TypeError, ValueError):
                raise CalcError('This value still has symbols in it; give them values first') from None
        if isinstance(value, np.ndarray):                      # digits → exact (nearest simple numbers)
            return sympy.Matrix(value.tolist()).applyfunc(lambda z: sympy.nsimplify(complex(z)))
        return sympy.nsimplify(value)

    def _scalar_if_1x1(self, v):
        b = self.backend
        if isinstance(v, Special):
            return v
        if b.is_matrix(v) and b.shape(v) == (1, 1):
            return b.entries(v)[0][0]
        return v

    def _check_size(self, v):
        b = self.backend
        if b.is_matrix(v) and max(b.shape(v)) > MAX_DIMENSION:
            raise CalcError(f'Results are limited to {MAX_DIMENSION}×{MAX_DIMENSION} (6 qubits)')
        return v

    def _step(self, node, value):
        if node.kind in ('binary', 'unary', 'postfix', 'call', 'matrix'):
            self.steps.append((node.text, self._scalar_if_1x1(value)))
        return value

    def _eval(self, node):
        b = self.backend
        kind = node.kind
        if kind == 'number':
            return b.number(node.value)
        if kind == 'name':
            name = node.value
            if name in self.variables:
                return self._variable(name)
            constant = b.constant(name)
            if constant is not None:
                return constant
            if name in self.library():
                return self.library()[name]
            return b.symbol(name)
        if kind == 'ket':
            return self.ket(node.value)
        if kind == 'bra':
            return b.dagger(self.ket(node.value))
        if kind == 'matrix':
            rows = [[self._eval(e) for e in row] for row in node.args]
            if any(b.is_matrix(e) for row in rows for e in row):
                raise CalcError('Matrix entries must be numbers')
            return self._step(node, b.matrix(rows))
        if kind == 'unary':
            inner = self._eval(node.args[0])
            if isinstance(inner, Special):
                raise CalcError('An eigensystem, Bloch vector or Pauli decomposition is shown, not computed with')
            return self._step(node, -inner)
        if kind == 'postfix':
            inner = self._eval(node.args[0])
            if isinstance(inner, Special):
                raise CalcError('An eigensystem, Bloch vector or Pauli decomposition is shown, not computed with')
            return self._step(node, b.dagger(inner))
        if kind == 'binary':
            values = [self._eval(a) for a in node.args]
            try:
                return self._step(node, self._check_size(self._binary(node.value, *values)))
            except CalcError as exc:
                tensored = [a for a in node.args if a.kind == 'binary' and a.value == '⊗']
                if node.value == '*' and tensored and 'Cannot multiply' in str(exc):
                    raise CalcError(f'{exc}. Note that ⊗ binds more tightly than side-by-side products, so '
                                    f'"{tensored[0].text}" was taken together; add brackets, such as '
                                    f'(RY(θ)|0⟩) ⊗ |1⟩') from None
                raise
        if kind == 'call':
            name = node.value
            if name in self.variables or name in self.library() or self.backend.constant(name) is not None:
                if len(node.args) != 1:                            # CNOT (H ⊗ I): a product, not a call
                    raise CalcError(f'{name} is not a function')
                product = Node('binary', '*', [Node('name', name, [], name), node.args[0]], node.text)
                return self._eval(product)
            return self._step(node, self._check_size(self._call(name, [self._eval(a) for a in node.args])))
        raise CalcError(f'Cannot evaluate {kind}')

    def _binary(self, op, a, c):
        b = self.backend
        if isinstance(a, Special) or isinstance(c, Special):
            raise CalcError('An eigensystem, Bloch vector or Pauli decomposition is shown, not computed with')
        ma, mc = b.is_matrix(a), b.is_matrix(c)
        if op in '+-':
            if ma != mc:
                raise CalcError('A number and a matrix cannot be added; multiply the number by I first')
            if ma and b.shape(a) != b.shape(c):
                raise CalcError(f'Cannot add a {self._size(a)} and a {self._size(c)} matrix')
            return a + c if op == '+' else a - c
        if op == '*':
            if ma and mc:
                if b.shape(a)[1] != b.shape(c)[0]:
                    raise CalcError(f'Cannot multiply a {self._size(a)} by a {self._size(c)}: the first needs as '
                                    f'many columns as the second has rows')
                return b.matmul(a, c)
            return a * c
        if op == '/':
            if mc:
                raise CalcError('Cannot divide by a matrix; multiply by inv(…) instead')
            return a / c
        if op == '⊗':
            if not (ma and mc):
                raise CalcError('⊗ joins two states or operators; for a number, just multiply')
            return b.kron(a, c)
        if op == '^':
            if mc:
                raise CalcError('A power must be a number')
            if ma:
                rows, cols = b.shape(a)
                if rows != cols:
                    raise CalcError('Only square matrices have powers')
                n = self._whole_number(c, 'A matrix power must be a whole number')
                return b.power(b.inverse(a), -n) if n < 0 else b.power(a, n)
            return a ** c
        raise CalcError(f'Unknown operation {op}')

    def _whole_number(self, x, message):
        if self.backend.name == 'digits':
            z = complex(x)
            if z.imag != 0 or z.real != int(z.real):
                raise CalcError(message)
            return int(z.real)
        if not getattr(x, 'is_integer', False):
            raise CalcError(message)
        return int(x)

    def _size(self, v):
        rows, cols = self.backend.shape(v)
        return f'{rows}×{cols}'

    def _call(self, name, args):
        b = self.backend

        def need(count):
            if len(args) != count:
                raise CalcError(f'{name}() takes {count} argument{"s" if count != 1 else ""}')

        def square(v):
            if not b.is_matrix(v) or b.shape(v)[0] != b.shape(v)[1]:
                raise CalcError(f'{name}() needs a square matrix')
            return v
        scalar_functions = ('exp', 'sin', 'cos', 'tan', 'log', 'conj', 're', 'im', 'abs', 'sqrt')
        if name in scalar_functions:
            need(1)
            x = args[0]
            if b.is_matrix(x):
                if name == 'exp':
                    return b.expm(square(x))
                if name == 'conj':
                    return b.dagger(b.transpose(x))
                if name == 'abs':
                    return b.norm(x)
                raise CalcError(f'{name}() of a matrix is not supported; use it on numbers')
            return b.scalar_function(name, x)
        if name in ('dag', 'adjoint'):
            need(1)
            return b.dagger(args[0])
        if name in ('T', 'transpose'):
            need(1)
            return b.transpose(args[0])
        if name in ('tr', 'trace'):
            need(1)
            return b.trace(square(args[0]))
        if name == 'det':
            need(1)
            return b.det(square(args[0]))
        if name == 'inv':
            need(1)
            return b.inverse(square(args[0]))
        if name == 'norm':
            need(1)
            return b.norm(args[0]) if b.is_matrix(args[0]) else b.scalar_function('abs', args[0])
        if name == 'normalize':
            need(1)
            return args[0] / b.norm(args[0])
        if name == 'kron':
            if len(args) < 2:
                raise CalcError('kron() takes two or more arguments')
            value = args[0]
            for other in args[1:]:
                value = b.kron(value, other)
            return value
        if name in ('comm', 'commutator'):
            need(2)
            return b.matmul(args[0], args[1]) - b.matmul(args[1], args[0])
        if name in ('acomm', 'anticommutator'):
            need(2)
            return b.matmul(args[0], args[1]) + b.matmul(args[1], args[0])
        if name in ('Id', 'eye'):
            need(1)
            n = self._whole_number(args[0], 'Id(n) needs a whole number')
            if not 1 <= n <= MAX_DIMENSION:
                raise CalcError(f'Id(n) needs 1 ≤ n ≤ {MAX_DIMENSION}')
            return b.identity(n)
        if name in ('RX', 'RY', 'RZ', 'P', 'U'):
            return self._rotation(name, args)
        result = self._quantum(name, args)
        if result is not None:
            return result
        raise CalcError(f'{name}() is not a known function')

    def _rotation(self, name, args):
        b = self.backend
        i = b.constant('i')
        if name == 'U':
            if len(args) != 3:
                raise CalcError('U(θ, φ, λ) takes three angles')
            t, p, l = args
            c, s = b.scalar_function('cos', t / 2), b.scalar_function('sin', t / 2)
            e = lambda x: b.scalar_function('exp', i * x)               # noqa: E731
            return b.matrix([[c, -e(l) * s], [e(p) * s, e(p + l) * c]])
        if len(args) != 1:
            raise CalcError(f'{name}(θ) takes one angle')
        t = args[0]
        c, s = b.scalar_function('cos', t / 2), b.scalar_function('sin', t / 2)
        if name == 'RX':
            return b.matrix([[c, -i * s], [-i * s, c]])
        if name == 'RY':
            return b.matrix([[c, -s], [s, c]])
        if name == 'RZ':
            return b.matrix([[b.scalar_function('exp', -i * t / 2), 0], [0, b.scalar_function('exp', i * t / 2)]])
        return b.matrix([[1, 0], [0, b.scalar_function('exp', i * t)]])           # P(λ)


# ---- results that are not numbers or matrices (v0.9.0, 20b) ------------------------------------
@dataclass
class Special:
    """An eigensystem, a Bloch vector or a Pauli decomposition: shown, not computed with."""
    kind: str                           # 'eigen', 'bloch', 'pauli'
    data: list


def _quantum(self, name, args):
    """The quantum functions; None if `name` is not one of them."""
    b = self.backend
    exact = b.name == 'exact'

    def need(count):
        if len(args) != count:
            raise CalcError(f'{name}() takes {count} argument{"s" if count != 1 else ""}')

    def density(v):
        """A ket becomes |ψ⟩⟨ψ|; a square matrix is taken as a density matrix already."""
        if not b.is_matrix(v):
            raise CalcError(f'{name}() needs a state or a density matrix')
        rows, cols = b.shape(v)
        if cols == 1:
            return b.matmul(v, b.dagger(v))
        if rows == 1:
            return b.matmul(b.dagger(v), v)
        if rows != cols:
            raise CalcError(f'{name}() needs a state or a square density matrix')
        return v

    def qubits(v):
        n = b.shape(v)[0]
        count = n.bit_length() - 1
        if n < 2 or 1 << count != n:
            raise CalcError(f'{name}() needs a size that is a power of 2 (qubits)')
        return count
    if name in ('dm', 'density'):
        need(1)
        return density(args[0])
    if name == 'expect':
        need(2)
        operator, state = args
        if not b.is_matrix(operator) or b.shape(operator)[0] != b.shape(operator)[1]:
            raise CalcError('expect(O, ψ) needs an operator first')
        if b.is_matrix(state) and b.shape(state)[1] == 1:
            if b.shape(state)[0] != b.shape(operator)[0]:
                raise CalcError('expect(O, ψ): the operator and the state have different sizes')
            return self._scalar_if_1x1(b.matmul(b.dagger(state), b.matmul(operator, state)))
        return b.trace(b.matmul(density(state), operator))
    if name == 'ptrace':
        need(2)
        rho = density(args[0])
        n = qubits(rho)
        q = self._whole_number(args[1], 'ptrace(ρ, q): q is the qubit to trace out (0 is the leftmost)')
        if not 0 <= q < n:
            raise CalcError(f'ptrace(ρ, q): q must be 0 to {n - 1} for {n} qubits')
        if n == 1:
            raise CalcError('ptrace() needs at least two qubits')
        dim, keep = 1 << n, n - 1
        out = [[0] * (1 << keep) for _ in range(1 << keep)]
        entries = b.entries(rho)
        for r in range(dim):
            for c in range(dim):
                if (r >> (n - 1 - q)) & 1 != (c >> (n - 1 - q)) & 1:
                    continue
                drop = lambda i: ((i >> (n - q)) << (n - 1 - q)) | (i & ((1 << (n - 1 - q)) - 1))   # noqa: E731
                out[drop(r)][drop(c)] = out[drop(r)][drop(c)] + entries[r][c]
        return b.matrix(out)
    if name == 'purity':
        need(1)
        rho = density(args[0])
        return b.trace(b.matmul(rho, rho))
    if name in ('eig', 'eigen'):
        need(1)
        m = args[0]
        if not b.is_matrix(m) or b.shape(m)[0] != b.shape(m)[1]:
            raise CalcError('eig() needs a square matrix')
        return Special('eigen', self._eigen(m))
    if name == 'entropy':
        need(1)
        rho = density(args[0])
        values = [value for value, _ in self._eigen(rho, vectors=False)]
        if exact:
            sp = b.sp
            return sp.simplify(-sum(v * sp.log(v, 2) for v in values if sp.simplify(v) != 0))
        return float(-sum(v.real * np.log2(v.real) for v in map(complex, values) if v.real > 1e-12))
    if name == 'fidelity':
        need(2)
        a, c = args
        pure = lambda v: b.is_matrix(v) and b.shape(v)[1] == 1                     # noqa: E731
        if pure(a) and pure(c):
            overlap = self._scalar_if_1x1(b.matmul(b.dagger(a), c))
            return b.scalar_function('abs', overlap) ** 2
        if pure(a) or pure(c):
            state, rho = (a, density(c)) if pure(a) else (c, density(a))
            return self._scalar_if_1x1(b.matmul(b.dagger(state), b.matmul(rho, state)))
        if exact:
            raise CalcError('fidelity() of two mixed states is computed in digits mode only')
        from scipy.linalg import sqrtm
        root = sqrtm(a)
        return float(np.real(np.trace(sqrtm(root @ c @ root))) ** 2)
    if name == 'bloch':
        need(1)
        rho = density(args[0])
        if b.shape(rho) != (2, 2):
            raise CalcError('bloch() needs one qubit')
        lib = self.library()
        return Special('bloch', [self._real_part(b.trace(b.matmul(rho, lib[p]))) for p in 'XYZ'])
    if name == 'pauli':
        need(1)
        m = args[0]
        if not b.is_matrix(m) or b.shape(m)[0] != b.shape(m)[1]:
            raise CalcError('pauli() needs a square matrix')
        n = qubits(m)
        if n > 4:
            raise CalcError('pauli() is limited to 4 qubits (256 Pauli strings)')
        import itertools
        lib = self.library()
        terms = []
        for word in itertools.product('IXYZ', repeat=n):
            op = lib[word[0]]
            for letter in word[1:]:
                op = b.kron(op, lib[letter])
            coefficient = b.trace(b.matmul(op, m)) / (1 << n)
            coefficient = b.simplify(coefficient) if exact else complex(coefficient)
            if (coefficient != 0) if exact else abs(coefficient) > 1e-12:
                terms.append((''.join(word), coefficient))
        return Special('pauli', terms)
    return None


def _real_part(self, z):
    b = self.backend
    return b.sp.simplify(b.sp.re(z)) if b.name == 'exact' else float(complex(z).real)


def _eigen(self, m, vectors=True):
    """[(eigenvalue, normalized eigenvector or None)], sorted by eigenvalue."""
    b = self.backend
    if b.name == 'exact':
        sp = b.sp
        if m.rows > EXACT_LIMIT:
            raise CalcError(f'Exact eigenvalues are limited to {EXACT_LIMIT}×{EXACT_LIMIT}; use digits mode')
        pairs = []
        if not vectors:
            for value, multiplicity in m.eigenvals().items():
                pairs += [(sp.simplify(value), None)] * multiplicity
        else:
            for value, _, basis in m.eigenvects():
                for v in basis:
                    norm = sp.sqrt(sp.simplify(sum(sp.Abs(e) ** 2 for e in v)))
                    v = (v / norm).applyfunc(sp.simplify)
                    first = next(e for e in v if sp.simplify(e) != 0)       # the same phase as digits mode:
                    v = (v * sp.conjugate(first) / sp.Abs(first)).applyfunc(sp.simplify)   # first entry > 0
                    pairs.append((sp.simplify(value), v))
        return sorted(pairs, key=lambda p: (complex(sp.N(p[0])).real if not p[0].free_symbols else 0,
                                            complex(sp.N(p[0])).imag if not p[0].free_symbols else 0))
    hermitian = np.allclose(m, m.conj().T, atol=1e-12)
    if hermitian:
        values, vecs = np.linalg.eigh(m)
    else:
        values, vecs = np.linalg.eig(m)
        order = np.lexsort((values.imag, values.real))
        values, vecs = values[order], vecs[:, order]
    out = []
    for k, value in enumerate(values):
        v = vecs[:, [k]] / np.linalg.norm(vecs[:, k])
        first = v[np.flatnonzero(np.abs(v) > 1e-12)[0], 0]           # a fixed global phase: first entry > 0
        v = v * (abs(first) / first)
        out.append((value.real if hermitian or abs(value.imag) < 1e-12 else value, v if vectors else None))
    return out


Calculator._quantum = _quantum
Calculator._real_part = _real_part
Calculator._eigen = _eigen
