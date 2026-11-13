---
title: QAOA and MaxCut
area: circuits
kind: lecture
order: 26
objectives: State the MaxCut problem as an energy | Build a QAOA circuit from cost and mixer layers | Interpret approximation ratios and the effect of symmetry
math: 10-pauli-algebra, 12-gradients-and-optimization
---
# QAOA and MaxCut

## The idea

Many practical problems — scheduling, routing, network design — ask for the best of an enormous number of combinations. QAOA turns such a problem into an energy, starts from all answers at once, and uses a few layers of alternating gates, tuned by a classical optimizer, to make good answers more likely. MaxCut on small graphs shows how it works and where its limits are.

## MaxCut

Colour each node of a graph 0 or 1. An edge is **cut** when its ends differ. **MaxCut** asks for the colouring with the most cut edges — a hard problem in general. As an energy, with one qubit per node,

$$H = \sum_{(i,j)\,\in\,\text{edges}} \frac{1}{2}\left(Z_i Z_j - 1\right)$$

counts minus the cut edges, so its minimum is minus the maximum cut.

## The QAOA circuit

The **Quantum Approximate Optimization Algorithm** (Farhi, Goldstone and Gutmann, 2014) alternates two steps, $p$ times:

1. **Cost** $e^{-i\gamma H}$: for every edge, CX, RZ(−γ), CX.
2. **Mixer** $e^{-i\beta \sum X}$: RX(2β) on every node.

It starts from H on every qubit (all colourings equally likely) and optimizes the $2p$ angles γ and β.

[Try it: QAOA on a square — Optimize, then Show the graph](qs:algorithm/qaoa?graph=ring4&layers=1)

## How good is it?

The **approximation ratio** is the expected cut divided by the maximum cut. On rings with an even number of nodes, one layer reaches exactly **3/4**. With two layers the hexagon reaches **5/6**, while the square — small enough for two layers to cover it — is solved outright: the maximum cut is found with certainty. More layers help, at the cost of more parameters.

## Symmetry

QAOA treats equivalent nodes and edges alike. On the pentagon all five edges are equivalent, so ⟨Z₀Z₁⟩ equals the average over the edges. The best cut leaves 1 of the 5 edges uncut, so that average is at least

$$\frac{1 - 4}{5} = -0.6$$

even though the observable Z₀Z₁ alone could reach −1. The circuit's structure limits the states it can make.

## Worked example

Take the square: four nodes in a ring, four edges. Colouring 0101 cuts all four edges, so the maximum cut is 4 and $\min H = -4$.

- **Before QAOA** (H on every qubit): every colouring is equally likely, each edge is cut half the time, and the expected cut is 2: ratio $2/4 = 0.5$.
- **One layer**, optimized: the expected cut rises to 3: ratio $3/4$.
- **Two layers**: the square is solved outright, and 0101 or 1010 is measured with certainty.

The answer is read by measuring: each shot gives one colouring, and the best one seen is kept.

## Common mistakes

- **Reading the expected cut as the answer.** QAOA produces a distribution; you measure and keep the best colouring found.
- **Expecting more layers to be free.** Each layer adds two angles to optimize and more gates to suffer noise.
- **Ignoring symmetry.** Equivalent edges get equal treatment, which can cap what a shallow circuit reaches.

## In the app

**Algorithms → QAOA** builds the circuit for rings and other small graphs. Press **Optimize**, then **Show the graph** to see the most likely colourings and their cuts; the verification panel reports the approximation ratio. Compare one and two layers on the square and the hexagon.

## Check your understanding

```quiz
Q: What does one QAOA layer contain?
- Only CX gates
* A cost step on every edge and a mixer RX(2β) on every node
- A measurement of every qubit
E: Each layer applies the cost Hamiltonian (angle γ) and the mixer (angle β).
```

```quiz
Q: For an even ring with one layer, what approximation ratio does QAOA reach?
- 1/2
* 3/4
- 1
E: The known result for rings at p = 1 is 3/4.
```

```quiz
Q: A triangle is coloured 001. How many edges are cut?
- 0
- 1
* 2
- 3
E: Edges (0,2) and (1,2) join nodes of different colours; edge (0,1) does not. No colouring of a triangle cuts all three.
```

```quiz
Q: What is the approximation ratio of measuring a random colouring of an even ring?
* 1/2
- 3/4
- 1
E: Each edge is cut with probability 1/2, so the expected cut is half the edges, while the maximum cut is all of them.
```

## Summary

- MaxCut becomes an energy: minus the number of cut edges.
- QAOA alternates cost and mixer layers and optimizes γ and β.
- Even rings: 3/4 at one layer; the hexagon 5/6 at two; symmetry limits what QAOA can reach.
