---
title: "Circuit cost: depth, T-count and Clifford gates"
area: circuits
kind: lecture
order: 10
objectives: Distinguish gate count, depth and minimum depth | Explain why T gates are expensive in fault-tolerant computing | Identify Clifford gates
math: 03-matrices-acting-on-states
---
# Circuit cost: depth, T-count and Clifford gates

## The idea

Two circuits can compute the same thing at very different cost. On real hardware the cost is time and noise: every layer of gates gives qubits more time to decay, and some gates are far more expensive than others. A few standard measures — gate counts, depth, and the T-count — let you compare circuits and make them cheaper.

## Counting gates

The simplest cost is the number of gates, with two-qubit gates usually weighted more heavily: on real hardware they are slower and noisier than single-qubit gates.

## Depth

**Depth** counts layers: gates on different qubits can run at the same time. QuantumScope reports two depths in the State Inspector's Circuit tab:

- **Drawn depth:** the occupied columns, as you laid out the circuit.
- **Minimum depth:** the fewest layers if every gate ran as early as possible.

A large gap means the drawing spreads out gates that could run in parallel. Depth matters because qubits lose their quantum information over time, so shallower circuits suffer less noise.

## Clifford gates and the T gate

**Clifford gates** map Pauli operators to Pauli operators. They include H, S, X, Y, Z, CX, CZ and SWAP. Circuits made only of Clifford gates can be simulated efficiently on a classical computer, so they cannot give a quantum speed-up on their own.

Adding the **T gate** ($\pi/4$ phase) makes the gate set universal. In error-corrected (fault-tolerant) computers, T gates are by far the most expensive to implement, so the **T-count** — the number of T and T† gates — is a standard cost measure. A Toffoli needs 7 T gates in its standard decomposition.

[Try it: Grover's circuit statistics](qs:algorithm/grover?n=3&marked=101&iterations=-1&inspector=1)

Open the Circuit tab to see gate counts, depths and Clifford counts. Collapsed blocks never hide their real gates in these statistics.

## Making circuits cheaper

**Tools → Simplify circuit** removes gates that cancel (such as H·H or S·S†) and merges consecutive rotations, verifying that the circuit's unitary is unchanged.

## Worked example

A circuit on three qubits: H on q0, H on q1, X on q2, then CX from q0 to q1, drawn in four separate columns.

- Gate count 4, of which one two-qubit gate.
- Drawn depth 4, but minimum depth 2: H, H and X can all run in the first layer, and the CX in the second.
- All four gates are Clifford gates, so the T-count is 0 and a classical computer can simulate the circuit efficiently, however many qubits it had.

Add one Toffoli and the picture changes: its standard decomposition uses 6 CX gates and 7 T gates, so the T-count jumps from 0 to 7.

## Common mistakes

- **Counting columns as depth.** The drawn depth depends on your layout; the minimum depth is what the hardware needs.
- **Weighting all gates equally.** Two-qubit gates are typically ten times noisier than single-qubit ones, and T gates dominate fault-tolerant cost.
- **Assuming more qubits means a quantum advantage.** A Clifford-only circuit on 100 qubits is still easy to simulate classically.

## In the app

Open the State Inspector's **Circuit** tab for gate counts, two-qubit counts, drawn and minimum depth, Clifford counts and the T-count; collapsed blocks never hide their real gates. Build the worked example and compare its two depths, then try **Tools → Simplify circuit** on a circuit with H·H or S·S† in it.

## Check your understanding

```quiz
Q: Which gate is NOT a Clifford gate?
- H
- S
- CX
* T
E: T is a π/4 phase; it maps X to a combination that is not a Pauli operator. It makes the gate set universal.
```

```quiz
Q: Four single-qubit gates act on four different qubits in four different columns. What is the minimum depth?
* 1
- 2
- 4
E: They act on different qubits, so they can all run in the same layer.
```

```quiz
Q: A circuit has drawn depth 10 but minimum depth 4. What does that tell you?
* Many gates could run in parallel; the layout spreads them out
- The circuit has 6 redundant gates
- The circuit is noisy
E: Minimum depth packs every gate as early as possible. The gap comes from the layout, not from extra gates.
```

```quiz
Q: Why is the T-count, rather than the CX count, the main cost in a fault-tolerant computer?
- T gates act on more qubits
* Error-corrected T gates need costly extra resources, while Clifford gates are cheap
- T gates cannot be simulated
E: In common error-correcting codes, Clifford gates are cheap to implement, while each T gate needs an expensive procedure such as magic-state distillation.
```

## Summary

- Costs include gate counts, two-qubit gate counts and depth; minimum depth packs parallel gates.
- Clifford circuits are classically simulable; T gates add universality and dominate fault-tolerant cost.
- Simplify removes redundant gates without changing the unitary.
