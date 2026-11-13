---
title: Optimizing with shots
area: circuits
kind: lecture
order: 28
objectives: Explain why measured energies are noisy and how the noise shrinks with shots | Describe SPSA, Rotosolve and the quantum natural gradient | Choose an optimizer for exact or noisy energies
math: 12-gradients-and-optimization
---
# Optimizing with shots

A simulator can compute ⟨H⟩ exactly. A quantum computer cannot: it prepares the state, measures it, and repeats. Each measurement of a Pauli term gives +1 or −1, so ⟨H⟩ is only **estimated** from a limited number of **shots**, and every estimate is a little different.

## Shot noise

With $N$ shots, a Pauli term $P$ is estimated by the average of $N$ outcomes of ±1. The estimate is right on average, but it scatters with a standard deviation of

$$\sigma = \sqrt{\frac{1 - \langle P \rangle^2}{N}}$$

so **a hundred times more shots make the noise ten times smaller**. In the Parameters panel, choose **Exact** or 100, 1,000 or 10,000 **shots**: with shots, the optimizer only ever sees noisy values, as on hardware, and the Optimize chart draws the measured ⟨H⟩ (thin) beside the true ⟨H⟩ (bold).

Noise hurts some methods badly. **Nelder–Mead** and **COBYLA** compare nearby energies, and noise makes those comparisons random. **BFGS** builds a model of the curvature from differences of gradients, which noise spoils. With shots, gradients also come from the **parameter-shift rule** applied to noisy energies, as on a real device: two circuit runs per gate.

## SPSA: two runs per step

**SPSA** (simultaneous perturbation stochastic approximation; Spall, 1992) moves every parameter at once, along a random direction $\Delta$ of $\pm 1$ entries:

$$\hat g = \frac{\langle H \rangle(\theta + c\Delta) - \langle H \rangle(\theta - c\Delta)}{2c}\,\Delta$$

That is a gradient estimate from **two** circuit runs, however many parameters there are; a full gradient needs two per gate. Its steps shrink slowly as the run goes on, so it explores first and settles later. It tolerates noise well, which is why it is the usual choice on hardware.

## Rotosolve: an exact minimum, one parameter at a time

A rotation gate RY(θ) changes ⟨H⟩ in a very simple way: with the other parameters fixed,

$$\langle H \rangle(\theta) = a\cos(\theta - b) + c$$

a sinusoid. Three values of ⟨H⟩ fix $a$, $b$ and $c$, and the minimum is then known exactly: $\theta = b + \pi$. **Rotosolve** (Ostaszewski, Grant and Benedetti, 2021) sets each parameter in turn to its exact minimum. It needs no learning rate. Because it moves one parameter at a time, it can zig-zag slowly along a narrow valley: watch its staircase path on the **Landscape**. (A parameter that drives several gates gives a sum of sinusoids, which Rotosolve fits with more values.)

## The quantum natural gradient

Gradient descent treats every parameter alike. But a change in one parameter may move the quantum state a lot, and the same change in another hardly at all. The **Fubini–Study metric** $g$ measures how far the state moves:

$$1 - |\langle \psi(\theta) | \psi(\theta + \delta) \rangle|^2 \approx \delta^{T} g\, \delta$$

The **quantum natural gradient** (Stokes and colleagues, 2020) steps along $g^{-1}\nabla\langle H \rangle$, so every step changes the *state* by a similar amount. It often needs fewer steps, at the cost of computing $g$.

## Simulated annealing

**Simulated annealing** makes random moves. It always accepts a move downhill, and accepts one uphill with probability $e^{-\Delta E / T}$, where the "temperature" $T$ falls as the run goes on. Early, it can climb out of local minima; late, it settles. It is slow, but it does not need gradients and does not get stuck in the first valley it finds.

## Choosing an optimizer

| Situation | A good choice |
|---|---|
| Exact energies, smooth landscape | BFGS, or the quantum natural gradient |
| Noisy energies (shots), many parameters | SPSA |
| Rotation-gate circuits, no tuning wanted | Rotosolve |
| Many local minima | Best of N starts, or simulated annealing |

[Try it: optimize the H₂ ground state, then repeat with 1,000 shots](qs:algorithm/vqe?problem=h2&layers=2)

## Check your understanding

```quiz
Q: How many more shots do you need to make the noise in ⟨H⟩ three times smaller?
- Three times as many
* Nine times as many
- Six times as many
E: The noise shrinks like 1/√N, so a third of the noise needs 3² = 9 times the shots.
```

```quiz
Q: A circuit has 40 parameters. How many circuit runs does one SPSA step need, and one exact parameter-shift gradient?
* SPSA: 2; the gradient: at least 80
- SPSA: 80; the gradient: 2
- Both need 40
E: SPSA estimates the gradient along one random direction from two runs; the parameter-shift rule needs two runs per parameter.
```

```quiz
Q: Why does Rotosolve need no learning rate?
* With the other parameters fixed, ⟨H⟩ is a sinusoid in each angle, so its exact minimum can be computed
- It uses the quantum natural gradient
- It only works with exact energies
E: Three values fix the sinusoid a cos(θ − b) + c, whose minimum is at θ = b + π.
```

## Summary

- Measured energies are noisy; the noise shrinks like 1/√(shots).
- SPSA needs two runs per step and tolerates noise; Rotosolve finds each parameter's exact minimum; the natural gradient follows the state's geometry.
- The best optimizer depends on whether energies are exact or measured.
