---
title: Global and relative phase
area: principles
kind: lecture
order: 5
objectives: Explain why a global phase is unobservable | Show how a relative phase changes measurement results after interference | Recognize phase on the Bloch sphere
math: 01-complex-numbers
---
# Global and relative phase

## The idea

Amplitudes are complex numbers, so each has a size and a **phase**. The sizes give probabilities directly; the phases do not. Yet phases are not decoration: a phase on the whole state changes nothing, while a phase *between* components decides what interference produces. Telling these two apart is the key to reading every circuit.

## Global phase

The states $|\psi\rangle$ and $e^{i\gamma}|\psi\rangle$ give identical probabilities for every possible measurement, because $|e^{i\gamma}|^2 = 1$. They are the same physical state. This is why the Bloch sphere needs only two angles, and why QuantumScope can "remove the global phase" without changing anything physical.

## Relative phase

A phase on *one* component is different:

$$|+\rangle = \frac{1}{\sqrt{2}}(|0\rangle + |1\rangle), \qquad |-\rangle = \frac{1}{\sqrt{2}}(|0\rangle - |1\rangle)$$

Measured in the $z$ basis, both give 50:50. But after a Hadamard, $|+\rangle \to |0\rangle$ and $|-\rangle \to |1\rangle$: completely different outcomes. A relative phase is invisible to one measurement and decisive for another.

## Phase on the Bloch sphere

The relative phase $\varphi$ is the **azimuthal angle** around the $z$ axis. Phase gates such as S, T and $R_Z$ rotate the state around that axis: they leave $z$-measurement probabilities unchanged but move the state between, for example, $|+\rangle$, $|+i\rangle$ and $|-\rangle$.

## Why phase matters

Every quantum algorithm works by arranging relative phases so that wrong answers cancel and right answers reinforce. Phase kickback, Grover's oracle and the QFT are all ways of writing information into phases.

## Worked example

Start with $|+\rangle$, add a relative phase $\varphi$, and apply H:

$$H\,\frac{|0\rangle + e^{i\varphi}|1\rangle}{\sqrt{2}} = \frac{1 + e^{i\varphi}}{2}|0\rangle + \frac{1 - e^{i\varphi}}{2}|1\rangle$$

so $P(0) = \cos^2(\varphi/2)$. Before the H, every one of these states gives 50:50 in the $z$ basis. After it:

- Z ($\varphi = \pi$): $P(0) = 0$.
- S ($\varphi = \pi/2$): $P(0) = 0.5$.
- T ($\varphi = \pi/4$): $P(0) = \cos^2(\pi/8) \approx 0.854$.

The phase was there all along; the H turned it into a measurable difference.

## Common mistakes

- **Treating −|ψ⟩ as a different state.** A minus sign on the whole state is a global phase. A minus sign on one component is not.
- **"Z does nothing, the probabilities didn't change."** Z leaves the $z$-basis probabilities alone but turns $|+\rangle$ into $|-\rangle$, which the next interference step will reveal.
- **Comparing gates up to global phase without saying so.** $R_Z(\theta)$ and $P(\theta)$ differ only by a global phase, so they act identically on one qubit; as *controlled* gates they differ, because the phase becomes relative.

## In the app

Build H, then a phase gate, then H, and open the State Inspector: the amplitude table shows each component's phase, and the probabilities show what the final H made of it. Try Z, S and T in the middle and compare with the worked example. The Bloch sphere shows the phase gates turning the arrow around the $z$ axis.

[Try it: a relative phase revealed by H](qs:circuit?n=1&gates=H:0;Z:0;H:0&inspector=1)

[Try it: H, T, H gives P(0) ≈ 0.854](qs:circuit?n=1&gates=H:0;T:0;H:0&inspector=1)

## Check your understanding

```quiz
Q: Which pair of states can be told apart by some measurement?
- |0⟩ and −|0⟩
- |+⟩ and i|+⟩
* |+⟩ and |−⟩
E: The first two pairs differ only by a global phase. |+⟩ and |−⟩ differ by a relative phase, which H turns into different outcomes.
```

```quiz
Q: What does an RZ gate do to the z-basis measurement probabilities?
* Nothing
- Swaps them
- Makes them equal
E: RZ only rotates around the z axis, changing the relative phase, not |α|² or |β|².
```

```quiz
Q: The circuit H, S, H acts on |0⟩. What is P(0)?
- 0
* 1/2
- 0.854
- 1
E: S gives a relative phase π/2, and P(0) = cos²(π/4) = 1/2.
```

```quiz
Q: Where does S move the state |+⟩ on the Bloch sphere?
- To the north pole
* A quarter turn around z, to |+i⟩ on the +y axis
- To |−⟩ on the −x axis
E: S multiplies the |1⟩ amplitude by i, a relative phase of π/2: the azimuth turns from 0 to 90°.
```

## Summary

- Global phase is unobservable; relative phase is physical.
- Relative phase is the azimuthal angle on the Bloch sphere, changed by phase gates.
- Interference turns relative phase into measurable differences: H, P(φ), H gives P(0) = cos²(φ/2).
- This is the engine of quantum algorithms.
