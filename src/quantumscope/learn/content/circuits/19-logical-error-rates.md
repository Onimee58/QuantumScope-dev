---
title: Logical error rates and thresholds
area: circuits
kind: lecture
order: 19
objectives: Compute the logical failure rate of a repetition code | Explain when a code helps and when it hurts | Describe the idea of a threshold
math: 06-probability
---
# Logical error rates and thresholds

## The idea

A code does not make errors impossible; it makes them rarer — if the physical error rate is low enough. This lecture computes how often the bit-flip code fails, shows that a code can even make things worse against the wrong kind of noise, and introduces the **threshold** that decides whether error correction pays off.

## When does the code fail?

Suppose each data qubit independently suffers a bit flip with probability $p$. The bit-flip code fails only when two or three qubits flip:

$$P_{\mathrm{fail}} = 3p^2(1-p) + p^3 = 3p^2 - 2p^3$$

An unprotected qubit fails with probability $p$. At $p = 0.1$, the code fails with probability $0.028$ — **3.6 times less often**.

## Helping and hurting

$3p^2 - 2p^3 < p$ for every $0 < p < \frac{1}{2}$: against its own error type, the code helps right up to $p = \frac{1}{2}$, where the curves meet. Against the *wrong* error type it hurts: under phase flips, the bit-flip code fails whenever an odd number of qubits is hit,

$$P_{\mathrm{fail}} = \frac{1 - (1-2p)^3}{2} \approx 3p$$

which is worse than doing nothing. Depolarizing noise contains both kinds of error, so a repetition code alone does not help against it either.

[Try it: the Error-correction explorer](qs:open/qec)

[Try it: plot the bit-flip code with random errors](qs:algorithm/bit_flip_code?logical=0&error=random&p=0.1)

With the second link, press **Plot logical error rate** in the verification panel: the curve comes from the circuit itself, so removing a correction gate visibly raises it.

## Thresholds

Our model only puts errors on the data. In a real device the gates that measure the syndrome are faulty too, so a code only helps when the physical error rate is below a **threshold** that depends on the code and the noise. Below it, larger codes push the logical error rate down further and further; above it, adding qubits makes things worse. For the surface code, a leading candidate for large quantum computers, thresholds of around one percent are typically quoted.

## Worked example

At $p = 0.01$, the bit-flip code fails with probability

$$3p^2 - 2p^3 = 0.0003 - 0.000002 \approx 0.0003$$

about **33 times** less often than an unprotected qubit (0.01). The improvement grows as $p$ shrinks, because failure needs two errors. Against phase flips at $p = 0.1$, however, the same code fails with probability $\frac{1}{2}(1 - 0.8^3) \approx 0.244$ — more than twice as often as a bare qubit.

## Common mistakes

- **Thinking a code always helps.** Against the wrong error type, or above threshold, it makes things worse.
- **Ignoring faulty syndrome measurements.** Real thresholds include errors in the checking circuits, which is why they are low.
- **Reading 3p² as small for any p.** It beats p only when p < ½ (against its own error type); for realistic codes the bar is far lower.

## In the app

Open the **Error-correction explorer** to compare logical and physical error rates for each code and noise type. In the bit-flip code example with random errors, **Plot logical error rate** draws the curve from the circuit itself; remove a correction gate and watch it rise.

## Check your understanding

```quiz
Q: What is the bit-flip code's failure rate at p = 0.2?
- 0.2
* 0.104
- 0.04
E: 3p² − 2p³ = 3(0.04) − 2(0.008) = 0.12 − 0.016 = 0.104.
```

```quiz
Q: Why can error correction make things worse?
- More qubits always mean more errors
* Each extra qubit is another place for errors; if they are too frequent or of the wrong type, the code adds failures
- Measurement is unreliable
E: Below the threshold the code's redundancy wins; above it, the extra error opportunities win.
```

```quiz
Q: At p = 0.2, how often does the bit-flip code fail against bit flips?
- 0.2
* 0.104
- 0.04
E: 3p² − 2p³ = 0.12 − 0.016 = 0.104, about half the unprotected rate.
```

```quiz
Q: Above the threshold, what happens when a larger code is used?
- The logical error rate falls
* The logical error rate rises: more qubits bring more errors than the code can fix
- Nothing changes
E: Below threshold, bigger codes help more and more; above it, they hurt.
```

## Summary

- The bit-flip code fails with probability 3p² − 2p³ against bit flips: far better than p for small p.
- Against the wrong error type a code can be worse than nothing.
- With faulty gates, codes help only below a threshold; larger codes then keep improving.
