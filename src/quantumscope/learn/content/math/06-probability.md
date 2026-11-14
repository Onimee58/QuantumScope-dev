---
title: Probability for quantum experiments
area: math
kind: lecture
order: 6
objectives: Compute an expectation value and a variance | Explain why shot counts fluctuate | Estimate the standard error of an average
---
# Probability for quantum experiments

## The idea

Every quantum measurement is random, so reading experiments means reading **statistics**: averages, spreads, and how both depend on the number of repetitions. A quantum computer never hands you a probability; it hands you counts. Knowing how much counts can wobble tells you when a result is real and when it is just chance.

## Probabilities and averages

A measurement has results $x_k$ with probabilities $p_k$, where all $p_k \geq 0$ and $\sum_k p_k = 1$. The **expectation value** is the probability-weighted average:

$$\langle x \rangle = \sum_k p_k\, x_k$$

For a qubit measured along $z$ with results $+1$ and $-1$:

$$\langle Z \rangle = p_0 \cdot (+1) + p_1 \cdot (-1) = p_0 - p_1$$

So $\langle Z \rangle = 0$ for $|+\rangle$ (50/50), and $\langle Z \rangle = 1$ for $|0\rangle$.

## Variance: how much results spread

The **variance** measures the spread around the average:

$$\mathrm{Var}(x) = \langle x^2 \rangle - \langle x \rangle^2$$

For results $\pm 1$, $x^2 = 1$ always, so $\mathrm{Var} = 1 - \langle x \rangle^2$. An eigenstate has variance 0 (always the same result); $|+\rangle$ measured along $z$ has variance 1, the maximum.

## Many shots: why counts fluctuate

Repeat a measurement $N$ times ("shots") and average. The average approaches $\langle x \rangle$, but never exactly: its typical error, the **standard error**, is

$$\sigma_{\mathrm{mean}} = \sqrt{\frac{\mathrm{Var}(x)}{N}}$$

The error shrinks like $1/\sqrt{N}$: **4 times more shots halve the error**, and 100 times more shots make it 10 times smaller.

For counts, the same rule says that an outcome with probability $p$ appears about $Np$ times, give or take $\sqrt{Np(1-p)}$. With $N = 1024$ and $p = \frac{1}{2}$ that is about $512 \pm 16$, so seeing 497 is perfectly normal.

## Worked example

A qubit is measured 1,000 times: 600 zeros and 400 ones. The estimate is

$$\langle Z \rangle \approx 0.6 - 0.4 = 0.2, \qquad \mathrm{Var} \approx 1 - 0.2^2 = 0.96, \qquad \sigma_{\mathrm{mean}} \approx \sqrt{0.96/1000} \approx 0.031$$

so $\langle Z \rangle = 0.20 \pm 0.03$. Could the true value be 0, a 50:50 state? That would be more than six standard errors away: very unlikely. Could it be 0.25? That is within two errors: quite possible. To tell 0.20 from 0.25 reliably, you would need errors around 0.01, about ten times as many shots.

## Common mistakes

- **Treating a count as exact.** 497 out of 1024 does not mean the probability is 0.485; it is consistent with 0.5.
- **Doubling shots to halve the error.** Halving needs four times the shots.
- **Confusing the spread of single results with the error of the average.** Single ±1 results always spread by about 1; the average's error shrinks with $N$.

## In the app

In the circuit editor, build a circuit with an M gate and press **Run shots** several times: the counts change each time but stay within about $\sqrt{Np(1-p)}$ of $Np$. Raise the number of shots and watch the histogram settle toward the exact probabilities. The Bell-test meter in the **Entanglement** experiment shows its result as $|S| \pm$ error: the error combines the standard errors of its four correlations.

[Try it: a |+⟩ qubit — press Run shots a few times and watch the counts vary around 512](qs:circuit?n=1&gates=H:0)

[Try it in the calculator: abs(⟨0|H|0⟩)^2](qs:calc?expr=abs%28%E2%9F%A80%7CH%7C0%E2%9F%A9%29%5E2)

## Check your understanding

```quiz
Q: A qubit gives +1 with probability 0.75 and −1 otherwise. What is ⟨Z⟩?
- 0.75
* 0.5
- 0.25
E: ⟨Z⟩ = 0.75·(+1) + 0.25·(−1) = 0.5.
```

```quiz
Q: An average from 100 shots has an error of about 0.1. How many shots give an error of about 0.01?
- 1,000
* 10,000
- 200
E: The error shrinks like 1/√N: ten times smaller needs 10² = 100 times more shots.
```

```quiz
Q: What is the variance of Z for a qubit in |1⟩?
* 0
- 1
- −1
E: |1⟩ is an eigenstate of Z: every result is −1, so ⟨Z⟩² = 1 = ⟨Z²⟩ and the variance is 0.
```

```quiz
Q: An outcome has probability 0.1. About how many times does it appear in 10,000 shots?
- Exactly 1,000
* About 1,000, give or take 30
- About 1,000, give or take 300
E: Np = 1,000 and √(Np(1 − p)) = √900 = 30.
```

## Summary

- Expectation value: $\langle x \rangle = \sum_k p_k x_k$; for $\pm 1$ results, $\langle Z \rangle = p_0 - p_1$.
- Variance $\langle x^2 \rangle - \langle x \rangle^2$ measures the spread; eigenstates have none.
- Averages of $N$ shots have errors that shrink like $1/\sqrt{N}$; counts vary by about √(Np(1 − p)).
