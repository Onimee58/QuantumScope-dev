---
title: "Lab: reveal a hidden phase"
area: principles
kind: lab
order: 93
objectives: Show that a relative phase changes nothing until interference | Predict P(0) = cos²(φ/2) for H, phase, H | Check that a global phase changes nothing at all
math: 01-complex-numbers
---
# Lab: reveal a hidden phase

A phase gate between two Hadamards is an interferometer on one qubit. You will see the phase stay invisible after the first H and decide everything after the second. Read *Global and relative phase* first.

[Start with an empty 1-qubit circuit](qs:circuit?n=1&inspector=1)

```step
title: An invisible phase
text: Place H, then Z, on q0. Open the State Inspector: the probabilities are still 50:50, although Z changed the state from |+⟩ to |−⟩.
check: qubits 1
check: state H:0;Z:0
```

```step
title: Make it visible
text: Add a second H after the Z. The qubit now gives 1 with certainty: the two paths to |0⟩ cancel.
check: state H:0;Z:0;H:0
check: probability 1=1
```

```step
title: A smaller phase
text: Replace the Z with T (a phase of π/4). The State Inspector shows P(0) = cos²(π/8) ≈ 0.854.
hint: Right-click the Z and delete it, then drag a T into its place.
check: state H:0;T:0;H:0
check: uses T
```

```step
title: A global phase does nothing
text: Replace the T with RZ and set its angle to π (double-click the gate). RZ(π) is Z times the global phase −i, so the qubit gives 1 with certainty, exactly as with Z.
check: uses RZ
check: probability 1=1
check: gates <= 3
```

## What you found

A relative phase is invisible to a measurement in the z basis, and decisive once a Hadamard makes the two components interfere: P(0) = cos²(φ/2). A global phase is invisible to every measurement.

```quiz
Q: Which phase φ between the two Hadamards gives P(0) = 1/2?
- 0
* π/2
- π
E: cos²(π/4) = 1/2. That is the S gate.
```
