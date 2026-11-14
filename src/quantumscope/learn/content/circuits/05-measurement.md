---
title: Measurement in circuits
area: circuits
kind: lecture
order: 5
objectives: Predict measurement probabilities from amplitudes | Compute the outcome distribution of measuring some of the qubits | Explain why finite shots only estimate probabilities
math: 02-vectors-and-dirac-notation, 06-probability
---
# Measurement in circuits

## The idea

A circuit's state holds many amplitudes, but a measurement returns one bit string. Which one is random, with probabilities set by the amplitudes. This lecture covers what you get when you measure all qubits or only some of them, what happens to the rest, and how to read the counts from many shots.

## Measuring every qubit

Measuring all qubits of $|\psi\rangle = \sum_x c_x|x\rangle$ gives the bit string $x$ with probability $|c_x|^2$. The state afterwards is $|x\rangle$: measurement **collapses** the superposition, so a measurement is usually the last thing that happens to a qubit. Measuring in the middle of a circuit, and using the result, is the subject of *Mid-circuit measurement*.

## Measuring some of the qubits

If you measure only q0, the probability of outcome $b$ adds up every basis state in which q0 equals $b$:

$$P(q_0 = b) = \sum_{x:\ x_0 = b} |c_x|^2$$

For the Bell pair, $P(q_0 = 0) = P(q_0 = 1) = \frac{1}{2}$, even though the pair is in a single, definite (pure) state. Put **M** gates only on the qubits you want to measure; the histogram then shows just those outcomes.

[Try it: a Bell pair, measuring q0 only](qs:circuit?n=2&gates=H:0;CX:0,1)

## Shots and statistics

A real experiment repeats the circuit many times (**shots**) and counts outcomes. With $N$ shots, an outcome of probability $p$ appears about $Np$ times, with a typical fluctuation of

$$\sqrt{Np(1-p)}$$

For $p = \frac{1}{2}$ and $N = 1024$ that is about 16 counts, so seeing 497 instead of 512 is perfectly normal. **Run shots** in the circuit tab samples from the exact probabilities, so the counts fluctuate the same way.

## Worked example

Take the two-qubit state with amplitudes $0.6$ for $|00\rangle$, $0$ for $|01\rangle$, $0.48$ for $|10\rangle$ and $0.64$ for $|11\rangle$ (q0 written first). It is normalized: $0.36 + 0.2304 + 0.4096 = 1$.

- Measuring q0 only: $P(q_0 = 1) = 0.48^2 + 0.64^2 = 0.64$.
- Measuring q1 only: $P(q_1 = 1) = 0^2 + 0.64^2 \approx 0.41$.

If q0 gives 1, the amplitudes with $q_0 = 0$ vanish and the rest are renormalized by $\sqrt{0.64} = 0.8$: q1 is left in $0.6|0\rangle + 0.8|1\rangle$. Measuring one qubit changed what we know about the other.

## Common mistakes

- **Forgetting to add up the matching amplitudes.** The probability for one qubit sums $|c_x|^2$ over every basis state with that qubit's value.
- **Forgetting to renormalize after a partial measurement.** The remaining amplitudes must be divided by the square root of the outcome's probability.
- **Reading small differences in counts as real.** 497 out of 1024 is normal for a 50:50 outcome.

## In the app

Place **M** gates on the qubits you want to measure and press **Run shots**: the histogram shows only the measured qubits' outcomes, while the State Inspector still shows the full state. Run the shots a few times to see the counts fluctuate by about $\sqrt{Np(1-p)}$.

## Check your understanding

```quiz
Q: A 2-qubit state has amplitudes 1/2 on each of |00⟩, |01⟩, |10⟩, |11⟩. What is P(q0 = 1)?
- 1/4
* 1/2
- 3/4
- 1
E: Add the probabilities of |10⟩ and |11⟩: 1/4 + 1/4 = 1/2.
```

```quiz
Q: You run 100 shots of a circuit with P(0) = 0.5. Which result is most suspicious?
- 46 zeros
- 55 zeros
* 80 zeros
E: The expected spread is √(100 · 0.5 · 0.5) = 5 counts, so 80 is six spreads away from 50.
```

```quiz
Q: In a GHZ state (|000⟩ + |111⟩)/√2, q0 is measured and gives 1. What is the state of q1 and q2?
* |11⟩
- (|00⟩ + |11⟩)/√2
- |00⟩
E: Only |111⟩ has q0 = 1, so after renormalizing, the other two qubits are certainly |11⟩.
```

```quiz
Q: An outcome has probability 0.2. About how many times does it appear in 500 shots?
- Exactly 100
* About 100, give or take 9
- About 100, give or take 50
E: Np = 100 and √(Np(1 − p)) = √80 ≈ 9.
```

## Summary

- Measuring all qubits gives x with probability |cₓ|², and the state collapses to |x⟩.
- Measuring some qubits sums the probabilities over the unmeasured ones.
- Finite shots estimate probabilities, with fluctuations of about √(Np(1−p)).
