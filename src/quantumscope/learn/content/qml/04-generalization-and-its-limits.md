---
title: Generalization, bandwidth and kernel concentration
area: qml
kind: lecture
order: 4
objectives: Recognize overfitting in decision regions | Use the bandwidth to control a kernel | Explain kernel concentration and the effect of shot noise
math: 06-probability
---
# Generalization, bandwidth and kernel concentration

## The idea

A classifier is only useful if it **generalizes**: if it is right on new data, not just on the points it learned from. Quantum kernels make this both easy to see and easy to get wrong. One setting, the **bandwidth**, controls how sharply the kernel tells points apart; too sharp and the model memorizes noise, and with many qubits every point starts to look unrelated to every other.

## Overfitting

A classifier **overfits** when it learns the training points too exactly, noise included. In the decision regions this shows as **islands**: small patches of one class around single training points. Training accuracy is then high, while test accuracy drops.

## Bandwidth

QuantumScope's **bandwidth** $\beta$ scales the data before encoding, $x \to \beta x$ (Shaydulin and Wild, 2022). For angle encoding, for instance,

$$K_\beta(x, x') = \prod_k \cos^2\frac{\beta\,(x_k - x'_k)}{2}$$

so a small $\beta$ makes the kernel change slowly: nearby points look similar, and the boundary becomes smoother. A large $\beta$ makes it change fast, which can capture fine detail but also invites overfitting. No single value is best: on two Iris species the ZZ map goes from 75% test accuracy at $\beta = 1$ to 100% at $\beta = 0.1$, while the circles need a large $\beta$. The bandwidth has to be chosen for the data, like any other model setting.

## Kernel concentration

With an entangling feature map on more qubits, a serious problem appears: the states of different data points become almost orthogonal, so

$$K(x, x') \approx 0 \quad \text{for almost every pair } x \neq x'$$

This is **kernel concentration** (Thanasilp et al., 2024). The kernel matrix looks like the identity, the classifier learns little more than "every point is different", and on hardware the tiny values are lost in shot noise. QuantumScope warns when the average kernel value of different points falls below 0.05; a smaller bandwidth usually helps.

## Shot noise

On a quantum computer each kernel value is estimated from $N$ shots, with an error of about $\sqrt{K(1-K)/N}$. Small kernel values are therefore the hardest to measure, which is exactly where concentration pushes them.

## An honest outlook

For small, classical datasets like these, quantum kernels are **not known to beat** good classical methods: the classical Gaussian (RBF) kernel is a strong baseline. Researchers look for advantages in data with a quantum structure, or in problems that are hard to simulate classically. QuantumScope is for understanding how these methods work, and why their settings matter.

## Worked example

Two points differ by 0.5 in one feature, with angle encoding:

| Bandwidth β | $K = \cos^2(0.25\,\beta)$ |
|---|---|
| 0.1 | 0.999 |
| 1 | 0.939 |
| 4 | 0.292 |

Now take 8 qubits where each feature contributes a factor 0.7: $K = 0.7^8 \approx 0.058$, already near the warning level. Measured with 1,000 shots its error is $\sqrt{0.058 \times 0.942 / 1000} \approx 0.007$, about 13% of the value itself. Halving the bandwidth raises each factor and the product with it.

## Common mistakes

- **Tuning the bandwidth on the test set.** Choose it with cross-validation on the training data; otherwise the test score is no longer honest.
- **Blaming the classifier for concentration.** When all kernel values are tiny, no classifier can learn; fix the kernel (bandwidth, qubits, feature map) first.
- **Expecting a quantum advantage on toy data.** These datasets are for learning the methods; classical kernels do as well or better on them.

## In the app

In the **Quantum Kernel Classifier**, choose Iris with the **ZZ feature map** and train at **Bandwidth** 1, then 0.1: compare the test accuracy and the decision regions. Raise the bandwidth on a noisy dataset to grow islands. Lower **Shots per entry** to see shot noise speckle the kernel heatmap, and watch for the concentration warning with more qubits.

[Try it: compare bandwidths on Iris with the ZZ feature map](qs:open/qml_kernel)

## Check your understanding

```quiz
Q: Training accuracy 100%, test accuracy 70%, and islands in the decision regions. What is happening?
* Overfitting: the classifier memorized the training points
- The test set is broken
- The kernel is concentrated, so it underfits
E: Islands around single training points, with a large gap between training and test accuracy, are the signs of overfitting.
```

```quiz
Q: The kernel matrix is close to the identity. What should you try?
- More shots only
* A smaller bandwidth (or fewer qubits, or a simpler feature map)
- A larger bandwidth
E: Near-zero kernel values for different points are kernel concentration; scaling the data down makes nearby states overlap again.
```

```quiz
Q: Which kernel values are hardest to measure accurately relative to their size?
- Values near 1
* Small values near 0
- Values near 0.5
E: The error √(K(1−K)/N) shrinks more slowly than K itself, so small values have the largest relative error.
```

```quiz
Q: How should the bandwidth be chosen?
- Always 1
- To maximize test accuracy
* By cross-validation on the training data
E: Choosing settings with the test set leaks it into the model; cross-validation keeps the test score honest.
```

## Summary

- Overfitting shows as islands and a gap between training and test accuracy.
- The bandwidth controls how fast the kernel varies; choose it for the data, with cross-validation.
- Kernel concentration makes different points look unrelated, and shot noise hides small kernel values.
- On small classical data, quantum kernels are tools for learning, not proven winners.
