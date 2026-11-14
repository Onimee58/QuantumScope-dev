---
title: "Study guide: Mathematics"
area: math
kind: guide
order: 0
objectives: See which mathematics quantum computing uses and in which order | Find the lecture behind any formula you meet elsewhere | Know what you should be able to compute at the end
---
# Study guide: Mathematics

## What this area is about

Quantum computing uses a small, well-defined toolbox: complex numbers, vectors and matrices, a little probability, and a few special constructions such as the tensor product and the Fourier transform. These twelve lectures cover exactly that toolbox, with quantum examples throughout. Every lecture has a calculator link, so you can check each result yourself.

**Who it is for:** anyone whose linear algebra is new, rusty or purely real-valued. If you studied complex linear algebra recently, skim the summaries and do the questions.

**Time:** about 12–14 hours — roughly 45 minutes per lecture and 30 minutes per lab.

## Before you start

High-school algebra and trigonometry (sine, cosine, angles in radians). Lecture 12 uses derivatives of sine and cosine; everything else needs no calculus.

## Suggested path

You do not have to finish this area before the others. Each lecture in the other areas lists the mathematics it needs under **Math you need**; read those lectures when you first meet them.

| Block | Lecture or lab | Used in |
|---|---|---|
| Foundations | [Complex numbers](qs:lesson/math/01-complex-numbers) | every amplitude and phase |
| Foundations | [Vectors and Dirac notation](qs:lesson/math/02-vectors-and-dirac-notation) | states, inner products |
| Foundations | [Matrices acting on states](qs:lesson/math/03-matrices-acting-on-states) | gates and circuits |
| Foundations | [Probability for quantum experiments](qs:lesson/math/06-probability) | shots and error bars |
| Foundations | [Lab: complex numbers and interference](qs:lesson/math/90-lab-complex-numbers) | practice: amplitudes and interference |
| Foundations | [Lab: states, overlaps and gate products](qs:lesson/math/91-lab-states-and-gates) | practice: states and matrices |
| Structure | [Conjugate transpose, Hermitian and unitary](qs:lesson/math/04-hermitian-and-unitary) | why gates are reversible |
| Structure | [Eigenvalues and eigenvectors](qs:lesson/math/05-eigenvalues) | measurement results |
| Structure | [Tensor products](qs:lesson/math/07-tensor-products) | many qubits, entanglement |
| Structure | [Pauli algebra](qs:lesson/math/10-pauli-algebra) | observables, error correction |
| Structure | [Lab: unitary gates and eigenvalues](qs:lesson/math/92-lab-unitary-and-eigen) | practice: gates and measurement results |
| Structure | [Lab: tensor products and entanglement](qs:lesson/math/93-lab-tensor-products) | practice: many qubits |
| Advanced | [Outer products, projectors and density matrices](qs:lesson/math/08-density-matrices-and-projectors) | noise, mixed states |
| Advanced | [Matrix exponentials and rotations](qs:lesson/math/09-matrix-exponentials) | rotation gates, time evolution |
| Advanced | [The discrete Fourier transform](qs:lesson/math/11-fourier-transform) | QFT, phase estimation |
| Advanced | [Gradients and optimization](qs:lesson/math/12-gradients-and-optimization) | VQE, QAOA, Quantum ML |
| Advanced | [Lab: Pauli algebra and rotations](qs:lesson/math/94-lab-pauli-and-rotations) | practice: rotation gates |
| Advanced | [Lab: an exact gradient from two circuits](qs:lesson/math/95-lab-parameter-shift) | practice: the parameter-shift rule |

The Foundations block is enough for the first Quantum Principles and Quantum Circuits lectures.

## How to study each lecture

1. Read **The idea**, then the definitions, slowly.
2. Redo the **Worked example** on paper before reading the answer.
3. Check your result with the calculator link in **In the app**, and change the numbers to test yourself.
4. Answer the four questions; each one practices a rule from the lecture.
5. Read **Common mistakes**: most are sign, conjugation and order errors.

## Check yourself at the end

You are comfortable with the mathematics when you can:

- compute $|z|^2 = z\bar{z}$ and multiply numbers in polar form;
- normalize a state and compute $\langle\varphi|\psi\rangle$;
- multiply gates in the right order and check that a matrix is unitary or Hermitian;
- find the eigenvalues of a 2 × 2 matrix;
- decide whether a two-qubit state is entangled with $wz - xy$;
- write $R_X(\theta)$ as an exponential and use the parameter-shift rule.

## Where to go next

- [Quantum Principles](qs:lesson/principles/00-study-guide): the physics these tools describe.
- [Quantum Circuits](qs:lesson/circuits/00-study-guide): the tools at work in algorithms.
