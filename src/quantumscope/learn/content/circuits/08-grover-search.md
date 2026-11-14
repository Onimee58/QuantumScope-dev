---
title: Grover search
area: circuits
kind: lecture
order: 8
objectives: Describe the oracle and diffusion steps | Use the geometric picture of Grover rotations | Choose the number of iterations and recognize overshooting
math: 02-vectors-and-dirac-notation, 03-matrices-acting-on-states
---
# Grover search

## The idea

Finding one marked item among $N$ takes about $N/2$ tries classically. Grover's algorithm needs only about $\sqrt{N}$ questions to the oracle. It does not look at items one by one: it repeatedly nudges amplitude toward the marked item, a rotation that must be stopped at the right moment.

## The problem

Among $N = 2^n$ items, one is **marked**, and an oracle recognizes it. Classically you need about $N/2$ guesses on average. Grover's algorithm needs about $\frac{\pi}{4}\sqrt{N}$ oracle queries.

## The two steps

Start in the uniform superposition $|s\rangle = H^{\otimes n}|0\rangle$ and repeat:

1. **Oracle:** flip the sign of the marked state $|w\rangle$.
2. **Diffusion:** reflect every amplitude about the average, $D = 2|s\rangle\langle s| - I$.

The diffusion is built as H on every qubit, X on every qubit, a multi-controlled Z, then X and H again.

## The geometric picture

Every state the algorithm visits lies in the plane spanned by $|w\rangle$ and the unmarked states. If $\sin\theta = 1/\sqrt{N}$, each oracle-plus-diffusion rotates the state by $2\theta$ towards $|w\rangle$, so after $k$ iterations

$$P(w) = \sin^2\left((2k+1)\theta\right)$$

| N | θ | Best k | P(w) at best k |
|---|---|---|---|
| 4 | 30° | 1 | 1 |
| 8 | 20.7° | 2 | 0.945 |
| 16 | 14.5° | 3 | 0.961 |

Going past the best $k$ rotates *past* $|w\rangle$, and the success probability falls again — the algorithm **overshoots**.

[Try it: Grover with 3 qubits](qs:algorithm/grover?n=3&marked=101&iterations=-1&inspector=1)

Remove one Oracle and Diffusion pair: the verification panel checks the new probability against the same formula with the smaller $k$.

## Worked example

Take $N = 4$ with $|10\rangle$ marked. All four amplitudes start at $\frac{1}{2}$.

1. The oracle flips the marked one: $(\frac{1}{2}, \frac{1}{2}, -\frac{1}{2}, \frac{1}{2})$. The average is now $\frac{1}{4}$.
2. Diffusion reflects each amplitude about the average, $a \to 2 \cdot \frac{1}{4} - a$: the unmarked ones become $0$ and the marked one $\frac{1}{2} + \frac{1}{2} = 1$.

One iteration finds the item with certainty, matching the table ($\theta = 30°$, $3\theta = 90°$). For $N = 8$ the best is $k = 2$ with $P = 0.945$; a third iteration overshoots to $\sin^2(7 \times 20.7°) \approx 0.33$.

## Common mistakes

- **Running more iterations "to be safe".** Past the best $k$ the success probability falls; Grover is a rotation, not a search that keeps improving.
- **Forgetting that the oracle only flips a sign.** The probabilities do not change until the diffusion step turns the phase into amplitude.
- **Expecting an exponential speedup.** Grover's speedup is quadratic: $\sqrt{N}$ instead of $N$.

## In the app

**Algorithms → Grover** builds the circuit for any marked string and the best number of iterations. Step through it in the State Inspector to watch the oracle flip a sign and the diffusion move amplitude. Set the iterations by hand and the verification panel compares the result with $\sin^2((2k+1)\theta)$, so you can see the overshoot.

## Check your understanding

```quiz
Q: How many iterations maximize success for N = 4?
* 1
- 2
- 4
E: θ = 30°, so after one iteration (2k + 1)θ = 90° and P = 1.
```

```quiz
Q: What happens if you run more iterations than the optimum?
- Success stays at its maximum
* Success decreases again
- The circuit fails to run
E: Each iteration rotates by 2θ; past the marked state, the overlap shrinks.
```

```quiz
Q: With N = 4 and one marked item, what does a single oracle step do to the measurement probabilities?
* Nothing: it only flips the sign of the marked amplitude
- It makes the marked item certain
- It halves the other probabilities
E: Probabilities depend on |amplitude|², which a sign flip does not change. The diffusion step turns the phase into amplitude.
```

```quiz
Q: About how many oracle queries does Grover need for N = 1,000,000 items?
- About 500,000
* About 785
- About 20
E: (π/4)√N = (π/4) × 1000 ≈ 785, against about 500,000 classical guesses on average.
```

## Summary

- Grover alternates an oracle (sign flip) and a diffusion (reflection about the mean).
- Each iteration rotates by 2θ with sin θ = 1/√N, giving P = sin²((2k+1)θ).
- About (π/4)√N iterations are optimal; more makes it worse.
