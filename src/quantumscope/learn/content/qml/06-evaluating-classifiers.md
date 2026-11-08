---
title: Evaluating a classifier
area: qml
kind: lecture
order: 6
objectives: Read a confusion matrix and the measures built from it | Explain the ROC curve and what its area means | Use training, validation and test data correctly, with cross-validation and hyperparameter search
math: 06-probability
---
# Evaluating a classifier

Training makes a classifier fit its data; evaluation tells you whether it will work on data it has never seen. A single accuracy number can hide a lot, so QuantumScope's **Evaluation** tab shows several measures, a confusion matrix and an ROC curve.

## The confusion matrix

For two classes, call one positive (+1) and the other negative (−1). Every test sample falls into one of four cells:

| | predicted +1 | predicted −1 |
|---|---|---|
| **true +1** | true positives, TP | false negatives, FN |
| **true −1** | false positives, FP | true negatives, TN |

The diagonal holds the correct predictions. The measures are built from these four counts:

$$\mathrm{accuracy} = \frac{TP + TN}{TP + FN + FP + TN} \qquad \mathrm{precision} = \frac{TP}{TP + FP} \qquad \mathrm{recall} = \frac{TP}{TP + FN}$$

**Precision** asks: when the classifier says +1, how often is it right? **Recall** asks: of the real +1 samples, how many does it find? **Specificity** is recall for the negative class, $TN / (TN + FP)$. The **F1 score** combines precision and recall:

$$F_1 = \frac{2 \cdot \mathrm{precision} \cdot \mathrm{recall}}{\mathrm{precision} + \mathrm{recall}}$$

When one class is much larger, accuracy misleads: always predicting the larger class can score well while finding none of the smaller one. **Balanced accuracy**, the mean of recall and specificity, is fairer then.

## The ROC curve

A classifier's decision value $f(x)$ is a number; the predicted class is its sign. Moving the threshold from 0 trades false positives for true positives. The **ROC curve** draws this trade-off: the true-positive rate (recall) against the false-positive rate ($1 -$ specificity), for every threshold.

The **area under the curve (AUC)** has a plain meaning: it is the probability that a randomly chosen +1 sample gets a higher decision value than a randomly chosen −1 sample. An AUC of 1 means the decision values separate the classes perfectly; 0.5 is no better than guessing (the dashed diagonal).

## Three sets, three jobs

- The **training set** is what the classifier learns from.
- A **validation set**, held out from the training data, guides choices: settings, or when to stop training.
- The **test set** is used once, at the end, for the honest score.

Every time the test set influences a choice, its score becomes optimistic. That is why QuantumScope's search and cross-validation use only the training data.

## Cross-validation

One validation split can be lucky or unlucky. **Cross-validation** splits the training data into $k$ parts (folds), trains on $k - 1$ of them and checks the remaining one, $k$ times, so every sample is validated once. The result is a mean and a spread, for example 90.7% ± 3.3%. The spread matters: two settings whose means differ by less than it may not really differ.

## Hyperparameter search

Settings such as the bandwidth, the feature map or $C$ are **hyperparameters**: chosen by you, not learned. A **search** cross-validates every combination and picks the best. But choosing the best of many noisy estimates favours one that was lucky, so the winner's cross-validated score tends to be optimistic. In one MNIST 3-versus-8 search, the best setting scored 92% in cross-validation and 88% on the test set. The test set, untouched by the search, gives the honest number.

## Early stopping

A variational classifier can keep improving on its training data while getting worse on new data: it starts to overfit. **Early stopping** watches the loss on validation data, stops when it has not improved for a while, and keeps the best step. In QuantumScope, set a **Validation share** and **Early stopping** in the Variational Classifier; the validation curves appear dashed beside the training curves.

[Try it: evaluate and search in the Quantum Kernel Classifier](qs:open/qml_kernel)

## Check your understanding

```quiz
Q: A classifier predicts +1 for 40 samples, of which 30 really are +1; there are 50 real +1 samples. What are its precision and recall?
- Precision 60%, recall 75%
* Precision 75%, recall 60%
- Precision 80%, recall 75%
E: Precision = 30 / 40 = 75% (of its +1 predictions, how many are right); recall = 30 / 50 = 60% (of the real +1 samples, how many it found).
```

```quiz
Q: Why can the best setting from a hyperparameter search score lower on the test set than in cross-validation?
* Picking the best of many noisy estimates favours one that was lucky, so its cross-validated score is optimistic
- Cross-validation uses the test set
- The test set is always harder
E: Each cross-validated score has its own uncertainty; the maximum of many such scores is biased upwards. The untouched test set gives the honest estimate.
```

## Summary

- The confusion matrix counts the four kinds of outcome; precision, recall, specificity, F1 and balanced accuracy are built from it.
- The AUC is the probability that a random +1 sample scores above a random −1 sample.
- Train on the training set, choose with validation or cross-validation, and score once on the test set.
