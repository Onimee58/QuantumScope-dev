---
title: The variational quantum eigensolver
area: circuits
kind: lecture
order: 24
objectives: Explain how VQE finds a ground-state energy | Run VQE for the H₂ molecule | Recognize when a circuit cannot express the ground state
math: 05-eigenvalues, 10-pauli-algebra, 12-gradients-and-optimization
---
# The variational quantum eigensolver

## The idea

Many problems in chemistry and physics ask for the **ground-state energy** $E_0$ of a Hamiltonian $H$ — the smallest eigenvalue. The variational principle says $\langle H \rangle \geq E_0$ for every state, so:

1. Prepare a state with a parameterized circuit (the **ansatz**).
2. Measure $\langle H \rangle$.
3. Let a classical optimizer adjust the parameters to lower it, and repeat.

The quantum computer prepares states that may be hard to describe classically; the classical computer steers. VQE was introduced by Peruzzo and colleagues in 2014.

## H₂

QuantumScope's VQE example includes the hydrogen molecule at a bond length of 0.735 Å, reduced to two qubits. Its exact ground energy is

$$E_0 = -1.137306 \text{ Hartree}$$

and one layer of RY rotations with a CX already reaches it.

[Try it: VQE for H₂ — press Optimize](qs:algorithm/vqe?problem=h2&layers=1)

## Expressibility

The ansatz decides which states can be reached. For a 3-spin Heisenberg chain ($E_0 = -4$), one entangling layer gets no lower than $-(1 + 2\sqrt{2}) \approx -3.83$, however well it is optimized; two layers reach −4 exactly. When the optimizer stops above the exact value, the circuit may simply be unable to represent the ground state.

[Try it: the Heisenberg chain with one layer](qs:algorithm/vqe?problem=heisenberg-3&layers=1)

## Worked example

The H₂ Hamiltonian is a sum of five Pauli terms. Its basis state $|01\rangle$ (q0 = 0, so $Z_0 = +1$; q1 = 1, so $Z_1 = -1$) is the chemists' Hartree–Fock state, with

$$\langle H\rangle = -0.332404 - 0.397938 - 0.397938 + 0.011280 \approx -1.116998 \text{ Hartree}$$

(the $X_0X_1$ term averages to 0 on a basis state). The ansatz mixes in a little $|10\rangle$, which the $X_0X_1$ term couples to $|01\rangle$, and the energy falls to $-1.137306$. The difference, about 0.020 Hartree or 13 kcal/mol, is the **correlation energy**: small, but chemistry needs it to about 1 kcal/mol.

## Common mistakes

- **Reading a VQE result as exact.** Every value is an upper bound; it equals $E_0$ only if the ansatz can reach the ground state and the optimizer finds it.
- **Blaming the optimizer for an expressibility limit.** If the best possible state is too simple, no optimizer can go lower; add a layer.
- **Forgetting that ⟨H⟩ is estimated from shots on hardware.** Each value carries statistical error, which the next lectures address.

## In the app

**Algorithms → VQE** builds the ansatz and the Hamiltonian for H₂, Ising and Heisenberg chains. Press **Optimize** in the **Parameters & observable** panel: ⟨H⟩ falls toward the exact $E_0$ shown beside it. Try the Heisenberg chain with one layer, then two, to see expressibility at work.

## Check your understanding

```quiz
Q: VQE reports ⟨H⟩ = −1.10 for H₂. What do you know about the true ground energy?
* It is at most −1.10
- It is exactly −1.10
- It is at least −1.10
E: By the variational principle every ⟨H⟩ is an upper bound on E₀.
```

```quiz
Q: The optimizer converges 0.17 above the exact energy. What is a sensible next step?
- Run the same optimizer longer
* Add layers to the ansatz, so it can represent more states
- Lower the exact energy
E: If the circuit cannot represent the ground state, no optimizer can reach it.
```

```quiz
Q: A VQE run stops at ⟨H⟩ = −3.83 for a problem with E₀ = −4. What could explain it?
* The ansatz cannot represent the ground state, or the optimizer is stuck in a local minimum
- The variational principle is violated
- The answer is −3.83, and E₀ is wrong
E: ⟨H⟩ ≥ E₀ always holds; stopping above E₀ points to the circuit's limits or to a local valley.
```

```quiz
Q: What does the classical computer do in VQE?
- It prepares the quantum state
* It chooses new parameters to lower the measured ⟨H⟩
- It computes E₀ exactly
E: The quantum computer prepares states and measures ⟨H⟩; the classical optimizer steers the parameters.
```

## Summary

- VQE lowers ⟨H⟩ over a parameterized circuit; every value is an upper bound on E₀.
- H₂ at 0.735 Å: E₀ = −1.137306 Hartree, reached with one layer.
- Too simple an ansatz stops above E₀: expressibility matters.
