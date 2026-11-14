---
title: Multi-qubit gates and tensor products
area: circuits
kind: lecture
order: 3
objectives: Apply a single-qubit gate inside a larger register | Read the matrices of CX, CZ, SWAP and CP | Explain why a controlled gate is not a product of two single-qubit gates
math: 03-matrices-acting-on-states, 07-tensor-products
---
# Multi-qubit gates and tensor products

## The idea

Single-qubit gates alone can never make qubits depend on each other. Multi-qubit gates can: a controlled gate acts on one qubit only when another is 1. This lecture shows how a gate on part of a register becomes a big matrix, and meets the gates — CX, CZ, SWAP, Toffoli — that every larger circuit is built from.

## A single-qubit gate in a bigger register

On two qubits, applying $H$ to q0 and nothing to q1 is the $4\times 4$ matrix $H\otimes I$. With q0 written first, the tensor product places a copy of the second factor in each entry of the first:

$$H\otimes I = \frac{1}{\sqrt{2}}\begin{pmatrix}1 & 0 & 1 & 0\\ 0 & 1 & 0 & 1\\ 1 & 0 & -1 & 0\\ 0 & 1 & 0 & -1\end{pmatrix}$$

Gates on different qubits in the same column act at the same time and their order does not matter: $(A\otimes I)(I\otimes B) = A\otimes B$.

## Controlled gates

A **controlled** gate applies an operation to a target only when the control is $|1\rangle$. The controlled-NOT, with control q0 and target q1, is

$$CX = \begin{pmatrix}1 & 0 & 0 & 0\\ 0 & 1 & 0 & 0\\ 0 & 0 & 0 & 1\\ 0 & 0 & 1 & 0\end{pmatrix}$$

It maps $|10\rangle \to |11\rangle$ and $|11\rangle \to |10\rangle$ and leaves the other basis states alone: classically, the target becomes target ⊕ control.

No matrix of the form $A\otimes B$ equals CX, because what happens to q1 depends on q0. That dependence is exactly how two-qubit gates create entanglement.

[Try it: CX in the Gate Explorer](qs:gate/CX)

## Phase-type two-qubit gates

$$CZ = \mathrm{diag}(1, 1, 1, -1), \quad CP(\lambda) = \mathrm{diag}(1, 1, 1, e^{i\lambda})$$

Both add a phase only to $|11\rangle$, so it does not matter which qubit you call the control: they are **symmetric**. CZ is CP(π). These gates are the building blocks of the quantum Fourier transform.

A useful identity links the two families: $(I\otimes H)\,CX\,(I\otimes H) = CZ$. Hadamards on the target turn a bit flip into a phase flip.

[Try it: CZ between two |+⟩ qubits](qs:circuit?n=2&gates=CZ:0,1&states=%2B,%2B&inspector=1)

## SWAP and three-qubit gates

SWAP exchanges two qubits: $|01\rangle \leftrightarrow |10\rangle$. It can be built from three CX gates with alternating directions.

On three qubits, the **Toffoli** gate CCX flips the target when both controls are 1, and the **Fredkin** gate CSWAP swaps two qubits when the control is 1. Both are reversible versions of classical logic, as the lecture on reversible logic shows.

## Worked example

SWAP from three CX gates, with directions q0→q1, q1→q0, q0→q1. Follow $|10\rangle$ (q0 = 1, q1 = 0):

$$|10\rangle \overset{CX_{0\to1}}{\longrightarrow} |11\rangle \overset{CX_{1\to0}}{\longrightarrow} |01\rangle \overset{CX_{0\to1}}{\longrightarrow} |01\rangle$$

The 1 has moved from q0 to q1. Check $|01\rangle$ the same way: it becomes $|01\rangle$, then $|11\rangle$, then $|10\rangle$. $|00\rangle$ and $|11\rangle$ are unchanged. Every basis state is swapped correctly, so the three CX gates are SWAP — which is how hardware without a native SWAP moves qubits around.

## Common mistakes

- **Confusing control and target.** In CX the target changes and the control does not; reversing them gives a different gate.
- **Writing CX as a product of single-qubit gates.** No $A \otimes B$ equals CX; that is why it can entangle.
- **Forgetting that CZ needs no direction.** Unlike CX, its two qubits play the same role.

## In the app

Drag a CX from the palette: the first drop places the target, then you pick the control. Build the three-CX SWAP from the worked example and check in the State Inspector that $|10\rangle$ comes out as $|01\rangle$; the **Gate Explorer** shows the 4 × 4 matrices of CX, CZ and SWAP.

[Try it: SWAP from three CX gates, applied to |10⟩](qs:circuit?n=2&gates=X:0;CX:0,1;CX:1,0;CX:0,1&inspector=1)

## Check your understanding

```quiz
Q: What does CX (control q0, target q1) do to |10⟩?
- Leaves it unchanged
* Changes it to |11⟩
- Changes it to |01⟩
- Multiplies it by −1
E: q0 is 1, so the target q1 is flipped from 0 to 1.
```

```quiz
Q: Why is CZ called symmetric?
* It only adds a phase to |11⟩, which treats both qubits the same way
- It is its own inverse
- Its matrix has only real entries
E: Swapping the roles of control and target leaves diag(1, 1, 1, −1) unchanged. Being its own inverse is true too, but that is a different property.
```

```quiz
Q: What does the Toffoli gate CCX (controls q0, q1; target q2) do to |110⟩?
- Leaves it unchanged
* Changes it to |111⟩
- Changes it to |010⟩
E: Both controls are 1, so the target flips from 0 to 1.
```

```quiz
Q: Hadamards on the target before and after a CX give which gate?
- SWAP
* CZ
- CX with the roles reversed
E: (I ⊗ H) CX (I ⊗ H) = CZ: the Hadamards turn the target's bit flip into a phase flip.
```

## Summary

- A gate on some qubits of a register is a tensor product with identities on the others.
- Controlled gates act on a target depending on a control and cannot be written as a product of single-qubit gates.
- CZ and CP add a phase to |11⟩ and are symmetric; SWAP, CCX and CSWAP complete the gate set.
