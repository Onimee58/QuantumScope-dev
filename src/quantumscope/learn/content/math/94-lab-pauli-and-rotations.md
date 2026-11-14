---
title: "Lab: Pauli algebra and rotations"
area: math
kind: lab
order: 94
objectives: Verify the Pauli product rules | Compute a commutator | Build rotation gates as exponentials
---
# Lab: Pauli algebra and rotations

You will check the rules that make Pauli algebra quick — XY = iZ and its relatives — and see the rotation gates appear as exponentials of Paulis. Read *Pauli algebra* and *Matrix exponentials and rotations* first.

[Open the calculator](qs:open/calculator)

```step
title: Two Paulis make the third
text: Compute X*Y, then compare it with i*Z: they are equal.
check: calc typed X*Y
check: calc gives i*Z
```

```step
title: A commutator
text: Evaluate commutator(X, Z). The result equals −2iY: X and Z do not commute, so they cannot be measured together with definite results.
check: calc gives -2i*Y
```

```step
title: A rotation as an exponential
text: Evaluate exp(-i*(pi/2)*X/2)|0⟩ and compare with RX(pi/2)|0⟩. Both give (|0⟩ − i|1⟩)/√2: a quarter turn about x takes the north pole to −y.
check: calc typed exp(
check: calc gives [1; -i]/sqrt(2)
```

```step
title: A half turn is X, up to a phase
text: Evaluate RX(pi). The result is −iX: the same gate as X, multiplied by a global phase.
check: calc gives -i*X
```

## What you found

XY = iZ and its cyclic partners, anticommuting Paulis, and the formula e^{−iθP/2} = cos(θ/2) I − i sin(θ/2) P: the whole algebra of single-qubit gates in a few lines.

```quiz
Q: What does RX(2*pi) give?
- I
* −I
- X
E: cos(π) I − i sin(π) X = −I: a full turn on the Bloch sphere is a global phase of −1.
```
