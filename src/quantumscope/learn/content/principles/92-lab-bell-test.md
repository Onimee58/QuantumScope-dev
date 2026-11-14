---
title: "Lab: run a Bell test"
area: principles
kind: lab
order: 92
objectives: Measure the correlation of an entangled pair | Beat the classical CHSH limit | Find how much noise destroys the violation
math: 06-probability, 07-tensor-products
---
# Lab: run a Bell test

You will send entangled electron pairs to Alice and Bob, measure their correlation, and then test Bell's inequality: can any pre-arranged plan explain the results? Read *Entanglement and Bell states* first.

[Open the Entanglement experiment](qs:open/entanglement)

```step
title: Perfectly opposite
text: Choose the singlet |Ψ⁻⟩ as the State, keep Clean pairs at 100%, set both Alice axis and Bob axis to 0°, and press Send many. Every pair gives opposite results: E = −1.
check: did pairs state=psi- alice=0 bob=0 E<=-0.99 clean=1
```

```step
title: Beat the classical limit
text: Press Run Bell test with the singlet and 100% clean pairs. The meter measures the four CHSH settings; |S| should come out near 2√2 ≈ 2.83, well above 2.
hint: With 500 pairs per setting, the error on |S| is about ±0.06.
check: did bell state=psi- clean=1 S>=2.5
```

```step
title: Add noise until the violation is gone
text: Lower Clean pairs to 60% and run the Bell test again. Every correlation shrinks by the same factor, so |S| ≈ 2.83 × 0.6 ≈ 1.70: below 2, explainable classically.
check: did bell state=psi- clean<=0.65 S<2
```

```step
title: A classical correlation
text: Choose the classically correlated State (|00⟩ or |11⟩, 50% each) and run the Bell test. Its results agree perfectly along z, yet |S| stays at or below 2.
check: did bell state=classical S<=2.15
```

## What you found

Perfect correlation alone proves nothing; the Bell test asks for correlations along *several* axes at once, and only entanglement exceeds 2. Noise erodes the violation, which disappears below about 71% clean pairs.

```quiz
Q: At which fraction of clean pairs does the singlet's |S| fall to exactly 2?
- 50%
* About 71% (1/√2)
- 90%
E: |S| = 2√2 × v, which equals 2 at v = 1/√2 ≈ 0.71.
```

```quiz
Q: Why does the classically correlated state fail the Bell test although its z results always agree?
* Its correlation disappears along other axes, so the four CHSH terms cannot all be large
- It has too few pairs
- Its results are random
E: A mixture of |00⟩ and |11⟩ is correlated only along z; along x its correlation is 0, which keeps |S| ≤ 2.
```
