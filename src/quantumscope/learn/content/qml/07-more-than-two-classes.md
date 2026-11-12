---
title: More than two classes
area: qml
kind: lecture
order: 7
objectives: Build a k-class classifier from binary ones (one-vs-rest) | Read a k × k confusion matrix and macro-averaged measures | Judge a multi-class score against chance and class imbalance
math: 06-probability
---
# More than two classes

An SVM answers a yes-or-no question: which side of a boundary is a point on? Many real questions have more answers: which of ten digits, which of three penguin species, which of six kinds of glass. QuantumScope's **Quantum Kernel Classifier** handles them by choosing **All classes** under Classes.

## One-vs-rest

The simplest way to build a $k$-class classifier from binary ones is **one-vs-rest**: train one classifier per class $c$, with that class as $+1$ and every other class as $-1$. Each gives a decision value $f_c(x)$, a measure of how confidently $x$ belongs to $c$. The prediction is the most confident class:

$$\hat{y}(x) = \mathrm{argmax}_c \, f_c(x)$$

For a quantum kernel this costs almost nothing extra. The kernel $K(x, x')$ depends only on the data, not on the labels, so all $k$ classifiers share **one** kernel matrix: the circuits are run once, and only the cheap classical training is repeated $k$ times.

An alternative, **one-vs-one**, trains a classifier for every pair of classes, $k(k-1)/2$ of them (45 for ten digits), and lets them vote. Each is trained on less data, but there are many more of them.

## Regions and boundaries

With two classes there is one boundary, where $f(x) = 0$. With $k$ classes, the space is divided into $k$ regions: class $c$ wins where $f_c(x)$ is larger than every other $f_{c'}(x)$, and the boundaries lie where two classes are equally confident. In the **Decision regions** and **3-D view**, each region takes its class's colour.

## Measuring success

**Chance is lower.** Guessing is right half the time with two balanced classes, but only $1/k$ of the time with $k$. So 60% accuracy on ten classes is far better than 60% on two.

**The confusion matrix is $k \times k$.** Each row is a true class and each column a predicted one; the diagonal holds the right answers. It shows *which* classes are confused: for handwritten digits, often 4, 7 and 9, which can look alike.

**Per-class measures, then averages.** Precision, recall and $F_1$ are computed for each class, treating it as positive and the rest as negative. Their plain average over the classes is the **macro average**: every class counts equally, however many samples it has. The **balanced accuracy** is the macro-averaged recall:

$$\mathrm{balanced\ accuracy} = \frac{1}{k}\sum_{c=1}^{k} \mathrm{recall}_c$$

**One ROC curve per class.** Each class's curve compares its decision value $f_c$ for its own samples with that for the others; QuantumScope reports the mean of their areas.

## Unbalanced classes

In the **Glass** dataset, building windows have 70 and 76 samples, while tableware has only 9. A classifier that never predicts the small classes still scores well on plain accuracy. The balanced accuracy and the confusion matrix expose it. QuantumScope's checker leaves out classes with fewer than 10 samples, too few to both learn from and test, and caps the samples per class so that the rest are better balanced.

## Easy and hard datasets

| Dataset | Classes | What makes it hard |
|---|---|---|
| Iris, Seeds | 3 | little: well separated |
| Palmer Penguins | 3 | missing values and text columns to prepare |
| Glass | 6 | few samples, unbalanced, overlapping classes |
| Digits, MNIST | 10 | many classes, from images, on few qubits |
| Fashion-MNIST | 10 | shirts, T-shirts, pullovers and coats look alike |

With one feature per qubit, more qubits keep more of an image's variation after PCA, and accuracy on ten classes rises with them.

[Try it: classify all three penguin species](qs:open/qml_kernel)

## Check your understanding

```quiz
Q: A one-vs-rest quantum kernel classifier separates 10 classes. How many kernel matrices must be computed on the quantum computer?
* One: the kernel depends only on the data, so all 10 classifiers share it
- Ten, one per classifier
- 45, one per pair of classes
E: The labels only enter the classical training. The same kernel matrix serves all ten one-vs-rest classifiers.
```

```quiz
Q: A ten-class classifier has 55% test accuracy. What does that say?
- It is barely better than guessing
* It is far better than guessing, which would be right about 10% of the time
- It is worse than guessing
E: With ten balanced classes, chance is 1 in 10. Always compare a score with chance for that number of classes.
```

```quiz
Q: In the confusion matrix, the row for digit 9 has 5 of its 10 samples in the column for 7. What does that mean?
* Five true 9s were predicted to be 7s
- Five true 7s were predicted to be 9s
- The classifier never predicts 9
E: Rows are true classes and columns are predictions. Whether 9 is ever predicted is read from its column, not its row.
```

```quiz
Q: Why does the balanced accuracy suit the Glass dataset better than plain accuracy?
- It ignores the small classes
* Every class counts equally, so missing the small classes is not hidden by the large ones
- It is always higher than plain accuracy
E: Balanced accuracy is the average recall over the classes. A classifier that ignores tableware and headlamps loses a whole class's share of it.
```
