---
title: Classical control, feed-forward and reset
area: circuits
kind: lecture
order: 13
objectives: Condition a gate on a classical bit | Reset a qubit with measurement and feed-forward | Explain when the order of operations in a column matters
math: 06-probability
---
# Classical control, feed-forward and reset

## The idea

A measurement result is only useful if the circuit can act on it. **Feed-forward** does exactly that: later gates run or not depending on a classical bit. With it, a circuit can reset qubits for reuse, correct errors, and complete protocols such as teleportation.

## Gates that depend on a measurement

A **classically controlled** gate runs only when a classical bit has a given value — "apply X to q2 if c1 = 1". Using measurement results later in the same run is called **feed-forward**. In QuantumScope, right-click any gate and choose **Run only if… → c1 = 1**; the gate shows a **c1=1** badge.

Within one column, gates act first and measurements after, so a condition always uses results from *earlier* columns.

## Reset by feed-forward

Measuring a qubit and then applying X if the result was 1 leaves it in $|0\rangle$ whatever it was before:

| Measured | Then | Result |
|---|---|---|
| 0 | nothing | \|0⟩ |
| 1 | X | \|0⟩ |

This **active reset** lets a circuit reuse a qubit, for example as a fresh work qubit. QuantumScope's **Reset** element does the same in one step, $\rho \rightarrow |0\rangle\langle 0|$ on that qubit, without recording a bit.

[Try it: reset |+⟩ by measurement and feed-forward](qs:circuit?n=1&gates=X:0&cols=1&states=%2B&measures=0:0:0&conditions=0:1:0:1&inspector=1)

## Why feed-forward is hard on real hardware

The measurement result has to be read, processed classically and used to control a gate while the other qubits wait — and waiting qubits decohere. Fast classical control is one of the engineering challenges of real quantum computers, and one reason the deferred-measurement principle (a later lecture) is useful.

## Worked example

Measure q0 of a Bell pair into c0, then apply X to **q1** only if c0 = 1.

- Result 0 (probability ½): both qubits are 0; nothing happens. q1 = 0.
- Result 1 (probability ½): both qubits are 1; the X flips q1 to 0.

q1 ends in $|0\rangle$ in every branch: the correlation has been used to reset a qubit that was never measured itself. The same idea, with the right corrections, is what makes teleportation work.

## Common mistakes

- **Conditioning on a later column.** A condition uses results from earlier columns; within a column, gates act before measurements.
- **Thinking a conditional gate is a controlled gate.** CX is controlled by a qubit in superposition; feed-forward uses a classical bit that is already 0 or 1.
- **Forgetting the cost on hardware.** Feed-forward makes the other qubits wait for classical processing, and waiting qubits decohere.

## In the app

Right-click any gate and choose **Run only if… → c0 = 1**; the gate shows a badge. The State Inspector's **Branches** tab confirms the result in each branch. **Reset** in the Classical palette does the measure-and-flip in one step.

[Try it: Bell pair, measure q0, flip q1 if c0 = 1](qs:circuit?n=2&gates=H:0;CX:0,1;X:1&cols=0,1,3&measures=0:2:0&conditions=1:3:0:1&inspector=1)

## Check your understanding

```quiz
Q: A qubit is measured into c0, and then X is applied if c0 = 1. What is the final state?
- The same state as before the measurement
* |0⟩, whatever the starting state
- |1⟩
E: Outcome 0 leaves |0⟩; outcome 1 leaves |1⟩, which X turns into |0⟩.
```

```quiz
Q: A conditioned gate and the measurement it depends on are in the same column. What happens?
- The gate uses the new result
* The gate uses the bit's earlier value, because gates act before measurements in a column
- The circuit is rejected
E: Within a column, gates come first; put the conditioned gate in a later column to use the new result.
```

```quiz
Q: A qubit is measured into c0 and then X is applied only if c0 = 1. What is the qubit's state afterwards?
* |0⟩, whatever it was before
- The same state as before the measurement
- |1⟩
E: A result of 0 leaves |0⟩; a result of 1 leaves |1⟩, which the X turns into |0⟩: an active reset.
```

```quiz
Q: What is the difference between CX and "X if c0 = 1"?
- None
* CX is controlled by a qubit, possibly in superposition; the conditional X by a classical bit already measured
- CX acts on classical bits
E: A controlled gate can entangle; a classically conditioned gate acts on one definite branch at a time.
```

## Summary

- Classically controlled gates run only for a chosen value of a classical bit: feed-forward.
- Measurement plus a conditional X resets any qubit to |0⟩; Reset does it in one step.
- Fast classical control is demanding for real hardware.
