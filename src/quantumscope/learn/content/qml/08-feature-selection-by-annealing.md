---
title: Choosing features by annealing
area: qml
kind: lecture
order: 8
objectives: Write feature selection as an Ising problem | Explain how relevance, redundancy and the penalty shape the answer | Use an annealer as it is used in practice, by reading many times | Judge honestly what annealing adds here
math: 06-probability, 12-gradients-and-optimization
---
# Choosing features by annealing

## The idea

A quantum classifier needs one qubit per feature, so a dataset with 30 measurements must be cut down to a few. PCA does this by mixing all 30 into new components, which nobody can measure or explain. **Feature selection** instead keeps a few of the original measurements. Choosing the best k of n features is a search over all subsets, and it can be written as an Ising problem: exactly the kind of problem a quantum annealer is built to solve. Companies and researchers have run it on real annealers, for example to choose the inputs of credit-scoring models.

## Two things a good choice needs

**Relevance.** A feature is relevant when, on its own, it separates the classes. QuantumScope measures this with the correlation ratio

$$r_i = \eta_i = \sqrt{\frac{\text{variance of the class means of feature } i}{\text{variance of feature } i}}$$

which runs from 0 (no help) to 1 (the classes do not overlap at all). For two classes it equals the absolute correlation between the feature and the label.

**Low redundancy.** Two features that measure the same thing waste a qubit. The redundancy of features i and j is their absolute correlation $R_{ij} = |\mathrm{corr}(x_i, x_j)|$. In the breast cancer data, the radius, perimeter and area of a cell nucleus have $R \approx 0.99$: once one is kept, the others add almost nothing.

Choosing the k most relevant features one by one (**greedy** selection) ignores redundancy, and can spend its whole budget on near-copies.

## Feature selection as an Ising problem

Give each candidate feature a bit $x_i$: 1 keeps it, 0 leaves it out. The energy of a choice is

$$E(x) = -\alpha \sum_i r_i x_i + (1 - \alpha) \sum_{i<j} R_{ij}\, x_i x_j + \lambda \left(\sum_i x_i - k\right)^2$$

- The first term rewards relevant features; the second charges for every pair that repeats each other.
- $\alpha$ sets the balance: $\alpha = 1$ is greedy selection; lower values avoid redundancy more.
- The **penalty** $\lambda$ makes any choice of a size other than k cost more, so the lowest energy keeps exactly k.

With $x_i = (1 - Z_i)/2$, this becomes a sum of $Z_i$ and $Z_i Z_j$ terms: an Ising problem with one spin per candidate. The anneal starts in the ground state of the driver and slowly switches this problem on. This is a QUBO (quadratic unconstrained binary optimization), the form used by Mücke et al. (2023).

## Reading many times

Good feature choices are often nearly tied: keeping the radius instead of the perimeter changes the energy very little. Nearly tied answers mean a tiny gap at the end of the anneal, so a single anneal finds the very best choice only a few percent of the time. Real annealers are used the same way for this reason: they anneal and measure many times (**reads**) and keep the lowest-energy choice seen. With 100 reads, an answer found 4% of the time is seen about 98% of the time. Too fast an anneal, though, leaves the spins nearly random: few reads even keep exactly k features.

## The penalty is a balancing act

If $\lambda$ is too small, the lowest energy keeps more or fewer than k features. If it is too large, it dominates every coefficient: the differences between good and bad choices become tiny by comparison, and so does the gap. QuantumScope uses 1.5 times the smallest penalty that still gives exactly k.

## Worked example

Three candidates, keep $k = 2$, with $\alpha = 0.7$:

| | relevance | redundancy |
|---|---|---|
| feature 1 | 0.80 | $R_{12} = 0.95$ |
| feature 2 | 0.75 | $R_{13} = 0.20$ |
| feature 3 | 0.50 | $R_{23} = 0.25$ |

Every pair keeps two features, so the penalty is 0 for all of them:

$$E_{12} = -0.7(0.80 + 0.75) + 0.3(0.95) = -0.800$$
$$E_{13} = -0.7(0.80 + 0.50) + 0.3(0.20) = -0.850$$
$$E_{23} = -0.7(0.75 + 0.50) + 0.3(0.25) = -0.800$$

The lowest energy keeps features 1 and 3. Greedy selection would keep 1 and 2, the two most relevant, even though they are near-copies. With $\alpha = 1$ the redundancy term vanishes and $E_{12} = -1.55$ wins.

## Common mistakes

- **Computing relevance on all the data.** The choice would then have seen the test samples, and the test accuracy would be too optimistic. QuantumScope uses the training split only.
- **Treating the lowest energy as the highest accuracy.** The energy is a stand-in for accuracy. The chosen features are a sensible, non-redundant set, not a guarantee of the best score.
- **Expecting a quantum speed-up here.** With 10 candidates there are 1,024 choices, which a laptop checks in a millisecond. Annealing matters only for hundreds of candidates, and even there, whether quantum annealers beat good classical heuristics is an open question.
- **Taking one read.** A single anneal is a random draw. Read many times and keep the best.

## In the app

In **Quantum annealing**, choose the problem **Feature selection (from data)**. Pick the data (a built-in dataset, or **From the Datasets tab**, which includes your own CSV), how many features to keep, $\alpha$, and up to 10 candidates. **Anneal** shows the spectrum and the anneal as for any problem; **Chosen features** shows the relevance of each candidate, the redundancy between them, and a table comparing the annealed choice with greedy selection, PCA and all candidates, scored on the test samples. **Use these features in the Datasets tab** prepares the data with them, for both classifiers. In the Datasets tab, **Choose by annealing…** does the same in the other direction.

[Try it: choose features by annealing](qs:open/annealing)

[Open the Datasets experiment](qs:open/qml_datasets)

## Check your understanding

```quiz
Q: Why can greedy selection (the k most relevant features) be a poor choice?
- It always picks irrelevant features
* It ignores redundancy, so it may keep several features that measure the same thing
- It cannot handle more than two classes
E: Radius, perimeter and area are all highly relevant and almost identical; keeping all three wastes two qubits.
```

```quiz
Q: What does the penalty λ(Σxᵢ − k)² do in the energy?
* It makes every choice that does not keep exactly k features cost more
- It rewards relevant features
- It charges for redundant pairs
E: Without it, the lowest energy might keep every relevant feature, or none.
```

```quiz
Q: A single anneal finds the best choice only 4% of the time. How is an annealer used anyway?
- The problem must be changed until the success is 100%
* Anneal and measure many times, and keep the lowest-energy valid choice seen
- Use the most likely bitstring of one run, whatever it is
E: With 100 reads, the chance of never seeing a 4% answer is 0.96¹⁰⁰ ≈ 2%.
```

```quiz
Q: Why is there no quantum advantage in the app's feature selection?
- Annealing cannot solve feature selection
* With at most 10 candidates, all 1,024 choices can be checked directly by a classical computer
- The simulation uses classical noise
E: Annealing is worth considering only for many candidates; even then, an advantage over classical methods is not established.
```

```quiz
Q: In the worked example, what does lowering α from 1 to 0.7 change?
- Nothing: the most relevant pair always wins
* Redundancy starts to count, and the pair of near-copies (1 and 2) loses to features 1 and 3
- The penalty disappears
E: At α = 1 only relevance counts and E₁₂ is lowest; at 0.7 the 0.95 correlation costs 0.285, enough to lose.
```

## Summary

- Feature selection keeps a few original, measurable features; PCA mixes them all.
- Energy: −α·relevance + (1 − α)·redundancy + a penalty for not keeping exactly k; its lowest state is the choice.
- Nearly tied choices make the gap tiny: read many times and keep the best.
- Choose from the training split only, and judge the choice by test accuracy.
- At 10 candidates this is a lesson in formulation, not a speed-up.
