---
title: The deferred-measurement principle
area: circuits
kind: lecture
order: 16
objectives: State the deferred-measurement principle | Rewrite feed-forward with quantum controls | Judge when mid-circuit measurement is really needed
math: 07-tensor-products
---
# The deferred-measurement principle

## The idea

Measuring a qubit and then acting on the result looks very different from a quantum-controlled gate — but for the final statistics they are the same. This principle lets any circuit postpone all measurements to the end, which matters for hardware without fast feed-forward and for reasoning about circuits.

## The principle

A measurement followed by a gate controlled by its result has exactly the same effect as a **quantum** controlled gate followed by the measurement:

$$\text{measure } q_a \text{ then (if } c = 1\text{) } U \text{ on } q_b \quad\equiv\quad CU_{a \rightarrow b} \text{ then measure } q_a$$

Measurements can therefore always be moved to the end of a circuit, replacing classical control by quantum control.

## Teleportation without feed-forward

Replace Bob's corrections "X if c1 = 1" and "Z if c0 = 1" by a CX from q1 to q2 and a CZ from q0 to q2. No measurement is needed mid-circuit at all, and q2 still ends in the input state — although now Alice's and Bob's qubits stay entangled until the final measurement.

[Try it: teleportation with quantum controls](qs:circuit?n=3&gates=H:1;CX:1,2;CX:0,1;H:0;CX:1,2;CZ:0,2&states=%2Bi,0,0&inspector=1)

## What the principle does — and does not — say

- **It does:** any circuit's final measurement statistics can be produced with all measurements at the end. Hardware without fast feed-forward can still run such algorithms.
- **It does not** say feed-forward is useless. The deferred version needs the measured qubits to stay coherent until the end, and it cannot *reuse* a qubit after measuring and resetting it. In teleportation it also needs Alice's and Bob's qubits to interact directly — impossible if they are far apart. Error correction relies on genuine mid-circuit measurement for the same reasons.

## Worked example

q0 is in $|+\rangle$, q1 in $|0\rangle$. Compare:

- **Measure, then control:** measure q0 (0 or 1, half the time each), then apply X to q1 if the result is 1. Final readouts: 00 or 11, half the time each.
- **Control, then measure:** apply CX from q0 to q1, giving $\frac{1}{\sqrt{2}}(|00\rangle + |11\rangle)$, then measure both. Final readouts: 00 or 11, half the time each.

The statistics agree. The difference is in between: in the second version the qubits are entangled until the end, so q0 must stay coherent that long.

## Common mistakes

- **Concluding that mid-circuit measurement is never needed.** Reuse of qubits, distant parties and error correction still need it.
- **Moving a measurement without changing the classical control.** The conditioned gate must become the matching quantum-controlled gate.
- **Expecting the same intermediate state.** Only the final statistics agree; the deferred circuit keeps more entanglement along the way.

## In the app

Compare the **Quantum teleportation** example (mid-circuit measurements and conditional gates) with the link below, which replaces the corrections by CX and CZ. The State Inspector shows q2 ending in the input state in both; the Branches tab is empty in the deferred version, because nothing is measured mid-circuit.

## Check your understanding

```quiz
Q: By the deferred-measurement principle, "measure q0, then X on q1 if the result is 1" equals …
- X on q1, then measure q0
* CX from q0 to q1, then measure q0
- Measure q1, then X on q0
E: The classical control becomes a quantum control from the qubit that would have been measured.
```

```quiz
Q: Why is real teleportation still done with mid-circuit measurement?
- The deferred version gives a different result
* The deferred version needs a direct quantum interaction between Alice's and Bob's distant qubits
- QuantumScope cannot simulate CZ
E: The CX and CZ would have to act across the distance; classical bits can travel instead.
```

```quiz
Q: A circuit measures q0 and then applies Z to q1 if the result is 1. What is the deferred version?
* CZ from q0 to q1, then measure q0
- Z on q1, then measure q0
- Measure q1 instead
E: The classically conditioned Z becomes a quantum-controlled Z, and the measurement moves after it.
```

```quiz
Q: Why can't distant Alice and Bob use the deferred version of teleportation?
- It needs more classical bits
* Their qubits would have to interact directly through quantum-controlled gates
- It gives a different final state
E: Replacing the corrections by CX and CZ needs a gate between Alice's and Bob's qubits, impossible when they are far apart.
```

## Summary

- Measure-then-control equals control-then-measure.
- All measurements can be moved to the end, at the cost of keeping qubits coherent longer.
- Mid-circuit measurement remains essential for qubit reuse, distributed protocols and error correction.
