---
title: Superposition and the Bloch sphere
area: principles
kind: lecture
order: 1
objectives: Write any single-qubit pure state with two angles | Locate states on the Bloch sphere | Connect a spin-½ particle with a qubit
math: 01-complex-numbers, 02-vectors-and-dirac-notation
---
# Superposition and the Bloch sphere

## The idea

A classical bit is 0 or 1. A qubit can be in a **superposition** of both, with complex weights. That sounds like a lot of freedom, but one picture captures all of it: every pure state of a single qubit is a point on the surface of a sphere. Once you can find a state on this sphere, gates become rotations and measurements become questions about directions.

## Two angles describe every pure state

Up to an unobservable global phase, every pure state of a two-level system can be written as

$$|\psi\rangle = \cos\frac{\theta}{2}|0\rangle + e^{i\varphi}\sin\frac{\theta}{2}|1\rangle$$

with $0 \leq \theta \leq \pi$ and $0 \leq \varphi < 2\pi$. These are the polar and azimuthal angles of a point on a sphere: the **Bloch sphere**. Its north pole is $|0\rangle$, its south pole $|1\rangle$, and the equator holds the equal superpositions such as $|+\rangle$ and $|+i\rangle$.

## The Bloch vector

The point's coordinates are the expectation values of the three Pauli operators:

$$\vec r = (\langle X\rangle, \langle Y\rangle, \langle Z\rangle) = (\sin\theta\cos\varphi,\ \sin\theta\sin\varphi,\ \cos\theta)$$

Pure states lie on the surface ($|\vec r| = 1$). Mixed states, such as one qubit of an entangled pair, lie inside; the maximally mixed state is the center.

## Spin-½

An electron's spin is a physical two-level system: "up" and "down" along any chosen axis. Spin up along $z$ corresponds to $|0\rangle$; spin up along $x$ corresponds to $|+\rangle$. The Bloch vector points along the direction in which the spin is definitely "up".

## Superposition is not ignorance

$|+\rangle$ is not "secretly 0 or secretly 1". A coin that is secretly heads or tails would give random results along *every* axis, but $|+\rangle$ gives a definite result when measured along $x$. Superposition is a definite state pointing in a different direction.

## Worked example

Take $\theta = \pi/3$ and $\varphi = \pi/4$. Then $\cos(\pi/6) \approx 0.866$ and $\sin(\pi/6) = 0.5$, so

$$|\psi\rangle \approx 0.866\,|0\rangle + 0.5\,e^{i\pi/4}|1\rangle$$

The Bloch vector is $(\sin\theta\cos\varphi, \sin\theta\sin\varphi, \cos\theta) \approx (0.612, 0.612, 0.5)$: halfway up the northern hemisphere, between the $+x$ and $+y$ axes. Its length is $\sqrt{0.612^2 + 0.612^2 + 0.5^2} = 1$, as a pure state's must be. Measured in the computational basis, $P(0) = 0.866^2 = 0.75$.

## Common mistakes

- **Using θ instead of θ/2.** The amplitudes use half the sphere's angle: the south pole ($\theta = \pi$) is $|1\rangle$, not $-|0\rangle$.
- **Thinking opposite points are opposite signs.** $|0\rangle$ and $|1\rangle$ are orthogonal, yet they sit at opposite poles. On the sphere, *antipodal* means orthogonal.
- **Giving the global phase a place on the sphere.** $|\psi\rangle$ and $e^{i\alpha}|\psi\rangle$ are the same point; only the *relative* phase $\varphi$ moves it.

## In the app

In **Quantum Principles → Superposition**, set θ and φ under **Prepare** and watch the arrow move. Then turn the measurement **Axis** and press **Measure many**: the fraction of "up" results follows the angle between the arrow and the axis. In the circuit editor, the State Inspector shows the same sphere for any circuit.

[Try it: explore the Bloch sphere](qs:open/superposition)

[Try it: the worked example's state in the State Inspector](qs:circuit?n=1&gates=RY:0:pi/3;RZ:0:pi/4&inspector=1)

## Check your understanding

```quiz
Q: Where on the Bloch sphere is |−i⟩ = (|0⟩ − i|1⟩)/√2?
- North pole
- On the equator, along +y
* On the equator, along −y
- At the center
E: θ = π/2 (equal weights) and φ = 3π/2 (the factor −i), which points along −y.
```

```quiz
Q: A qubit's Bloch vector has length 0.6. What can you say?
- It is a pure state
* It is mixed, for example entangled with something else
- It has been measured
E: Pure states lie on the surface (length 1); shorter vectors are mixed states.
```

```quiz
Q: A state has θ = π/2 and φ = 0. What is it?
* |+⟩, on the equator along +x
- |1⟩, at the south pole
- |0⟩, at the north pole
- The maximally mixed state
E: cos(π/4) = sin(π/4) = 1/√2 and e^{i·0} = 1, so the state is (|0⟩ + |1⟩)/√2 = |+⟩, the +x direction.
```

```quiz
Q: Two pure states sit at opposite points of the Bloch sphere. What is true?
- They differ only by a global phase
* They are orthogonal: a measurement can tell them apart perfectly
- One is the negative of the other
- They give the same probabilities in every basis
E: Antipodal points are orthogonal states, like |0⟩ and |1⟩ or |+⟩ and |−⟩. Measuring along their axis always distinguishes them.
```

## Summary

- Two angles θ, φ describe every pure qubit state: a point on the Bloch sphere.
- The amplitudes use θ/2, so opposite points are orthogonal states.
- The Bloch vector is (⟨X⟩, ⟨Y⟩, ⟨Z⟩); mixed states lie inside the sphere.
- A spin-½ particle is a physical qubit; superposition is a definite state, not hidden ignorance.
