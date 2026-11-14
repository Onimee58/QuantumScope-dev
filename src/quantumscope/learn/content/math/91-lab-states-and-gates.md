---
title: "Lab: states, overlaps and gate products"
area: math
kind: lab
order: 91
objectives: Normalize a state and compute an overlap | Multiply gate matrices in the right order | Show that HZH = X
---
# Lab: states, overlaps and gate products

You will turn a list of amplitudes into a state, measure its overlap with another, and multiply gates as matrices — the calculations behind every circuit. Read *Vectors and Dirac notation* and *Matrices acting on states* first.

[Open the calculator](qs:open/calculator)

```step
title: Normalize
text: Evaluate normalize((1+i)|0⟩ + |1⟩). Each amplitude is divided by the length √3, so the result is ((1+i)/√3)|0⟩ + (1/√3)|1⟩.
hint: Type ⟩ with the symbol buttons, or simply write |0> with a greater-than sign.
check: calc gives [(1+i)/sqrt(3); 1/sqrt(3)]
```

```step
title: An overlap
text: How likely is this state to be found in |+⟩? Compute abs(⟨+|normalize((1+i)|0⟩ + |1⟩))^2. The worked example in the lecture gives 5/6.
check: calc gives 5/6
```

```step
title: Order matters
text: Compute X*Z and then Z*X. They differ by a sign: XZ = −ZX.
check: calc gives [0, -1; 1, 0]
check: calc gives [0, 1; -1, 0]
```

```step
title: A phase flip between Hadamards
text: Compute H*Z*H. The result is the matrix of X: a phase flip between two Hadamards is a bit flip.
check: calc typed H*Z*H
check: calc gives X
```

## What you found

States are normalized vectors, overlaps are inner products, and circuits are matrix products read right to left. HZH = X shows the Hadamard swapping the x and z directions.

```quiz
Q: What does H*X*H give?
- X
* Z
- I
E: By the same symmetry, a bit flip between Hadamards is a phase flip.
```
