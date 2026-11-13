---
title: Measurement and the Born rule
area: principles
kind: lecture
order: 2
objectives: Compute measurement probabilities along any axis | Describe the state after a measurement | Explain why repeated measurements are needed to learn a state
math: 02-vectors-and-dirac-notation, 06-probability
---
# Measurement and the Born rule

## The idea

A quantum state holds amplitudes, but a measurement never shows them. It gives one definite result, chosen at random, and changes the state to match. The **Born rule** says how likely each result is. Everything we learn about quantum systems comes from repeating measurements and counting.

## The Born rule

Measuring a state $|\psi\rangle$ in a basis $\{|b\rangle\}$ gives outcome $b$ with probability

$$P(b) = |\langle b|\psi\rangle|^2$$

and leaves the system in $|b\rangle$. The probabilities add up to one because the state is normalized.

## Measuring along any axis

Measuring a spin along a direction $\hat n$ gives "up" with probability

$$P(\uparrow_{\hat n}) = \frac{1 + \vec r\cdot\hat n}{2}$$

where $\vec r$ is the Bloch vector. A state pointing along $\hat n$ is always "up"; one pointing the opposite way is always "down"; one at right angles is 50:50.

## Collapse and repetition

After the measurement the state *is* the outcome, so measuring again along the same axis repeats the result. The original amplitudes cannot be read from a single measurement; they are estimated by preparing the same state many times — the shots in a circuit simulation. With $N$ shots, a probability $p$ is estimated to within about $\sqrt{p(1-p)/N}$.

## Measuring in other bases with gates

Circuits measure in the computational ($z$) basis. To measure along $x$, apply H first; to measure along $y$, apply S† and then H. Gates rotate the state so that the axis you care about lines up with $z$.

## Worked example

A spin is prepared at $60°$ from $+z$, tilted toward $+x$, so $\vec r = (\sin 60°, 0, \cos 60°) \approx (0.866, 0, 0.5)$.

- Along $z$: $P(\uparrow) = (1 + 0.5)/2 = 0.75$.
- Along $x$: $P(\uparrow) = (1 + 0.866)/2 \approx 0.933$.
- Along $-z$: $P(\uparrow) = (1 - 0.5)/2 = 0.25$, the same as "down" along $z$, as it must be.

With 1,000 shots along $z$ you expect about 750 "up" results, give or take $\sqrt{1000 \times 0.75 \times 0.25} \approx 14$. Seeing 739 or 762 is normal; seeing 600 means the state is not what you think.

## Common mistakes

- **Squaring the amplitude without its modulus.** For an amplitude $i/\sqrt{2}$, the probability is $|i/\sqrt{2}|^2 = 1/2$, not $i^2/2 = -1/2$.
- **Expecting exact frequencies.** 1,000 shots of a 50:50 state rarely give exactly 500. Differences of a few percent are statistics, not errors.
- **Measuring again to "check".** A second measurement along the same axis only repeats the first result; it says nothing new about the original state.

## In the app

In **Quantum Principles → Superposition**, prepare θ = 60°, φ = 0°, and set the **Axis** (0° is $z$, 90° is $x$). The panel shows the Born-rule probabilities; **Measure once** collapses the arrow onto the axis, and **Measure many** measures fresh copies and builds the histogram. In a circuit, more shots make the histogram approach the State Inspector's exact probabilities.

[Try it: measure spin along different axes](qs:open/superposition)

[Try it: |+⟩ is certain along x](qs:circuit?n=1&gates=H:0;H:0&inspector=1)

## Check your understanding

```quiz
Q: A spin points along +x. You measure along +z. What is P(up)?
- 0
* 1/2
- 1
E: r·n = 0 for perpendicular directions, so P = (1 + 0)/2 = 1/2.
```

```quiz
Q: How do you measure a qubit along x in a circuit?
* Apply H, then measure
- Apply X, then measure
- Measure twice
E: H swaps the x and z axes, so the x-basis states |+⟩ and |−⟩ become |0⟩ and |1⟩.
```

```quiz
Q: A measurement along z gives "up". You measure along z again at once. What happens?
- "Up" or "down", 50:50
* "Up" again, with certainty
- "Down", since the state flipped
E: After the first measurement the state is |0⟩, so the same measurement repeats the result.
```

```quiz
Q: The state (|0⟩ + i√3|1⟩)/2 is measured in the computational basis. What is P(1)?
- −3/4
- √3/2
* 3/4
- 1/4
E: P(1) = |i√3/2|² = 3/4. The modulus removes the i; probabilities are never negative.
```

## Summary

- P(b) = |⟨b|ψ⟩|²; afterwards the state is |b⟩.
- Along an axis n̂, P(up) = (1 + r·n̂)/2.
- One measurement reveals one outcome; probabilities need many repetitions, with a spread of about √(p(1−p)/N).
- Gates before measurement select the measurement basis.
