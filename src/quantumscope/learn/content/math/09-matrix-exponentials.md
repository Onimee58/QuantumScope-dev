---
title: Matrix exponentials and rotations
area: math
kind: lecture
order: 9
objectives: Compute e^{−iθX/2} from the exponential series | Recognize rotation gates as exponentials of Paulis | Relate time evolution to e^{−iHt}
---
# Matrix exponentials and rotations

## The idea

Rotation gates, time evolution and phases all come from one operation: the **exponential of a matrix**. For the Pauli matrices this exponential has a simple closed form, which is why every single-qubit rotation can be written with one cosine and one sine — and why the angles in the formulas are halved.

## The exponential series

For numbers, $e^x = 1 + x + \frac{x^2}{2!} + \frac{x^3}{3!} + \dots$. The same series defines $e^A$ for a square matrix $A$:

$$e^{A} = I + A + \frac{A^2}{2!} + \frac{A^3}{3!} + \dots$$

## Paulis square to the identity

The series becomes simple for Pauli matrices because $X^2 = Y^2 = Z^2 = I$. Splitting it into even and odd powers gives, for $P = X$, $Y$ or $Z$:

$$e^{-i\theta P/2} = \cos\frac{\theta}{2}\, I - i\,\sin\frac{\theta}{2}\, P$$

This is the same pattern as Euler's formula, $e^{-i\theta/2} = \cos\frac{\theta}{2} - i\sin\frac{\theta}{2}$, with the matrix $P$ in place of the number 1.

## Rotation gates

The rotation gates are exactly these exponentials:

$$R_X(\theta) = e^{-i\theta X/2}, \qquad R_Y(\theta) = e^{-i\theta Y/2}, \qquad R_Z(\theta) = e^{-i\theta Z/2}$$

$R_X(\theta)$ turns the Bloch vector by the angle $\theta$ about the $x$ axis, and likewise for $y$ and $z$. For example

$$R_Y(\theta) = \begin{pmatrix} \cos\frac{\theta}{2} & -\sin\frac{\theta}{2} \\ \sin\frac{\theta}{2} & \cos\frac{\theta}{2} \end{pmatrix}$$

so $R_Y(\pi)|0\rangle = |1\rangle$ and $R_Y(\frac{\pi}{2})|0\rangle = |+\rangle$.

The angle is halved inside the formula because a full turn on the Bloch sphere ($\theta = 2\pi$) gives $e^{-i\pi P} = -I$: the state picks up a sign, a **global phase**, which no measurement can detect. Only $\theta = 4\pi$ gives exactly $I$ again.

## Time evolution

A system with Hamiltonian $H$ (its energy observable) evolves for a time $t$ by the unitary

$$U(t) = e^{-iHt/\hbar}$$

Because $H$ is Hermitian, $U(t)$ is unitary. An eigenstate of $H$ with energy $E$ only picks up a phase, $e^{-iEt/\hbar}$: this is why energy eigenstates are called **stationary states**, and why hydrogen's orbitals do not change shape over time.

## Worked example

Apply $R_X(\pi/2)$ to $|0\rangle$. With $\theta/2 = \pi/4$:

$$R_X\!\left(\frac{\pi}{2}\right)|0\rangle = \cos\frac{\pi}{4}|0\rangle - i\sin\frac{\pi}{4}\,X|0\rangle = \frac{1}{\sqrt{2}}\left(|0\rangle - i|1\rangle\right) = |{-i}\rangle$$

On the Bloch sphere, a quarter turn about $x$ takes the north pole to $-y$, as the right-hand rule says. Now a spin in a magnetic field along $z$ has $H = \frac{\hbar\omega}{2}Z$, so $U(t) = e^{-i\omega t Z/2} = R_Z(\omega t)$: the field turns the Bloch vector steadily about $z$, one full turn every $2\pi/\omega$. This precession is how magnetic resonance controls spins.

## Common mistakes

- **Forgetting the half angle.** $R_Y(\pi)$ uses $\cos(\pi/2)$ and $\sin(\pi/2)$, and flips $|0\rangle$ to $|1\rangle$: a half turn on the sphere is a full flip of the state.
- **Exponentiating entry by entry.** $e^A$ is not the matrix of $e^{a_{ij}}$; use the series or the Pauli formula.
- **Reading $R_Z(2\pi) = -I$ as a physical change.** The sign is a global phase; it matters only when the rotation is controlled by another qubit.

## In the app

Place an RX gate and double-click it to set the angle; the State Inspector shows the Bloch arrow turning by exactly that angle. Try RX at π/2 on $|0\rangle$ and find the arrow on $-y$. In the calculator, `exp(-i θ X / 2)` gives the formula above with θ as a symbol.

[Try it: RY(90°) turns |0⟩ into |+⟩](qs:circuit?n=1&gates=RY:0:pi/2)

[Try it: RX(90°) turns |0⟩ into |−i⟩](qs:circuit?n=1&gates=RX:0:pi/2&inspector=1)

[Try it in the calculator: exp(-i θ X / 2)](qs:calc?expr=exp%28-i%20%CE%B8%20X%20%2F%202%29&mode=exact)

## Check your understanding

```quiz
Q: What is RX(π) up to a global phase?
* X
- I
- H
E: e^{−iπX/2} = cos(π/2) I − i sin(π/2) X = −iX, which is X times a global phase.
```

```quiz
Q: Why does an energy eigenstate look unchanged over time?
- Its energy is zero
* It only gains a phase e^{−iEt/ħ}, which is unobservable on its own
- Hamiltonians are not unitary
E: e^{−iHt/ħ} acting on an eigenstate just multiplies it by e^{−iEt/ħ}, a global phase.
```

```quiz
Q: What is RZ(θ) applied to |0⟩?
* |0⟩, up to a global phase
- |1⟩
- |+⟩
E: |0⟩ is an eigenstate of Z, so e^{−iθZ/2}|0⟩ = e^{−iθ/2}|0⟩: the arrow on the z axis does not move.
```

```quiz
Q: Which angle θ makes RY(θ) exactly the identity matrix?
- π
- 2π
* 4π
E: RY(2π) = −I, a global phase of −1. Only 4π brings the matrix back to I.
```

## Summary

- $e^A$ is defined by the exponential series; for Paulis, $e^{-i\theta P/2} = \cos\frac{\theta}{2} I - i\sin\frac{\theta}{2} P$.
- $R_X$, $R_Y$, $R_Z$ are exactly these exponentials: rotations of the Bloch sphere by θ.
- Time evolution is $e^{-iHt/\hbar}$; energy eigenstates only gain a phase, and a field along z makes spins precess.
