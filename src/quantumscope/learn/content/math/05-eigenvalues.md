---
title: Eigenvalues and eigenvectors
area: math
kind: lecture
order: 5
objectives: Check whether a vector is an eigenvector and find its eigenvalue | Name the eigenstates of X, Y and Z | Connect eigenvalues to measurement results
---
# Eigenvalues and eigenvectors

## The idea

Most vectors change direction when a matrix acts on them. The special ones that do not are the **eigenvectors**, and the factor they are stretched by is the **eigenvalue**. In quantum mechanics this is not just algebra: the eigenvalues of an observable are the only results a measurement can give, and its eigenvectors are the states it leaves behind.

## The definition

A nonzero vector $v$ is an eigenvector of $A$, with eigenvalue $\lambda$, if

$$A v = \lambda v$$

Quantum physics calls eigenvectors **eigenstates**. Example: $Z|0\rangle = |0\rangle$ and $Z|1\rangle = -|1\rangle$, so $|0\rangle$ and $|1\rangle$ are eigenstates of $Z$ with eigenvalues $+1$ and $-1$.

## Finding them

For a 2 × 2 matrix, the eigenvalues solve the **characteristic equation**

$$\det(A - \lambda I) = 0$$

For $X$: $\det\begin{pmatrix} -\lambda & 1 \\ 1 & -\lambda \end{pmatrix} = \lambda^2 - 1 = 0$, so $\lambda = \pm 1$. Solving $Xv = v$ gives $v = |+\rangle$, and $Xv = -v$ gives $|-\rangle$.

## The Pauli eigenstates

| Matrix | Eigenvalue +1 | Eigenvalue −1 |
|---|---|---|
| $Z$ | \|0⟩ | \|1⟩ |
| $X$ | \|+⟩ | \|−⟩ |
| $Y$ | \|+i⟩ | \|−i⟩ |

On the Bloch sphere these are the six points where the axes meet the surface.

## Why measurement cares

For an observable $A$ (Hermitian, lesson 4):

- the **possible results** of measuring it are its eigenvalues, which are real;
- right after a measurement with result $\lambda$, the state is the matching eigenstate (the **collapse**);
- eigenstates of a Hermitian matrix with different eigenvalues are orthogonal, so the eigenstates form a basis, the measurement basis.

A state that is already an eigenstate gives its eigenvalue every time. Any other state gives a random eigenvalue, with Born-rule probabilities.

Eigenvalues matter for unitaries too: since $U$ preserves lengths, its eigenvalues have modulus 1, $\lambda = e^{2\pi i \varphi}$. **Phase estimation** measures exactly this $\varphi$.

## Worked example

Find the eigenvalues of the observable $A = Z + X = \begin{pmatrix} 1 & 1 \\ 1 & -1 \end{pmatrix}$:

$$\det\begin{pmatrix} 1 - \lambda & 1 \\ 1 & -1 - \lambda \end{pmatrix} = -(1 - \lambda)(1 + \lambda) - 1 = \lambda^2 - 2 = 0$$

so $\lambda = \pm\sqrt{2}$. A single measurement of $A$ gives $+1.414$ or $-1.414$, never 0 or 2. Its eigenstates point halfway between $+z$ and $+x$ on the Bloch sphere (for $+\sqrt{2}$) and opposite (for $-\sqrt{2}$). Note that $A = \sqrt{2}\,H$: the Hadamard has eigenvalues $\pm 1$ with the same eigenvectors.

## Common mistakes

- **Expecting the eigenvalues of a sum to be the sums.** $Z$ and $X$ each have eigenvalues $\pm 1$, but $Z + X$ has $\pm\sqrt{2}$, because their eigenvectors differ.
- **Accepting the zero vector.** $A\,0 = \lambda\,0$ for every $\lambda$; eigenvectors must be nonzero.
- **Treating a scaled eigenvector as a new one.** $2|+\rangle$ and $-|+\rangle$ are the same eigenstate as $|+\rangle$, up to normalization and phase.

## In the app

In the calculator, `eig(Y)` lists each eigenvalue with its eigenvector; try `eig(Z + X)` for the worked example. In **Quantum Principles → Superposition**, a state on the measurement axis always gives the same result: it is an eigenstate of the measurement.

[Try it: measure |+⟩ along z and along x in the Superposition experiment](qs:open/superposition)

[Try it in the calculator: eig(Y)](qs:calc?expr=eig%28Y%29)

## Check your understanding

```quiz
Q: |+⟩ is measured along x many times. What do you get?
* Always +1
- +1 and −1, half the time each
- Always 0
E: |+⟩ is the eigenstate of X with eigenvalue +1, so measuring X gives +1 every time.
```

```quiz
Q: Which numbers can be eigenvalues of a unitary matrix?
- Any real number
* Complex numbers of modulus 1
- Only 0 and 1
E: U preserves lengths: |Uv| = |λ||v| must equal |v|, so |λ| = 1.
```

```quiz
Q: What are the eigenvalues of the matrix diag(2, 5)?
* 2 and 5
- 7 and 10
- 0 and 7
E: A diagonal matrix's eigenvalues are its diagonal entries, with |0⟩ and |1⟩ as eigenvectors.
```

```quiz
Q: A state is not an eigenstate of Z. What does a Z measurement give?
- The expectation value, every time
* +1 or −1 at random, with Born-rule probabilities
- An error
E: Every single result is an eigenvalue. Only the average over many shots equals the expectation value.
```

## Summary

- $Av = \lambda v$: an eigenvector keeps its direction, scaled by the eigenvalue $\lambda$.
- Eigenvalues solve det(A − λI) = 0; for Z + X they are ±√2.
- The eigenstates of $X$, $Y$ and $Z$ are the six axis points of the Bloch sphere.
- Measuring an observable gives one of its eigenvalues and leaves the matching eigenstate.
