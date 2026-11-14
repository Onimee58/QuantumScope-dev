---
title: "Lab: pure, mixed and entangled"
area: principles
kind: lab
order: 94
objectives: Find a maximally mixed qubit inside a pure entangled pair | Lower a state's purity with noise | Entangle two qubits with a phase alone
math: 07-tensor-products, 08-density-matrices-and-projectors
---
# Lab: pure, mixed and entangled

A qubit can be mixed for two very different reasons: because it is entangled with a partner, or because noise has disturbed it. You will create both and tell them apart with the State Inspector. Read *Density matrices and mixed states* first.

[Start with an empty 2-qubit circuit](qs:circuit?n=2&inspector=1)

```step
title: Mixed, but not noisy
text: Build a Bell pair: H on q0, then CX from q0 to q1. In the State Inspector's Reduced state tab, keep q0 only: its density matrix is I/2, purity 0.5. Keep both qubits: the pair is pure.
check: qubits 2
check: state H:0;CX:0,1
check: entangled 0
```

```step
title: Mixed because of noise
text: Drag a Depolarizing channel from the noise palette onto q1 after the CX. Now the whole pair is mixed: its purity drops below 1, and below 0.95 with a strong enough channel.
hint: Double-click the channel to change its strength.
check: noise depolarizing
check: purity <= 0.95
```

```step
title: Entangled by a phase
text: Start a new 2-qubit circuit: H on both qubits, then CZ. CZ changes no probability — all four outcomes stay at ¼ — yet each qubit is now maximally mixed: the pair is entangled.
hint: Use File → New circuit, or the link at the top of this lab.
check: state H:0;H:1;CZ:0,1
check: entangled 0
```

## What you found

Purity of the whole tells noise from entanglement: an entangled pure pair has purity 1 although each half is completely mixed, while noise lowers the purity of the whole. A sign alone, as CZ adds, can entangle.

```quiz
Q: One qubit of a pair has purity 0.5. What can you conclude?
- The device is noisy
* The qubit is maximally mixed — from entanglement with its partner, from noise, or both
- The pair is a product state
E: The single qubit's purity cannot tell the cause; the purity of the whole pair can.
```
