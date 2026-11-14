---
title: Observables and expectation values
area: principles
kind: lecture
order: 8
objectives: Read an observable written as a sum of Pauli terms | Compute an expectation value for simple states | State the variational principle
math: 04-hermitian-and-unitary, 05-eigenvalues, 10-pauli-algebra
---
# Observables and expectation values

## The idea

So far we have measured qubits as 0 or 1. Physics and chemistry ask other questions: what is the energy of this molecule, how magnetized is this chain of spins? Each such question is an **observable**. A single measurement gives one of a few allowed values; averaging many measurements gives the **expectation value**, the number that variational algorithms try to make as small as possible.

## A quantity you could measure

An observable is a physical quantity — an energy, a magnetization, a parity. In quantum mechanics it is a Hermitian operator, and on qubits every observable can be written as a weighted sum of **Pauli terms**:

| Term | Meaning | Value for \|0⟩ | Value for \|1⟩ |
|---|---|---|---|
| $Z_k$ | is qubit $k$ 0 or 1? | +1 | −1 |
| $Z_0 Z_1$ | do q0 and q1 agree? | +1 if equal | −1 if different |
| $X_k$ | qubit $k$ along $x$ | +1 for \|+⟩ | −1 for \|−⟩ |

For example $Z_0 Z_1 + 0.5\,X_0$ adds "agreement" and half of q0's $x$-value.

## Expectation values

A single measurement gives one of the operator's eigenvalues. Averaged over many measurements of the same state $|\psi\rangle$ the result is the **expectation value**

$$\langle O \rangle = \langle \psi | O | \psi \rangle$$

For $|+\rangle$, measuring $Z$ gives +1 and −1 equally often, so $\langle Z \rangle = 0$, while $\langle X \rangle = 1$. For the Bell state $\frac{1}{\sqrt{2}}(|00\rangle + |11\rangle)$ the two qubits always agree: $\langle Z_0 Z_1 \rangle = 1$.

## The lowest possible value

No state can do better than the smallest eigenvalue $E_0$ of $O$:

$$\langle \psi | O | \psi \rangle \geq E_0 \quad \text{for every } |\psi\rangle$$

This **variational principle** is the basis of the variational algorithms in the Circuits lectures: lower ⟨O⟩ as far as possible, and you approach $E_0$. QuantumScope shows the exact $E_0$ next to ⟨O⟩, computed by diagonalizing the observable.

## Worked example

Take $O = Z_0 Z_1 + 0.5\,X_0$. Expectation values add term by term:

- For $|00\rangle$: $\langle Z_0 Z_1\rangle = 1$ and $\langle X_0\rangle = 0$, so $\langle O\rangle = 1$.
- For $|01\rangle$: the qubits differ, so $\langle O\rangle = -1 + 0 = -1$.

Is $-1$ the lowest? $Z_0 Z_1$ and $X_0$ anticommute, so $O^2 = 1 + 0.25$, and the eigenvalues of $O$ are $\pm\sqrt{1.25} \approx \pm 1.118$. The ground state does better than $|01\rangle$ by mixing in some $x$-direction for q0: $E_0 \approx -1.118$, and no state can go lower.

## Common mistakes

- **Expecting a measurement to return ⟨O⟩.** Each shot returns an eigenvalue, such as +1 or −1; only the average approaches ⟨O⟩, which can be any value between them.
- **Reading $Z_0 Z_1$ as "Z on q0, then Z on q1, then measure each".** It is one quantity, the product of the two results: +1 when they agree, −1 when they differ.
- **Thinking entanglement can beat $E_0$.** Every state, entangled or not, gives ⟨O⟩ ≥ $E_0$; entanglement can only help reach it.

## In the app

Open the circuit editor's **Parameters & observable** panel and type an observable such as `Z0 Z1 + 0.5 X0`. The panel shows ⟨O⟩ for the current circuit and the exact lowest value $E_0$ beside it. Build $|01\rangle$ with an X on q1 and compare with the worked example; then add an RY on q0 and turn its slider to see how close you can get to −1.118.

[Try it: the observable panel (a Bell pair with Z0 Z1)](qs:circuit?n=2&gates=H:0;CX:0,1&observable=Z0%20Z1)

## Check your understanding

```quiz
Q: What is ⟨Z0 Z1⟩ for |01⟩?
- +1
* −1
- 0
E: q0 = 0 and q1 = 1 differ, so Z0 Z1 gives −1 every time.
```

```quiz
Q: Can a state give ⟨O⟩ below the smallest eigenvalue of O?
- Yes, with enough entanglement
* No: the smallest eigenvalue is a lower bound for every state
E: ⟨O⟩ is a weighted average of eigenvalues, so it can never fall below the smallest one.
```

```quiz
Q: What is ⟨X⟩ for the state |0⟩?
- +1
- −1
* 0
E: |0⟩ is an equal superposition of |+⟩ and |−⟩, so measuring X gives +1 and −1 equally often.
```

```quiz
Q: A single shot measures Z on |+⟩. Which results are possible?
- Only 0, the expectation value
* +1 or −1, each half the time
- Any number between −1 and +1
E: A shot always returns an eigenvalue of Z. The expectation value 0 is the average of many shots.
```

## Summary

- Observables on qubits are weighted sums of Pauli terms.
- Each shot gives an eigenvalue; ⟨O⟩ is the average of many measurements of the same state.
- Expectation values add term by term.
- The smallest eigenvalue bounds ⟨O⟩ from below: the variational principle.
