---
title: "Lab: watch a quantum beat"
area: hydrogen
kind: lab
order: 92
objectives: Play a two-state superposition and read its beat period | Show that degenerate states do not beat | Separate how fast the cloud moves from how much it moves
math: 01-complex-numbers, 09-matrix-exponentials
---
# Lab: watch a quantum beat

A single orbital never moves; two together slosh back and forth. You will play superpositions, check the beat period against h/|ΔE|, and find one pair that does not move at all. Read *Superposition and quantum beats* first.

[Open Hydrogen Dynamics 2D](qs:open/dynamics2d)

```step
title: The 1s + 2p beat
text: Choose 1s as State A and a 2p state as State B, set State A probability to 50% and press Play. The beat period is 0.4055 fs: h/(E₂ − E₁).
check: did beat pair=1s+2p p=0.5
```

```step
title: A faster beat
text: Change State B to a 3d state and play again. The energy difference is larger, so the period is shorter: 0.3421 fs.
check: did beat pair=1s+3d
```

```step
title: A superposition that stands still
text: Choose 2s and 2p and press Play. The density is lopsided but does not move: the two states have the same energy, so there is no beat.
check: did beat pair=2s+2p
```

```step
title: How much, not how fast
text: Go back to 1s + 2p and set State A probability to 90%. Play: the period is unchanged, but the cloud moves much less.
check: did beat pair=1s+2p p>=0.85
```

## What you found

The period depends only on the energies; the mixture sets the amplitude of the motion. Equal energies mean no beat at all. Try the same pairs in **Hydrogen Dynamics 3D** to see the motion in space.

```quiz
Q: The 2s + 3p superposition beats with which period?
- 0.4055 fs
* About 2.19 fs
- No beat
E: h/|E₃ − E₂| = 4.1357 × 10⁻¹⁵ eV s / 1.8887 eV ≈ 2.19 fs: the period of Balmer α light.
```
