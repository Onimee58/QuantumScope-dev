---
title: "Lab: an exact gradient from two circuits"
area: math
kind: lab
order: 95
objectives: Compute an expectation value of a rotated state | Apply the parameter-shift rule | Compare it with the exact derivative
---
# Lab: an exact gradient from two circuits

Variational algorithms need slopes. You will compute the slope of ⟨Z⟩ for a rotated qubit with the parameter-shift rule — two evaluations, no approximation — and compare it with calculus. Read *Gradients and optimization* first.

[Open the calculator](qs:open/calculator)

```step
title: The value at θ = π/3
text: Evaluate expect(Z, RY(pi/3)|0⟩). The result is cos(π/3) = 1/2.
check: calc typed expect(Z, RY(pi/3)
check: calc gives 1/2
```

```step
title: The parameter-shift rule
text: Evaluate (expect(Z, RY(pi/3 + pi/2)|0⟩) - expect(Z, RY(pi/3 - pi/2)|0⟩))/2. The two shifted values give the exact derivative −√3/2 ≈ −0.866.
check: calc gives -sqrt(3)/2
check: calc typed pi/3 + pi/2
```

```step
title: Compare with calculus
text: The derivative of cos θ is −sin θ. Evaluate -sin(pi/3): the same −√3/2, with no rounding error.
check: calc typed sin(pi/3)
```

```step
title: At the bottom of the valley
text: Repeat the parameter-shift rule at θ = π, where cos θ has its minimum −1. The slope is 0: gradient descent would stop here.
check: calc typed pi + pi/2
check: calc gives 0
```

## What you found

Two evaluations at θ ± π/2 give the exact derivative of any expectation value of a rotation gate — which is how a quantum computer measures gradients for VQE, QAOA and Quantum ML.

```quiz
Q: With step size 0.5, one gradient-descent step from θ = π/3 moves θ to what?
* About 1.48
- About 0.61
- π
E: θ − η f′(θ) = 1.047 − 0.5 × (−0.866) ≈ 1.480: downhill, toward π.
```
