---
title: "Lab: complex numbers and interference"
area: math
kind: lab
order: 90
objectives: Multiply complex numbers and take moduli | Use e^{iφ} as a rotation | Compute the interference of two amplitudes
---
# Lab: complex numbers and interference

Every probability in quantum mechanics is a modulus squared of a complex amplitude, and every interference effect is two amplitudes adding at an angle. You will do both in the calculator. Read *Complex numbers* first.

[Open the calculator](qs:open/calculator)

```step
title: Multiply
text: Type (1+2i)(3-i) and press Enter. Check the result, 5 + 5i, by hand with i² = −1.
check: calc typed (1+2i)(3-i)
check: calc gives 5+5i
```

```step
title: A probability from an amplitude
text: The amplitude (1 + i)/2 gives the probability |(1 + i)/2|². Compute it with abs(...)^2. The answer, 1/2, is real and between 0 and 1, as a probability must be.
check: calc typed abs(
check: calc gives 1/2
```

```step
title: Euler's formula
text: Evaluate exp(i*pi). The point e^{iπ} is half a turn around the unit circle: −1.
check: calc gives -1
check: calc typed exp(
```

```step
title: Two paths that cancel
text: Two paths of amplitude ½ meet with a phase difference φ. Compute abs(1/2 + exp(i*pi)/2)^2 for φ = π, then abs(1/2 + exp(i*pi/2)/2)^2 for φ = π/2.
hint: The lecture's formula is (2 + 2cos φ)/4.
check: calc gives 0
check: calc typed exp(i*pi/2)
```

## What you found

Multiplying by e^{iφ} turns a number without changing its size, and adding two amplitudes at an angle φ gives a probability between 0 (opposite) and the full sum (aligned): interference.

```quiz
Q: What does abs(1/2 + exp(i*pi/3)/2)^2 give?
* 3/4
- 1/2
- 1
E: (2 + 2cos(π/3))/4 = (2 + 1)/4 = 3/4.
```
