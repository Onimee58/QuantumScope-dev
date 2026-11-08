"""Parsing calculator input into a tree (v0.9.0).

Notation (Unicode, or the plain-keyboard form in brackets):
  kets |0⟩ |+⟩ |01⟩ |ψ⟩ (|0>)      bras ⟨0| (<0|)      ⟨a|b⟩ shares one bar     ⟨a|M|b⟩
  products: A B (side by side), A * B, A · B      tensor: A ⊗ B (A (x) B)      a / b
  powers A^2      adjoint A† (A')      matrices [[1, 0], [0, 1]] or [1, 0; 0, 1]
  functions f(x, y)      names: letters, digits, _ and Greek (ψ, θ, …)      assignment: ψ = H|0⟩
Precedence, loosest first: + and −, products (and side by side), ⊗, signs, ^, †.
So H ⊗ I |00⟩ is (H ⊗ I)|00⟩, and 2 X ⊗ Y is 2 (X ⊗ Y).
"""
from dataclasses import dataclass, field


class CalcError(ValueError):
    """A problem with the input, explained for the user; `at` is the character position, if known."""

    def __init__(self, message, at=None):
        super().__init__(message)
        self.at = at


@dataclass
class Node:
    kind: str                          # number, name, ket, bra, matrix, call, unary, binary, postfix
    value: object = None               # the number, name, label, operator or function name
    args: list = field(default_factory=list)
    text: str = ''                     # the source text, for showing the working


@dataclass
class Statement:
    expr: Node
    assign: str = None                 # `name = …`


GREEK = 'αβγδεζηθικλμνξοπρστυφχψωΓΔΘΛΞΠΣΦΨΩ'
SYMBOLS = {'⊗': '⊗', '·': '*', '×': '*', '−': '-', '†': '†', '⁺': '†', "'": '†'}


def _is_name_start(ch):
    return ch.isalpha() or ch == '_' or ch in GREEK


@dataclass
class Token:
    kind: str                          # num, name, ket, bra, op, end
    value: object
    start: int
    end: int


def tokenize(text):
    tokens, i, n = [], 0, len(text)
    while i < n:
        ch = text[i]
        if ch.isspace():
            i += 1
            continue
        if ch.isdigit() or (ch == '.' and i + 1 < n and text[i + 1].isdigit()):
            j = i
            while j < n and (text[j].isdigit() or text[j] == '.'):
                j += 1
            if j < n and text[j] in 'eE' and j + 1 < n and (text[j + 1].isdigit() or text[j + 1] in '+-'):
                k = j + 1 + (text[j + 1] in '+-')
                if k < n and text[k].isdigit():
                    j = k
                    while j < n and text[j].isdigit():
                        j += 1
            if text[i:j].count('.') > 1:
                raise CalcError(f'"{text[i:j]}" is not a number', i)
            tokens.append(Token('num', text[i:j], i, j))
            i = j
            continue
        if _is_name_start(ch):
            j = i
            while j < n and (text[j].isalnum() or text[j] == '_' or text[j] in GREEK):
                j += 1
            tokens.append(Token('name', text[i:j], i, j))
            i = j
            continue
        if ch == '(' and text[i:i + 3] == '(x)':
            tokens.append(Token('op', '⊗', i, i + 3))
            i += 3
            continue
        if ch in '⟨<':                                         # a bra: ⟨label| ; ⟨a|b⟩ shares the bar
            j = text.find('|', i + 1)
            if j < 0:
                raise CalcError('A bra ⟨…| needs its closing bar', i)
            label = text[i + 1:j].strip()
            if not label:
                raise CalcError('A bra needs a label, as in ⟨0|', i)
            tokens.append(Token('bra', label, i, j + 1))
            k = j + 1                                          # ⟨a|b⟩: the ket shares this bar
            m = k
            while m < n and text[m] not in '⟩>|⟨<' and not text[m].isspace() and text[m] not in '()[]*·⊗,;=^':
                m += 1
            if m > k and m < n and text[m] in '⟩>':
                tokens.append(Token('ket', text[k:m].strip(), k, m + 1))
                i = m + 1
            else:
                i = k
            continue
        if ch == '|':                                          # a ket: |label⟩
            m = i + 1
            while m < n and text[m] not in '⟩>|':
                m += 1
            if m >= n or text[m] == '|':
                raise CalcError('A ket |…⟩ needs its closing ⟩ (or >)', i)
            label = text[i + 1:m].strip()
            if not label:
                raise CalcError('A ket needs a label, as in |0⟩', i)
            tokens.append(Token('ket', label, i, m + 1))
            i = m + 1
            continue
        if ch in SYMBOLS:
            tokens.append(Token('op', SYMBOLS[ch], i, i + 1))
            i += 1
            continue
        if ch in '+-*/^()[],;=':
            tokens.append(Token('op', ch, i, i + 1))
            i += 1
            continue
        raise CalcError(f'"{ch}" is not something the calculator understands', i)
    tokens.append(Token('end', None, n, n))
    return tokens


class Parser:
    def __init__(self, text):
        self.text = text
        self.tokens = tokenize(text)
        self.pos = 0

    @property
    def tok(self):
        return self.tokens[self.pos]

    def take(self, kind=None, value=None):
        t = self.tok
        if (kind and t.kind != kind) or (value is not None and t.value != value):
            want = repr(value) if value is not None else kind
            found = 'the end' if t.kind == 'end' else f'"{self.text[t.start:t.end]}"'
            raise CalcError(f'Expected {want} but found {found}', t.start)
        self.pos += 1
        return t

    def is_op(self, *values):
        return self.tok.kind == 'op' and self.tok.value in values

    def node(self, kind, value, args, start):
        end = self.tokens[self.pos - 1].end
        return Node(kind, value, args, self.text[start:end].strip())

    def statement(self):
        assign = None
        if self.tok.kind == 'name' and self.tokens[self.pos + 1].kind == 'op' and self.tokens[self.pos + 1].value == '=':
            assign = self.take('name').value
            self.take('op', '=')
        if self.tok.kind == 'end':
            raise CalcError('Type an expression, such as H|0⟩', self.tok.start)
        expr = self.sum()
        if self.tok.kind != 'end':
            raise CalcError(f'Unexpected "{self.text[self.tok.start:self.tok.end]}"', self.tok.start)
        return Statement(expr, assign)

    def sum(self):
        start = self.tok.start
        left = self.product()
        while self.is_op('+', '-'):
            op = self.take().value
            left = self.node('binary', op, [left, self.product()], start)
        return left

    def starts_factor(self):
        t = self.tok
        return t.kind in ('num', 'name', 'ket', 'bra') or (t.kind == 'op' and t.value in ('(', '['))

    def product(self):
        start = self.tok.start
        left = self.tensor()
        while True:
            if self.is_op('*', '/'):
                op = self.take().value
                left = self.node('binary', op, [left, self.tensor()], start)
            elif self.starts_factor():                         # side by side: H|0⟩, 2X, ⟨0|X|1⟩
                left = self.node('binary', '*', [left, self.tensor()], start)
            else:
                return left

    def tensor(self):
        start = self.tok.start
        left = self.signed()
        while self.is_op('⊗'):
            self.take()
            left = self.node('binary', '⊗', [left, self.signed()], start)
        return left

    def signed(self):
        start = self.tok.start
        if self.is_op('-', '+'):
            op = self.take().value
            inner = self.signed()
            return inner if op == '+' else self.node('unary', '-', [inner], start)
        return self.power()

    def power(self):
        start = self.tok.start
        base = self.postfix()
        if self.is_op('^'):
            self.take()
            if self.is_op('†'):                                # A^† is A†
                self.take()
                return self.node('postfix', '†', [base], start)
            return self.node('binary', '^', [base, self.signed()], start)
        return base

    def postfix(self):
        start = self.tok.start
        value = self.atom()
        while self.is_op('†'):
            self.take()
            value = self.node('postfix', '†', [value], start)
        return value

    def atom(self):
        t, start = self.tok, self.tok.start
        if t.kind == 'num':
            self.take()
            return Node('number', t.value, [], t.value)
        if t.kind == 'ket':
            self.take()
            return Node('ket', t.value, [], self.text[t.start:t.end])
        if t.kind == 'bra':
            self.take()
            return Node('bra', t.value, [], self.text[t.start:t.end])
        if t.kind == 'name':
            self.take()
            if self.is_op('('):                                # a function call
                self.take()
                args = []
                if not self.is_op(')'):
                    args.append(self.sum())
                    while self.is_op(','):
                        self.take()
                        args.append(self.sum())
                self.take('op', ')')
                return self.node('call', t.value, args, start)
            return Node('name', t.value, [], t.value)
        if self.is_op('('):
            self.take()
            inner = self.sum()
            self.take('op', ')')
            inner.text = self.text[start:self.tokens[self.pos - 1].end].strip()
            return inner
        if self.is_op('['):
            return self.matrix()
        found = 'the end' if t.kind == 'end' else f'"{self.text[t.start:t.end]}"'
        raise CalcError(f'Expected a number, name, state or bracket, but found {found}', t.start)

    def matrix(self):
        """[[1, 0], [0, 1]] (a list of rows) or [1, 0; 0, 1] (rows separated by ;)."""
        start = self.tok.start
        self.take('op', '[')
        rows = []
        if self.is_op('['):
            while True:
                self.take('op', '[')
                row = [self.sum()]
                while self.is_op(','):
                    self.take()
                    row.append(self.sum())
                self.take('op', ']')
                rows.append(row)
                if self.is_op(','):
                    self.take()
                    continue
                break
        else:
            row = [self.sum()]
            while self.is_op(',', ';'):
                sep = self.take().value
                if sep == ';':
                    rows.append(row)
                    row = []
                row.append(self.sum())
            rows.append(row)
        self.take('op', ']')
        if len({len(r) for r in rows}) != 1:
            raise CalcError('Every row of a matrix needs the same number of entries', start)
        return self.node('matrix', None, rows, start)


def parse(text):
    """Text → Statement. Raises CalcError with the position of the problem."""
    return Parser(text).statement()
