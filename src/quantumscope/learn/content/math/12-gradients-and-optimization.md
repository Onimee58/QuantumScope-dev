---
title: Gradients and optimization
area: math
kind: lecture
order: 12
objectives: Compute derivatives and gradients of simple functions | Describe gradient descent and its pitfalls | Explain why the parameter-shift rule gives exact derivatives
---
# Gradients and optimization

## The idea

Variational algorithms tune circuit parameters to make a quantity as small as possible, like turning knobs to find the lowest point of a landscape. The tools are classical calculus: **derivatives** say which way is downhill, **gradient descent** walks that way, and the **parameter-shift rule** lets a quantum computer measure the slope exactly.

## Derivatives

The derivative $f'(\theta)$ is the slope of $f$ at $\theta$: how fast $f$ changes when $\theta$ changes a little. Two rules cover most circuits:

$$\frac{d}{d\theta}\cos\theta = -\sin\theta, \qquad \frac{d}{d\theta}\sin\theta = \cos\theta$$

At a minimum the slope is zero, which is the condition optimizers look for.

## Gradients

With several parameters $\theta_1, \dots, \theta_k$, the **gradient** collects the slopes along each one (the partial derivatives):

$$\nabla f = \left( \frac{\partial f}{\partial \theta_1}, \dots, \frac{\partial f}{\partial \theta_k} \right)$$

It points uphill, in the direction of steepest increase.

## Gradient descent

**Gradient descent** repeatedly takes a small step downhill:

$$\theta \leftarrow \theta - \eta\, \nabla f(\theta)$$

where $\eta$ is the step size. Too large a step overshoots the valley; too small a step crawls. QuantumScope's gradient descent shortens the step whenever it would go uphill, so it never makes things worse.

Two pitfalls appear in the energy landscapes:

- **Local minima:** a valley that is not the lowest one. Descent stops there, which is why starting again from random parameters ("best of N starts") helps.
- **Barren plateaus:** large flat regions where the gradient is nearly zero in every direction, so there is no downhill to follow.

## The parameter-shift rule

A circuit's expectation value depends on a rotation angle like $f(\theta) = A + B\cos\theta + C\sin\theta$. For such a function, the derivative is **exactly**

$$f'(\theta) = \frac{f(\theta + \frac{\pi}{2}) - f(\theta - \frac{\pi}{2})}{2}$$

Check it: $\cos(\theta + \frac{\pi}{2}) - \cos(\theta - \frac{\pi}{2}) = -2\sin\theta$, giving $-B\sin\theta$, and the $\sin$ term gives $C\cos\theta$ the same way. Unlike a numerical difference with a tiny step, this uses two large shifts and has no approximation error, so a quantum computer can measure gradients with just two extra circuit runs per parameter.

## Worked example

Minimize $f(\theta) = \langle Z\rangle$ for the state $R_Y(\theta)|0\rangle$, which is $f(\theta) = \cos\theta$. Start at $\theta = \pi/3$, where $f = 0.5$. The parameter-shift rule gives

$$f'\!\left(\frac{\pi}{3}\right) = \frac{\cos\frac{5\pi}{6} - \cos\left(-\frac{\pi}{6}\right)}{2} = \frac{-0.866 - 0.866}{2} = -0.866$$

exactly $-\sin(\pi/3)$. With step size $\eta = 0.5$: $\theta \leftarrow 1.047 + 0.433 = 1.480$, and $f$ falls to $0.091$. One more step reaches $\theta \approx 1.978$ and $f \approx -0.40$; continuing, $\theta$ approaches $\pi$ and $f$ its minimum $-1$, the state $|1\rangle$.

## Common mistakes

- **Stepping along the gradient.** The gradient points uphill; descent subtracts it.
- **Using a tiny shift in the parameter-shift rule.** The shifts are exactly $\pm\pi/2$; a tiny shift would be an approximate finite difference, badly hurt by shot noise.
- **Reading a zero gradient as the answer.** It can be a local minimum, a plateau, or even a maximum; check the value and try other starts.

## In the app

The VQE example lets you press **Optimize** and then open the energy landscape: you can see the path descent takes and where local minima sit. Choose different optimizers and starting points to compare. In the calculator, the link below evaluates the worked example's parameter-shift derivative and gives exactly $-\sqrt{3}/2$.

[Try it: VQE for H₂ — press Optimize, then open the landscape](qs:algorithm/vqe?problem=h2&layers=1)

[Try it in the calculator: (expect(Z, RY(pi/3 + pi/2)|0⟩) - expect(Z, RY(pi/3 - pi/2)|0⟩))/2](qs:calc?expr=%28expect%28Z%2C%20RY%28pi%2F3%20%2B%20pi%2F2%29%7C0%E2%9F%A9%29%20-%20expect%28Z%2C%20RY%28pi%2F3%20-%20pi%2F2%29%7C0%E2%9F%A9%29%29%2F2)

## Check your understanding

```quiz
Q: f(θ) = cos θ. What does the parameter-shift rule give at θ = 0?
- 1
* 0
- −1
E: [cos(π/2) − cos(−π/2)]/2 = (0 − 0)/2 = 0, exactly f′(0) = −sin 0 = 0.
```

```quiz
Q: Gradient descent stops at a valley that is not the lowest. What helps?
- A smaller step size
* Starting again from other (random) parameters
- Measuring more shots
E: A local minimum traps descent from that side; other starting points can reach other valleys.
```

```quiz
Q: The gradient at the current parameters is (0.4, −0.2). With step size 0.5, how do the parameters change?
* By (−0.2, +0.1)
- By (+0.2, −0.1)
- By (0.4, −0.2)
E: θ ← θ − η∇f: −0.5 × (0.4, −0.2) = (−0.2, +0.1).
```

```quiz
Q: How many circuit runs does the parameter-shift rule need per parameter (exactly, without shot noise)?
- One
* Two: at θ + π/2 and θ − π/2
- As many as the number of parameters
E: Each partial derivative needs the two shifted evaluations of that one parameter.
```

## Summary

- The gradient collects partial derivatives and points uphill; descent steps against it.
- Local minima and barren plateaus are the main obstacles; random restarts help with the first.
- The parameter-shift rule gives exact derivatives from two shifted circuit runs.
