---
title: The variational quantum linear solver
area: circuits
kind: lecture
order: 27
objectives: Write a linear system as a quantum state problem | Explain the VQLS cost and why its minimum is the solution | Explain how the condition number affects the solve
math: 04-hermitian-and-unitary, 10-pauli-algebra, 12-gradients-and-optimization
---
# The variational quantum linear solver

Many problems in science and engineering come down to a **linear system** $A x = b$. Quantum algorithms approach it by preparing a state proportional to the solution, $|x\rangle \propto A^{-1}|b\rangle$. The famous HHL algorithm (Harrow, Hassidim and Lloyd, 2009) needs deep circuits; the **variational quantum linear solver** (VQLS; Bravo-Prieto et al., 2023) uses a short parameterized circuit and a classical optimizer instead.

## The idea

A parameterized circuit prepares $|x(\theta)\rangle$. The goal is to make $A|x\rangle$ point along $|b\rangle$: then $|x\rangle$ is the normalized solution. QuantumScope uses the cost

$$C(\theta) = \langle x(\theta)|\, A^\dagger (I - |b\rangle\langle b|)\, A\, |x(\theta)\rangle$$

The operator in the middle is Hermitian and never negative, and $C = 0$ exactly when $A|x\rangle$ has no part orthogonal to $|b\rangle$, that is, at the solution (for an invertible $A$). So minimizing $C$ is a VQE-style problem: QuantumScope writes the operator as a Pauli sum and uses it as the circuit's observable, and **Optimize**, the landscape and **Best of N** work as for VQE.

## The systems

In **Algorithms → Variational quantum linear solver**, the matrix $A$ is a sum of Pauli terms, as in the original paper:

$$A = 1 + 0.2\, X_0 Z_1 + 0.2\, X_0, \qquad |b\rangle = |{+}{+}{+}\rangle$$

You can also enter your own $A$ on 1 to 3 qubits, with $|b\rangle$ = |0…0⟩, |+…+⟩ or |1…1⟩. QuantumScope rejects a matrix that is not invertible, since then $A x = b$ has no unique solution. **Show the solution** compares the circuit's amplitudes with the classical solution $A^{-1}b$ as you optimize.

## The condition number

How hard a system is depends on its **condition number** $\kappa = \sigma_{\max}/\sigma_{\min}$, the ratio of the largest to the smallest singular value of $A$. The standard system has $\kappa \approx 2.3$; the worse-conditioned one, with 0.45 instead of 0.2, has $\kappa = 19$. Its cost landscape is flatter near the solution, and the optimizer needs about twice as many steps. For real VQLS on hardware, the number of measurements also grows with $\kappa$.

## On hardware

A quantum computer cannot read $C$ directly. VQLS estimates the terms with **Hadamard tests**: circuits with one extra qubit that controls the Pauli terms of $A$. QuantumScope computes $C$ exactly instead, to show the method itself clearly.

[Try it: solve a 1-qubit system with VQLS](qs:algorithm/vqls?problem=single&layers=1)

## Worked example

The 1-qubit system: $A = 1 + 0.5X$ and $|b\rangle = |0\rangle$. Since $X^2 = 1$, $A^{-1} = \frac{4}{3}(1 - 0.5X)$, so

$$A^{-1}|0\rangle = \frac{4}{3}\left(|0\rangle - 0.5|1\rangle\right) \ \Rightarrow\ |x\rangle \approx 0.894|0\rangle - 0.447|1\rangle$$

Check: $A(|0\rangle - 0.5|1\rangle) = 0.75|0\rangle + 0|1\rangle$, which points exactly along $|b\rangle$, so $C = 0$. The eigenvalues of $A$ are 1.5 and 0.5, so $\kappa = 3$: a well-conditioned system. One RY gate can reach this state, and the optimizer finds it in a few steps.

## Common mistakes

- **Expecting the solution vector itself.** VQLS gives a normalized state $\propto x$; its overall length and individual entries need further measurements.
- **Using a singular matrix.** Without an inverse there is no unique solution, and the cost has a whole valley of zeros.
- **Ignoring the condition number.** A large κ means a flat landscape near the solution and many more measurements.

## In the app

**Algorithms → Variational quantum linear solver** sets up the standard systems or your own $A$. Press **Optimize** and open **Show the solution** to compare the circuit's amplitudes with $A^{-1}b$; the landscape shows how flat the cost becomes for the badly conditioned system.

## Check your understanding

```quiz
Q: Why is the minimum of the VQLS cost exactly the solution?
* C = 0 only when A|x⟩ points along |b⟩, which for an invertible A means |x⟩ ∝ A⁻¹|b⟩
- Because the optimizer always finds the global minimum
- Because A is unitary
E: The cost measures the part of A|x⟩ orthogonal to |b⟩; it vanishes only when A|x⟩ ∝ |b⟩.
```

```quiz
Q: A system has condition number 19 instead of 2.3. What changes?
- Nothing: the solution is exact either way
* The cost landscape is flatter, so the solve takes more optimizer steps (and, on hardware, more measurements)
- The system has no solution
E: A large condition number means A nearly loses a direction, which makes the solution harder to pin down.
```

```quiz
Q: What is the cost C at the exact solution?
* 0
- 1
- κ
E: At the solution A|x⟩ points along |b⟩, so its part orthogonal to |b⟩, which C measures, vanishes.
```

```quiz
Q: A has singular values 4 and 0.5. What is its condition number?
- 2
* 8
- 4.5
E: κ = σmax/σmin = 4/0.5 = 8.
```

## Summary

- VQLS prepares $|x\rangle \propto A^{-1}|b\rangle$ with a parameterized circuit.
- The cost $\langle x| A^\dagger(I - |b\rangle\langle b|)A |x\rangle$ is 0 exactly at the solution.
- The condition number $\kappa$ measures how hard the system is.
