---
title: Entanglement in circuits
area: circuits
kind: lecture
order: 4
objectives: Build the four Bell states and a GHZ state | Decide whether a two-qubit state is entangled | Use the reduced state and its entropy as an entanglement measure
math: 07-tensor-products
---
# Entanglement in circuits

## The idea

Two gates — a Hadamard and a CX — are enough to make two qubits share one state that cannot be split into a state for each. That is **entanglement**, the resource behind teleportation, superdense coding, error correction and most quantum algorithms. This lecture shows how circuits create it, how to test for it, and how to measure how much there is.

## The Bell states

A Hadamard followed by a CX turns $|00\rangle$ into

$$|\Phi^+\rangle = \frac{1}{\sqrt{2}}(|00\rangle + |11\rangle)$$

Starting from the other three basis states gives the other **Bell states**:

| Start | Result |
|---|---|
| \|00⟩ | (\|00⟩ + \|11⟩)/√2 |
| \|01⟩ | (\|01⟩ + \|10⟩)/√2 |
| \|10⟩ | (\|00⟩ − \|11⟩)/√2 |
| \|11⟩ | (\|01⟩ − \|10⟩)/√2 |

[Try it: the Bell pair](qs:circuit?n=2&gates=H:0;CX:0,1&inspector=1)

## What makes a state entangled

A two-qubit state is a **product state** if it can be written as $|a\rangle\otimes|b\rangle$; otherwise it is **entangled**. For $|\psi\rangle = c_{00}|00\rangle + c_{01}|01\rangle + c_{10}|10\rangle + c_{11}|11\rangle$ there is a quick test:

$$|\psi\rangle \text{ is a product state} \Leftrightarrow c_{00}c_{11} - c_{01}c_{10} = 0$$

For $|\Phi^+\rangle$, $c_{00}c_{11} = \frac{1}{2}$ while $c_{01}c_{10} = 0$, so it is entangled.

## Measuring entanglement with the reduced state

Ignoring q1 leaves q0 in a **reduced density matrix** $\rho_0$. For a product state, $\rho_0$ is pure; for an entangled state it is mixed. The **entanglement entropy**

$$S = -\mathrm{Tr}\,\rho_0 \log_2 \rho_0$$

is 0 for a product state and 1 bit for a Bell state, the maximum for one qubit. The State Inspector's **Reduced state** tab shows $\rho$, its purity and $S$.

## GHZ states

Adding a second CX spreads the entanglement to a third qubit:

$$|GHZ\rangle = \frac{1}{\sqrt{2}}(|000\rangle + |111\rangle)$$

Every single qubit of a GHZ state has entropy 1 bit, and so does every pair. Measuring any one qubit fixes the other two.

[Try it: GHZ with the State Inspector](qs:example/GHZ?inspector=1)

## Worked example

Start from $|10\rangle$: X on q0, then H on q0, then CX. The Hadamard turns q0's $|1\rangle$ into $|-\rangle$:

$$|10\rangle \to \frac{1}{\sqrt{2}}(|00\rangle - |10\rangle) \to \frac{1}{\sqrt{2}}(|00\rangle - |11\rangle) = |\Phi^-\rangle$$

as in the table. Now a *partly* entangled state: replace H by $R_Y(\pi/3)$, giving $\cos\frac{\pi}{6}|00\rangle + \sin\frac{\pi}{6}|11\rangle$. The reduced state of q0 has eigenvalues 0.75 and 0.25, so

$$S = -0.75\log_2 0.75 - 0.25\log_2 0.25 \approx 0.81 \text{ bits}$$

less than the Bell state's 1 bit, more than a product state's 0.

## Common mistakes

- **Calling every correlated state entangled.** A random mix of $|00\rangle$ and $|11\rangle$ is correlated but not entangled; the test needs the amplitudes of a pure state.
- **Thinking CX alone entangles.** On $|00\rangle$ it does nothing; the control must be in a superposition first.
- **Reading 1 bit of entropy as "one qubit is measured".** It means the qubit is maximally entangled with the rest.

## In the app

Build H then CX and open the State Inspector's **Reduced state** tab: keep q0 only to see $\rho = I/2$, purity 0.5 and entropy 1 bit. Change the H to an RY and turn its angle to watch the entropy move between 0 and 1. The GHZ example spreads the same entanglement over three qubits.

[Try it: a partly entangled pair](qs:circuit?n=2&gates=RY:0:pi/3;CX:0,1&inspector=1)

## Check your understanding

```quiz
Q: Is (|00⟩ + |01⟩)/√2 entangled?
- Yes
* No, it is |0⟩ ⊗ |+⟩
E: c00·c11 − c01·c10 = 0 − 0 = 0. The state factors as |0⟩ ⊗ (|0⟩ + |1⟩)/√2.
```

```quiz
Q: What is the entanglement entropy of one qubit of a Bell pair?
- 0 bits
- ½ bit
* 1 bit
- 2 bits
E: Its reduced state is I/2, maximally mixed, with entropy 1 bit.
```

```quiz
Q: Which input does H on q0 followed by CX turn into (|01⟩ + |10⟩)/√2?
- |00⟩
* |01⟩
- |10⟩
- |11⟩
E: From |01⟩, H gives (|01⟩ + |11⟩)/√2, and CX flips q1 when q0 is 1: (|01⟩ + |10⟩)/√2.
```

```quiz
Q: CX is applied to |00⟩ with no gate before it. Is the result entangled?
* No: the control is |0⟩, so nothing happens
- Yes: CX always entangles
- Only if measured
E: CX acts on |00⟩ as the identity. Entanglement needs the control in a superposition.
```

## Summary

- H then CX creates a Bell state; different inputs give the four Bell states.
- A state is entangled when it is not a product; for two qubits, c00·c11 − c01·c10 ≠ 0.
- The reduced state's entropy measures entanglement: 0 for product states, 1 bit for Bell states.
