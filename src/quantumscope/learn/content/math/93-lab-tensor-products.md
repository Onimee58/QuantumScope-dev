---
title: "Lab: tensor products and entanglement"
area: math
kind: lab
order: 93
objectives: Build two-qubit states with ⊗ | Make a Bell state with matrices | Measure entanglement with the partial trace and purity
---
# Lab: tensor products and entanglement

You will build two-qubit states from single-qubit ones, make a Bell state with the same matrices a circuit uses, and show that each half of it is completely random. Read *Tensor products* and *Outer products, projectors and density matrices* first.

[Open the calculator](qs:open/calculator)

```step
title: A product state
text: Evaluate |+⟩ ⊗ |0⟩. Only |00⟩ and |10⟩ appear, each with amplitude 1/√2: the first qubit is in a superposition, the second is 0.
check: calc typed ⊗
check: calc gives [1; 0; 1; 0]/sqrt(2)
```

```step
title: A Bell state from matrices
text: Evaluate CNOT (H ⊗ I)|00⟩ — the circuit "H on q0, then CX" written as matrices. The result is (|00⟩ + |11⟩)/√2.
check: calc gives [1; 0; 0; 1]/sqrt(2)
```

```step
title: Each half is random
text: Compute purity(ptrace(CNOT (H ⊗ I)|00⟩, 1)): trace out qubit 1 and measure what is left. Purity ½ means q0 alone is completely random.
check: calc typed ptrace(
check: calc gives 1/2
```

```step
title: A product has pure halves
text: Now compute purity(ptrace(|+⟩ ⊗ |0⟩, 1)). The result is 1: in a product state each qubit has a definite state of its own.
check: calc typed purity(ptrace(|+⟩
check: calc gives 1
```

## What you found

A tensor product of two states has pure halves; the Bell state does not factor, and its halves are maximally mixed. The partial trace and purity turn "entangled" into a number.

```quiz
Q: What is the purity of one qubit of a GHZ state (|000⟩ + |111⟩)/√2?
- 1
* 1/2
- 1/4
E: Tracing out the other two leaves an equal mixture of |0⟩ and |1⟩, purity ½.
```
