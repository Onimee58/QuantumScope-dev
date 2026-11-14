---
title: Conjugate transpose, Hermitian and unitary
area: math
kind: lecture
order: 4
objectives: Compute a conjugate transpose | Check whether a matrix is unitary or Hermitian | Explain why gates are unitary and observables Hermitian
---
# Conjugate transpose, Hermitian and unitary

## The idea

Two kinds of matrices run through all of quantum computing: **unitary** matrices (the gates) and **Hermitian** matrices (the observables). Gates must never lose probability, and measured values must be real numbers; these two physical demands are exactly the two definitions. Both are written with one operation, the **conjugate transpose**.

## The conjugate transpose

The conjugate transpose $A^\dagger$ ("A dagger") flips a matrix over its diagonal and conjugates every entry:

$$\begin{pmatrix} a & b \\ c & d \end{pmatrix}^\dagger = \begin{pmatrix} \bar{a} & \bar{c} \\ \bar{b} & \bar{d} \end{pmatrix}$$

For a ket, the dagger gives its bra: $|\psi\rangle^\dagger = \langle\psi|$. A useful rule: $(AB)^\dagger = B^\dagger A^\dagger$, the order reverses.

## Unitary: gates

A matrix $U$ is **unitary** if

$$U^\dagger U = I$$

Unitary matrices preserve inner products, $\langle U\varphi|U\psi\rangle = \langle\varphi|\psi\rangle$, so they preserve lengths and therefore **probabilities**: a normalized state stays normalized. That is why every quantum gate must be unitary.

Two more consequences:

- Every gate can be undone: its inverse is simply $U^\dagger$.
- $X$, $Z$ and $H$ are their own inverses, since $X^\dagger X = X^2 = I$, and likewise for $Z$ and $H$.

## Hermitian: observables

A matrix $A$ is **Hermitian** if it equals its own conjugate transpose:

$$A = A^\dagger$$

The diagonal of a Hermitian matrix is real, and the entries across the diagonal are conjugates of each other. Hermitian matrices have **real eigenvalues** (lesson 5), which is why measurable quantities, the **observables**, are Hermitian: measurement results are real numbers.

## Examples

| Matrix | Unitary? | Hermitian? |
|---|---|---|
| $X$, $Y$, $Z$, $H$ | yes | yes |
| $S = \mathrm{diag}(1, i)$ | yes | no, since $S^\dagger = \mathrm{diag}(1, -i)$ |
| $Z_0 Z_1 + 0.5\,X_0$ (an observable) | no | yes |

The Pauli matrices and $H$ are both: they are gates and observables at once.

## Worked example

Test $U = \frac{1}{\sqrt{2}}\begin{pmatrix} 1 & i \\ i & 1 \end{pmatrix}$. Its conjugate transpose conjugates the $i$'s:

$$U^\dagger = \frac{1}{\sqrt{2}}\begin{pmatrix} 1 & -i \\ -i & 1 \end{pmatrix}, \qquad U^\dagger U = \frac{1}{2}\begin{pmatrix} 1 + 1 & i - i \\ -i + i & 1 + 1 \end{pmatrix} = I$$

So $U$ is unitary: a valid gate. It is not Hermitian, since $U^\dagger \neq U$. Undoing it needs $U^\dagger$, not $U$ again: applying $U$ twice gives $U^2 = iX$, a bit flip with a global phase.

## Common mistakes

- **Transposing without conjugating.** For complex matrices, $A^T$ and $A^\dagger$ differ; unitarity and Hermiticity use $A^\dagger$.
- **Thinking every gate is its own inverse.** True for X, Z and H, but S, T and most rotations need their daggers: S is undone by S†, not by S.
- **Reversing $(AB)^\dagger$ the wrong way.** It is $B^\dagger A^\dagger$; this is why undoing a circuit runs the gates' inverses in reverse order.

## In the app

The gate palette has each non-self-inverse gate's partner: S and SDG, T and TDG. Build H, S, SDG and check in the State Inspector that the state is $|+\rangle$ again. In the calculator, `†` takes the conjugate transpose: `H† H` gives the identity, and `S† S` does too, while `S S` does not.

[Try it: S followed by its inverse SDG returns |+⟩ unchanged](qs:circuit?n=1&gates=H:0;S:0;SDG:0)

[Try it in the calculator: H† H](qs:calc?expr=H%E2%80%A0%20H)

## Check your understanding

```quiz
Q: Which property makes a matrix a valid quantum gate?
* U†U = I (unitary)
- A = A† (Hermitian)
- All entries real
E: Gates must keep states normalized, which is exactly the unitary condition.
```

```quiz
Q: Is the matrix with rows (1, 2i) and (−2i, 3) Hermitian?
* Yes
- No
E: Its diagonal is real and the off-diagonal entries 2i and −2i are conjugates, so it equals its conjugate transpose.
```

```quiz
Q: What undoes the gate T?
- T again
* T† (TDG)
- Z
E: T is unitary, so its inverse is T†. T·T = S, not the identity.
```

```quiz
Q: A circuit applies A, then B. Which circuit undoes it?
- A†, then B†
* B†, then A†
- B, then A
E: The circuit is BA, and (BA)† = A†B†, which applies B† first and A† last.
```

## Summary

- $A^\dagger$: transpose and conjugate; $(AB)^\dagger = B^\dagger A^\dagger$.
- Unitary ($U^\dagger U = I$): preserves probabilities; every gate, undone by $U^\dagger$.
- Hermitian ($A = A^\dagger$): real eigenvalues; every observable.
- Some matrices are both (X, Y, Z, H); most gates are only unitary.
