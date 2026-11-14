---
title: The discrete Fourier transform
area: math
kind: lecture
order: 11
objectives: Work with roots of unity | Write the DFT matrix for small sizes | Explain why the quantum Fourier transform is unitary
---
# The discrete Fourier transform

## The idea

The **quantum Fourier transform** at the heart of phase estimation and Shor's algorithm is the ordinary discrete Fourier transform, applied to amplitudes. It converts between two descriptions of the same state: one where information is a **position** (which basis state), and one where it is a **phase that turns step by step**. Everything rests on one fact: equally spaced points around a circle add up to zero.

## Roots of unity

The $N$-th **roots of unity** are the $N$ complex numbers with $\omega^N = 1$. They are evenly spaced around the unit circle:

$$\omega = e^{2\pi i/N}, \qquad 1, \omega, \omega^2, \dots, \omega^{N-1}$$

For $N = 4$: $1, i, -1, -i$. Added together, the roots of unity always give 0: they cancel around the circle. This cancellation is what makes the transform work.

## The DFT matrix

The discrete Fourier transform of size $N$ is the $N \times N$ matrix with entries

$$F_{jk} = \frac{1}{\sqrt{N}}\, \omega^{jk} \qquad (j, k = 0, \dots, N-1)$$

For $N = 2$, $\omega = -1$ and $F$ is exactly the Hadamard gate $H$. For $N = 4$:

$$F = \frac{1}{2}\begin{pmatrix} 1 & 1 & 1 & 1 \\ 1 & i & -1 & -i \\ 1 & -1 & 1 & -1 \\ 1 & -i & -1 & i \end{pmatrix}$$

## Why it is unitary

Two different columns $k$ and $l$ of $F$ have inner product

$$\frac{1}{N}\sum_{j=0}^{N-1} \omega^{j(l - k)} = 0$$

because the terms are roots of unity that cancel. Each column has length 1, so the columns are orthonormal and $F^\dagger F = I$: the Fourier transform is a valid quantum gate. Its inverse $F^\dagger$ simply uses $\omega^{-jk}$.

## What it does

The DFT turns a **phase that grows step by step** into a **single peak**. The state

$$\frac{1}{\sqrt{N}}\sum_{j} e^{2\pi i\, j\varphi}\, |j\rangle$$

is turned by $F^\dagger$ into a state concentrated on $|k\rangle$ with $k/N \approx \varphi$. Phase estimation prepares exactly this state with **phase kickback**, then reads $\varphi$ off as a binary number. On $n$ qubits, $N = 2^n$, and the quantum circuit needs only about $n^2$ gates, far fewer than the $N^2 = 4^n$ entries of the matrix.

## Worked example

Take $N = 4$ and the basis state $|1\rangle$. $F|1\rangle$ is column 1 of the matrix:

$$F|1\rangle = \frac{1}{2}\left(|0\rangle + i|1\rangle - |2\rangle - i|3\rangle\right)$$

Every amplitude has size $\frac{1}{2}$, so all four outcomes are equally likely; the information is now in the phases, which turn by a quarter circle ($\varphi = \frac{1}{4}$) from one basis state to the next. Applying $F^\dagger$ undoes this: the phases of the four terms line up only for $|1\rangle$ and cancel for every other basis state, and the peak returns to $|1\rangle$, that is $k/N = \frac{1}{4} = \varphi$.

## Common mistakes

- **Expecting the QFT to change probabilities into a peak by itself.** $F$ spreads a basis state evenly; it is $F^\dagger$ applied to a phase pattern that makes the peak.
- **Mixing up $F$ and $F^\dagger$.** Phase estimation ends with the *inverse* transform.
- **Thinking the quantum circuit multiplies the full matrix.** It uses about $n^2$ gates (Hadamards and controlled phases), not $4^n$ multiplications.

## In the app

Open the QFT example from the algorithm library and step through it in the State Inspector: a basis state spreads into equal amplitudes with turning phases. Phase estimation with 3 counting qubits reads $\varphi = 3/8$ exactly, since 3/8 has three binary digits. In the calculator, the Hadamard written as a matrix is the one-qubit Fourier transform.

[Try it: phase estimation reads φ = 3/8 exactly with 3 counting qubits](qs:algorithm/qpe?t=3&phase=3/8)

[Try it in the calculator: the one-qubit Fourier transform of |0⟩](qs:calc?expr=%5B1%2C%201%3B%201%2C%20-1%5D%2Fsqrt%282%29%20%7C0%E2%9F%A9)

## Check your understanding

```quiz
Q: What are the 4th roots of unity?
* 1, i, −1, −i
- 1, 2, 3, 4
- 0, 1, 2, 3
E: e^{2πik/4} for k = 0…3: the points 1, i, −1, −i on the unit circle.
```

```quiz
Q: Which gate is the DFT of size 2?
- X
* H
- Z
E: For N = 2, ω = −1, so F = (1/√2)[[1, 1], [1, −1]], the Hadamard gate.
```

```quiz
Q: What is the sum 1 + ω + ω² for ω = e^{2πi/3}?
* 0
- 3
- 1
E: The three cube roots of unity are evenly spaced on the unit circle, so they cancel.
```

```quiz
Q: With N = 4, F|0⟩ is measured. What are the outcome probabilities?
- |0⟩ with certainty
* Each of the four outcomes with probability 1/4
- |1⟩ and |3⟩, 1/2 each
E: Column 0 of F has every entry 1/2, so each outcome has probability (1/2)² = 1/4.
```

## Summary

- The $N$-th roots of unity $\omega^k$, $\omega = e^{2\pi i/N}$, sum to 0.
- $F_{jk} = \omega^{jk}/\sqrt{N}$ has orthonormal columns, so it is unitary; for $N = 2$ it is $H$.
- $F$ spreads a basis state into turning phases; $F^\dagger$ turns a steadily growing phase back into a peak: the core of phase estimation.
