---
title: Preparing real data
area: qml
kind: lecture
order: 5
objectives: Explain why real data rarely fits a quantum model as it is | Use PCA to reduce features to qubits | Explain why preprocessing is fitted on the training data only
math: 06-probability, 05-eigenvalues
---
# Preparing real data

## The idea

Built-in toy datasets fit a quantum model as they are; real data almost never does. It has too many columns, too many rows, text, gaps and wildly different scales, while a quantum model wants a few numbers per point, each turned into an angle. Preparing data is ordinary data science, with one rule that matters above all: every learned step is fitted on the training data only.

## What the checker looks for

The **Datasets** experiment checks a dataset, says what stands in the way, and suggests a fix for each problem.

| Problem | Why it matters | The usual fix |
|---|---|---|
| more features than qubits | one feature per qubit | **PCA**, or choosing features |
| many samples | a kernel compares every pair: $N^2$ circuits | balanced **subsampling** |
| more than two classes | the variational classifier separates two | **All classes** (kernel classifier, one-vs-rest), or two |
| text columns | circuits need numbers | encode as numbers, or drop |
| missing values | a gap has no angle | drop those samples, or fill with the mean |
| different scales | angles must lie in $[0, \pi]$ | **scale** each feature |

## PCA: from pixels to qubits

An MNIST image has 784 pixels, far more than ten qubits. **Principal component analysis** finds the directions in which the data varies most: the eigenvectors of the data's covariance matrix, with the largest eigenvalues first. Keeping the first $k$ components replaces 784 numbers by $k$ while keeping as much of the variation as possible. For MNIST 0s and 1s, 4 components keep about half of the variance, which is plenty to tell them apart.

Some pixels, near the image borders, are always black; they carry no information and are dropped first.

## Fit on the training data only

Every learned step (the column means for missing values, the PCA directions, the scaling range) is computed from the **training** split only, and then applied unchanged to the test split. Computing them from all the data would let information about the test points leak into the model, and the test accuracy would look better than it really is. This is called **data leakage**, and QuantumScope's preparation avoids it by splitting first.

## Your own data

**Import CSV or .npz…** reads your own files: a CSV with a header (the label column is found by name, such as *label*, *target* or *class*, or is the last column), or a NumPy file with arrays named X and y. The checker then works on it like any built-in dataset.

## Worked example

Scale Iris's sepal length to an angle. In the training split it runs from 4.3 cm to 7.9 cm, so

$$\theta = \pi\,\frac{x - 4.3}{7.9 - 4.3}, \qquad x = 6.1\ \mathrm{cm} \ \Rightarrow\ \theta = \pi\,\frac{1.8}{3.6} = \frac{\pi}{2}$$

A test flower is scaled with the *same* 4.3 and 7.9, even if it measures 8.1 cm and lands slightly beyond $\pi$. The same holds for a missing value: it is filled with the training mean, never with a mean that includes test rows.

## Common mistakes

- **Scaling or PCA before splitting.** The test set then shapes the model, and the score is optimistic.
- **Keeping the first k columns instead of PCA.** The first columns are an accident of the file; PCA keeps the most informative directions.
- **Subsampling one class only.** Keep the classes balanced, or the classifier learns to prefer the larger one.

## In the app

Open the **Datasets** experiment, pick MNIST, and read the checker's list. Press **Apply suggestions** to fill in **PCA components**, **Samples per class** and **Scale each feature to [0, π]**, then **Prepare**. The prepared data can be sent to either classifier. Try **Import CSV or .npz…** with your own file to see which problems it reports.

[Try it: check and prepare MNIST in the Datasets experiment](qs:open/qml_datasets)

## Check your understanding

```quiz
Q: Why are the PCA directions computed from the training data only?
* So that no information from the test points leaks into the model
- Because the test data has no labels
- Because PCA needs exactly 150 points
E: The test set must stay unseen until it is used for the score; fitting any step on it makes the score optimistic.
```

```quiz
Q: A dataset has 30 features and you have 4 qubits. What does the checker suggest?
- Use the first 4 columns
* Reduce to 4 features with PCA
- Use 30 qubits
E: PCA keeps the 4 directions of greatest variation, usually far more informative than the first 4 columns.
```

```quiz
Q: A feature runs from 0 to 50 in the training split. Which angle does the value 25 get?
- 25
* π/2
- π
E: θ = π(25 − 0)/(50 − 0) = π/2: halfway along the range maps to halfway to π.
```

```quiz
Q: A column has missing values. Which mean fills them in the test set?
* The mean of the training split
- The mean of the test split
- The mean of all the data
E: Like every learned step, the fill value comes from the training data only and is applied unchanged to the test data.
```

## Summary

- Real data needs fixing first: features to qubits, samples, classes, text, gaps and scales.
- PCA keeps the directions of greatest variation.
- Fit every step — scaling, PCA, filling — on the training data only, to avoid leakage.
