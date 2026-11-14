---
title: Optimizers, landscapes and plateaus
area: circuits
kind: lecture
order: 25
objectives: Compare gradient-based and gradient-free optimizers | Read an energy landscape | Recognize step-size problems, plateaus and local minima
math: 12-gradients-and-optimization
---
# Optimizers, landscapes and plateaus

## The idea

Training a variational circuit is walking downhill on a landscape whose height is ⟨H⟩. The walk can be fast or slow, can overshoot, and can get stuck — in a valley that is not the lowest, or on a plain where the ground is nearly flat. Choosing an optimizer is choosing how to walk.

## The landscape

⟨H⟩ as a function of the parameters is an **energy landscape**. **Landscape…** in the Parameters panel draws it over one or two parameters (others fixed): blue valleys are low, yellow hills high, and the optimizer's path is drawn on top.

## Gradient descent and the step size

The simplest method steps downhill: $\theta \leftarrow \theta - \eta\,\nabla \langle H \rangle$. Its step size $\eta$ matters: too large, and each step overshoots the valley so the energy bounces up and down; too small, and progress crawls. QuantumScope uses a **backtracking line search**: a step that would raise ⟨H⟩ is rejected and the step halved, so gradient descent never goes uphill.

## Better methods

| Method | Uses | Character |
|---|---|---|
| Gradient descent | gradients | simple; slow on flat regions |
| BFGS | gradients | learns the curvature; few steps |
| Adam | gradients | momentum and a step size per parameter |
| SPSA | two ⟨H⟩ values per step | cheap; the usual choice on hardware |
| Rotosolve | three ⟨H⟩ values per parameter | sets each parameter to its exact minimum |
| Quantum natural gradient | gradients and the state's geometry | steps of even size in the state |
| Simulated annealing | only ⟨H⟩ values | random, can climb out of local minima |
| COBYLA, Nelder–Mead | only ⟨H⟩ values | no gradients; try many probe points |

The next lecture explains SPSA, Rotosolve and the natural gradient, and what happens when ⟨H⟩ comes from a limited number of measurements.

The optimizer reports both its **steps** and its **circuit evaluations**: BFGS takes few steps but each needs a full gradient, while gradient-free methods discard most probes.

## Plateaus and local minima

- On a **plateau** the gradient is nearly zero and gradient descent crawls. In large random circuits these *barren plateaus* (McClean and colleagues, 2018) make training very hard.
- A **local minimum** is a valley that is not the lowest. "No step lowered ⟨H⟩" can mean you are at the best the circuit can do — or only at a local valley: try other starting values.

[Try it: compare methods on a 4-spin Ising chain](qs:algorithm/vqe?problem=ising-4&layers=3)

## Worked example

Minimize $f(\theta) = \cos\theta$ from $\theta = 2.5$, where $f = -0.801$ and $f'(\theta) = -\sin 2.5 = -0.598$. A backtracking line search tries a big step first:

| Step size η | New θ | New f | Verdict |
|---|---|---|---|
| 5 | 5.49 | +0.703 | uphill: rejected, halve |
| 2.5 | 4.00 | −0.657 | still worse than −0.801: halve |
| 1.25 | 3.25 | −0.994 | accepted |

One accepted step brings $\theta$ close to the minimum at $\pi$. Without the check, the first step would have thrown the parameter far past the valley.

## Common mistakes

- **Using one fixed step size everywhere.** Steep and flat regions need different steps; line searches and Adam adapt.
- **Comparing optimizers by steps alone.** Count circuit evaluations: a BFGS step can cost many circuits.
- **Stopping at the first minimum found.** Restart from other values to check for a lower valley.

## In the app

In the **Parameters & observable** panel, choose an optimizer and press **Optimize**; it reports steps and circuit evaluations. **Landscape…** draws ⟨H⟩ over one or two parameters with the optimizer's path on top. Try several methods on the 4-spin Ising chain and compare their evaluations.

## Check your understanding

```quiz
Q: Gradient descent's energy bounces up and down. What is the likely cause?
* The step size is too large
- The gradient is exact
- The circuit has too many layers
E: Too large a step overshoots the valley on every step.
```

```quiz
Q: Why does BFGS report many circuit evaluations despite few steps?
* Each step needs a full parameter-shift gradient: two runs per bound gate
- BFGS repeats every step twice
- It counts measurement shots
E: Steps are cheap to count, but every gradient costs two circuit runs per gate.
```

```quiz
Q: Gradient descent's energy bounces up and down from step to step. What is the likely cause?
* The step size is too large, so each step overshoots the valley
- The step size is too small
- The landscape has no minimum
E: Overshooting lands on the other side of the valley each time; a smaller step or a line search fixes it.
```

```quiz
Q: Which optimizer can, in principle, climb out of a local minimum?
- Gradient descent
- BFGS
* Simulated annealing
E: Simulated annealing sometimes accepts uphill moves at random, so it can leave a valley; gradient methods only go downhill.
```

## Summary

- The landscape shows ⟨H⟩ over the parameters; optimizers walk downhill on it.
- Step size matters; a line search keeps gradient descent from overshooting.
- Plateaus slow optimizers down; local minima can stop them early.
