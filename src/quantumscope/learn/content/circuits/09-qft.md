---
title: The quantum Fourier transform
area: circuits
kind: lecture
order: 9
objectives: State what the QFT does to a basis state | Build the QFT from H, controlled-phase and SWAP gates | Recognize the QFT's phase pattern in the State Inspector
math: 01-complex-numbers, 11-fourier-transform
---
# The quantum Fourier transform

## The idea

The quantum Fourier transform rewrites a number stored in the qubits as a pattern of phases: each output amplitude turns by an angle proportional to the input. On its own that pattern is invisible to measurement, but run backwards it turns a phase into a readable number — the key step of phase estimation and Shor's factoring algorithm.

## Definition

On $n$ qubits with $N = 2^n$, the **quantum Fourier transform** maps each basis state to an evenly spread superposition whose phases rotate at a rate set by $x$:

$$QFT\,|x\rangle = \frac{1}{\sqrt{N}}\sum_{y=0}^{N-1} e^{2\pi i\,xy/N}\,|y\rangle$$

Here $x$ and $y$ are read as binary numbers with q0 as the most significant bit. Every outcome is equally likely; all the information is in the **phases**.

## The circuit

For each qubit in turn, from q0 down:

1. Apply H.
2. Apply a controlled phase $CP(\pi/2^k)$ from each lower qubit, where $k$ is the distance between them.

Finally, SWAP the qubits to reverse their order. On three qubits this takes 3 H gates, 3 CP gates and 1 SWAP. In general it needs about $n^2/2$ gates, far fewer than the $N^2$ operations of a direct matrix product.

## Seeing the phases

For $|x\rangle = |001\rangle$ on 3 qubits ($x = 1$), the amplitude of $|y\rangle$ has phase $2\pi y/8$: the phases step around the circle in eighths. The State Inspector's color swatches show this as a rainbow. For $x = 2$ they step in quarters, twice as fast.

[Try it: QFT of |001⟩ with the State Inspector](qs:algorithm/qft?n=3&x=1&inverse=no&inspector=1)

The inverse transform QFT† undoes the QFT exactly; it is a key step of phase estimation.

[Try it: QFT followed by QFT†](qs:algorithm/qft?n=3&x=5&inverse=yes&inspector=1)

## Worked example

QFT of $|10\rangle$ on two qubits, so $x = 2$ and $N = 4$. The phase of $|y\rangle$ is $e^{2\pi i \cdot 2y/4} = (-1)^y$:

$$QFT\,|10\rangle = \frac{1}{2}\left(|00\rangle - |01\rangle + |10\rangle - |11\rangle\right) = |+\rangle \otimes |-\rangle$$

Every outcome has probability $\frac{1}{4}$, yet the state is far from random: it is a product of two simple single-qubit states. This holds for every basis input — the QFT of $|x\rangle$ is always a product state, with each qubit's phase set by the bits of $x$. That is why a circuit of only about $n^2/2$ gates can produce it.

## Common mistakes

- **Measuring right after the QFT.** All outcomes are equally likely; the information is in the phases, which need the inverse QFT to read.
- **Forgetting the final SWAPs.** Without them the output qubits come out in reversed order.
- **Reading x with the wrong bit order.** Here q0 is the most significant bit, so $|001\rangle$ is $x = 1$.

## In the app

**Algorithms → QFT** builds the circuit for any input $x$. With the State Inspector open, the colored phase swatches show the phases stepping around the circle; choose QFT followed by QFT† to see the input return exactly.

## Check your understanding

```quiz
Q: After the QFT of a basis state, what is the probability of each outcome?
- It depends on x
* 1/N for every outcome
- 1 for y = x and 0 otherwise
E: Every amplitude has magnitude 1/√N; x only changes the phases.
```

```quiz
Q: Why does the QFT end with SWAP gates?
- To undo the controlled phases
* The H-and-phase stages produce the output with its qubits in reverse order
- They are needed to make the circuit unitary
E: Without the SWAPs, the result is correct but with q0 and q(n−1) exchanged, and so on.
```

```quiz
Q: The QFT is applied to |000⟩. What is the result?
* The uniform superposition: every amplitude 1/√8 with phase 0
- |000⟩ unchanged
- |111⟩
E: For x = 0 every phase e^{2πi·0·y/N} is 1, so the QFT of |0…0⟩ is H on every qubit.
```

```quiz
Q: About how many gates does the QFT on 10 qubits need?
- About 1,000,000
* About 50
- About 10
E: About n²/2 = 50 gates (plus a few SWAPs), compared with N² ≈ 10⁶ entries in the full matrix.
```

## Summary

- The QFT spreads a basis state evenly, encoding x in phases e^{2πixy/N}.
- It uses H, CP(π/2^k) and a final reversal by SWAPs: about n²/2 gates.
- QFT† undoes it; both are blocks in the Algorithms menu.
