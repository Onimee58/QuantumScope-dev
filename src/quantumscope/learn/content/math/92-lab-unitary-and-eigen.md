---
title: "Lab: unitary gates and eigenvalues"
area: math
kind: lab
order: 92
objectives: Check that a matrix is unitary | Find eigenvalues and eigenvectors | Verify an eigenvector by multiplying
---
# Lab: unitary gates and eigenvalues

You will test whether a matrix is a valid gate, find the possible measurement results of an observable, and confirm an eigenvector by hand. Read *Conjugate transpose, Hermitian and unitary* and *Eigenvalues and eigenvectors* first.

[Open the calculator](qs:open/calculator)

```step
title: Is it a gate?
text: Store the matrix with U = [1, i; i, 1]/sqrt(2), then compute U† U. The identity means U is unitary: a valid gate.
hint: † (dagger) is on the calculator's symbol buttons.
check: calc typed U=
check: calc gives I
```

```step
title: Not its own inverse
text: Compute U*U. The result is iX, not the identity: U is unitary but not Hermitian, so undoing it needs U†.
check: calc gives i*X
```

```step
title: The results of measuring Z + X
text: Evaluate eig(Z + X). The two eigenvalues, ±√2, are the only results a measurement of this observable can give.
check: calc typed eig(
```

```step
title: Check an eigenvector
text: The eigenvector for +√2 is proportional to (1 + √2, 1). Compute (Z+X)*[1+sqrt(2); 1] and compare it with sqrt(2)*[1+sqrt(2); 1]: they are equal.
check: calc gives sqrt(2)*[1+sqrt(2); 1]
```

## What you found

Unitary means U†U = I: probabilities are kept and U† undoes the gate. Eigenvalues are the possible measurement results; an eigenvector is only scaled by its matrix.

```quiz
Q: What is det(Z + X)?
- 0
* −2
- 2
E: The product of the eigenvalues: (√2)(−√2) = −2. Directly: 1·(−1) − 1·1 = −2.
```
