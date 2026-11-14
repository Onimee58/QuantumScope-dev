---
title: "Lab: where is the electron?"
area: hydrogen
kind: lab
order: 91
objectives: Read the radial probability chart | Find radial nodes and the most probable radius | See how enclosure surfaces depend on the chosen probability
math: 06-probability
---
# Lab: where is the electron?

The density |ψ|² and the radial probability r²R² answer different questions. You will read both, find the peaks and nodes the lectures computed, and see how much an orbital picture depends on the probability it encloses. Read *Probability density and radial probability* first.

[Open the Hydrogen Explorer](qs:open/orbital)

```step
title: The 1s peak at one Bohr radius
text: Draw n = 1 (1s). The Radial probability chart peaks at r = 1 a_μ, although the density is largest at the nucleus. Find the peak on the chart.
check: did orbital n=1 l=0
```

```step
title: Enclosure surfaces have no fixed edge
text: Set Representation to Probability enclosure and draw 1s with Enclosed probability 50%, then 99%. The surface for 99% is far larger: an orbital has no edge, only a chosen fraction.
check: did orbital n=1 l=0 view=enclosure enclosed<=60
check: did orbital n=1 l=0 view=enclosure enclosed>=95
```

```step
title: A node and two peaks
text: Draw 2s (n = 2, l = 0). The radial chart drops to zero at r = 2 a_μ — the radial node — with a small inner peak near 0.76 a_μ and the main peak near 5.24 a_μ.
check: did orbital n=2 l=0
```

```step
title: Same energy, different radial shape
text: Draw 2p (n = 2, l = 1). Its radial probability has a single peak at 4 a_μ and no node. Compare with 2s: same energy, different distances.
check: did orbital n=2 l=1
```

## What you found

The radial chart is the probability per distance; its peaks and zeros match $P(r) = r^2R^2$ from the lecture. An enclosure surface is a choice, not the atom's edge.

```quiz
Q: The 2s radial probability is zero at r = 2 a_μ. What is this point called?
* A radial node
- The Bohr radius
- The most probable radius
E: R(r) changes sign there, so the probability of finding the electron at exactly that distance is zero.
```
