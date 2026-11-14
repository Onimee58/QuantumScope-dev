---
title: Mid-circuit measurement and classical bits
area: circuits
kind: lecture
order: 12
objectives: Measure a qubit in the middle of a circuit and store the result | Describe the branches a measurement creates | Explain why the averaged state is a density matrix
math: 06-probability, 08-density-matrices-and-projectors
---
# Mid-circuit measurement and classical bits

## The idea

Until now, measurement ended the circuit. Many protocols need to measure in the middle, keep the result as a classical bit, and carry on. Doing so splits the computation into branches — one per possible result — and, if nobody reads the result, it quietly destroys the interference that the circuit might have needed.

## Two kinds of measurement

So far, measurement came at the very end: the **M** gates read out the final state. Many protocols need more: they measure *during* the circuit and use the result later. QuantumScope's **M→c** (in the Classical palette) measures a qubit at any point and stores the result in a **classical bit** c0, c1, …

| | M | M→c |
|---|---|---|
| Where | at the end only | anywhere |
| Result | the final readout (histogram) | stored in a classical bit for later use |
| Afterwards | nothing | the circuit continues with the collapsed qubit |

## Branches

Measuring q0 of $\alpha|0\rangle + \beta|1\rangle$ gives 0 with probability $|\alpha|^2$ and 1 with probability $|\beta|^2$, and the qubit collapses to the outcome. A circuit with mid-circuit measurements therefore splits into **branches**, one per possible record of the classical bits:

$$\rho \rightarrow \sum_{m} p_m\,\rho_m, \qquad p_m = \mathrm{Tr}(P_m\,\rho\,P_m), \quad \rho_m = \frac{P_m\,\rho\,P_m}{p_m}$$

where $P_0 = |0\rangle\langle 0|$ and $P_1 = |1\rangle\langle 1|$ act on the measured qubit. QuantumScope follows every branch exactly — the State Inspector's **Branches** tab lists each record, its probability, and the state in that branch.

## The averaged state

Someone who does not look at the classical bits describes the system by the average over the branches, $\sum_m p_m \rho_m$. Measuring and *forgetting* the result is a channel: it removes the coherences between $|0\rangle$ and $|1\rangle$ of the measured qubit — exactly phase damping with $\lambda = 1$. That is why a circuit with mid-circuit measurements is shown as a mixed state.

[Try it: a Bell pair with q0 measured mid-circuit](qs:circuit?n=2&gates=H:0;CX:0,1&measures=0:2:0&inspector=1)

In the Branches tab, the two records each have probability ½, and in each branch q1 has collapsed to the same value as q0: the measurement on q0 fixed q1 too.

## Worked example

H, then H, on $|0\rangle$ gives $|0\rangle$ with certainty: the second H undoes the first. Now put an **M→c** between them.

- With probability ½ the measurement gives 0: the qubit is $|0\rangle$, and the second H makes $|+\rangle$, which reads 0 or 1 at random.
- With probability ½ it gives 1: the qubit is $|1\rangle$, and H makes $|-\rangle$, again 50:50.

Overall $P(0) = \frac{1}{2}$ instead of 1. The measurement removed the coherence between $|0\rangle$ and $|1\rangle$ that the second H needed to interfere back to $|0\rangle$.

## Common mistakes

- **Using M where M→c is meant.** M is the final readout; only M→c stores a result for later gates.
- **Expecting a mid-circuit measurement to leave superpositions intact.** The measured qubit collapses in every branch.
- **Reading the averaged state as one branch.** The density matrix is the average; each branch is a definite record with its own state.

## In the app

Take **M→c** from the Classical palette and drop it anywhere on a wire. The State Inspector's **Branches** tab lists each classical record with its probability, purity and per-qubit Bloch vectors. Build the worked example (H, M→c, H) and compare it with plain H, H.

[Try it: H, measure mid-circuit, H](qs:circuit?n=1&gates=H:0;H:0&cols=0,2&measures=0:1:0&inspector=1)

## Check your understanding

```quiz
Q: q0 is in |+⟩ and is measured mid-circuit into c0. How many branches are there afterwards?
- 1
* 2
- 4
E: The result is 0 or 1, each with probability ½: two classical records, two branches.
```

```quiz
Q: What is the averaged state of a |+⟩ qubit after it is measured and the result is ignored?
- |+⟩
- |0⟩
* The maximally mixed state I/2
E: Each outcome has probability ½, and averaging |0⟩⟨0| and |1⟩⟨1| gives I/2: the coherence is gone.
```

```quiz
Q: H, a mid-circuit measurement, then H act on |0⟩. What is P(0) at the end?
- 1
* 1/2
- 0
E: The measurement collapses the qubit to |0⟩ or |1⟩; the second H then gives |+⟩ or |−⟩, each read 50:50.
```

```quiz
Q: Three qubits are measured mid-circuit into c0, c1, c2. At most how many branches can there be?
- 3
- 6
* 8
E: Each record of three classical bits is a branch: 2³ = 8 possible records.
```

## Summary

- M→c measures mid-circuit and stores the result in a classical bit; M remains the final readout.
- Each possible classical record is a branch with its own probability and state.
- Averaging over unread results gives a density matrix: measurement acts like complete dephasing.
