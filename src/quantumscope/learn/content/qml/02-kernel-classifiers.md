---
title: Kernel classifiers and the SVM
area: qml
kind: lecture
order: 2
objectives: Explain the kernel trick | Describe kernel ridge classification | Explain the margin, support vectors and C of a support vector machine
math: 02-vectors-and-dirac-notation, 12-gradients-and-optimization
---
# Kernel classifiers and the SVM

## The idea

Once every pair of data points has a kernel value, the quantum part is done. A classical method then learns from the **kernel matrix** alone: this is the **kernel trick**. It lets a classifier work in the huge space of quantum states without ever writing those states down. A new point is classified by how similar it is to the training points of each class.

## Labels, training and testing

Each data point has a label $y = +1$ or $-1$ (the two classes). The data is split into a **training set**, used to learn, and a **test set**, kept aside to measure how well the classifier does on points it has never seen. Accuracy on the test set is the honest score; accuracy on the training set can be misleadingly high.

## Kernel ridge classification

Kernel ridge looks for a decision function built from the training points,

$$f(x) = \sum_i \alpha_i\, K(x, x_i)$$

and predicts the class $\mathrm{sign}\, f(x)$. The weights have a closed form,

$$\alpha = (K + \lambda I)^{-1} y$$

where $K$ is the training kernel matrix and $\lambda > 0$ is a **regularization** strength: larger $\lambda$ gives a smoother, more cautious classifier.

## Support vector machines

A **support vector machine** (SVM; Cortes and Vapnik, 1995) looks for the boundary with the widest **margin**: the largest gap between the classes. Its decision function has the same shape plus a bias,

$$f(x) = \sum_i \alpha_i y_i\, K(x, x_i) + b$$

but most weights $\alpha_i$ come out exactly 0. The points with $\alpha_i > 0$ are the **support vectors**: the points on or inside the margin, which alone define the boundary. The constant $C$ bounds the weights, $0 \leq \alpha_i \leq C$: a large $C$ insists on classifying every training point correctly, a small $C$ tolerates a few mistakes for a wider margin.

QuantumScope finds the weights with Platt's SMO algorithm (1998), which updates two weights at a time until the optimality conditions hold.

## Worked example

Kernel ridge with two training points, $y = (+1, -1)$, kernel $K(x_1, x_2) = 0.2$ and $\lambda = 0.1$:

$$K + \lambda I = \begin{pmatrix} 1.1 & 0.2 \\ 0.2 & 1.1 \end{pmatrix}, \qquad \alpha = \frac{1}{1.17}\begin{pmatrix} 1.1 & -0.2 \\ -0.2 & 1.1 \end{pmatrix}\begin{pmatrix} 1 \\ -1 \end{pmatrix} \approx \begin{pmatrix} 1.11 \\ -1.11 \end{pmatrix}$$

A new point with $K(x, x_1) = 0.7$ and $K(x, x_2) = 0.3$ gets $f(x) = 1.11 \times 0.7 - 1.11 \times 0.3 \approx 0.44 > 0$: class $+1$, because it resembles $x_1$ more. A point equally similar to both would get $f = 0$, right on the boundary.

## Common mistakes

- **Judging by training accuracy.** 100% on the training set can mean memorization; the test set tells the truth.
- **Setting C very high "to be accurate".** A huge $C$ bends the boundary around every noisy point and usually lowers test accuracy.
- **Thinking every training point matters to an SVM.** Removing a point with $\alpha_i = 0$ leaves the boundary unchanged.

## In the app

The **Quantum Kernel Classifier** shows the **decision regions**: the background colour is the class $f$ predicts, deeper where the classifier is more confident, with the boundary $f = 0$ as a white line. Training points are dots, test points triangles, and mistakes are marked ✕. Switch between **Kernel ridge** and **SVM** and change **C or λ**: watch the boundary smooth out or bend. With more than two features, the regions are drawn in the plane of the two leading principal components, a slice through the data.

[Try it: separate the circles with a kernel](qs:open/qml_kernel)

## Check your understanding

```quiz
Q: Which points define an SVM's decision boundary?
- All training points equally
* The support vectors (the points with αᵢ > 0)
- The test points
E: Points with αᵢ = 0 do not appear in f(x) at all; only the support vectors do.
```

```quiz
Q: Why is the test accuracy the honest score?
* The test points were never used for learning
- The test set is larger
- The test points are easier
E: A classifier can memorize its training points; only unseen points show whether it has learned the pattern.
```

```quiz
Q: In kernel ridge, what does a larger λ do?
- Makes the classifier fit every training point exactly
* Makes the decision function smoother and more cautious
- Adds more qubits
E: λ is added to the kernel matrix's diagonal before inverting, which shrinks the weights and smooths f.
```

```quiz
Q: Where does the quantum computer appear in a kernel classifier?
* Only in computing the kernel values K(x, x′)
- In every step of the SVM's optimization
- In predicting the class sign f(x)
E: After the kernel matrix is measured, training and prediction are classical: the kernel trick.
```

## Summary

- The kernel trick: a classical method learns from the kernel matrix alone.
- Kernel ridge: $\alpha = (K + \lambda I)^{-1} y$; an SVM maximizes the margin, and only its support vectors matter.
- C and λ trade fitting the training points against a smoother boundary.
- Judge a classifier by its test accuracy, not its training accuracy.
