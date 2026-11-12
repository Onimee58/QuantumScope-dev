---
title: "Lab: from three species to ten digits"
area: qml
kind: lab
order: 93
objectives: Train a one-vs-rest quantum kernel classifier | Read a many-class confusion matrix | Compare an easy and a hard ten-class dataset | Separate several classes with one variational circuit
---
# Lab: from three species to ten digits

You will classify three iris species, then all ten handwritten digits, then ten kinds of clothing, and finally separate three classes with a single variational circuit. Read the lecture *More than two classes* first.

[Open the Quantum Kernel Classifier](qs:open/qml_kernel)

```step
title: Three iris species
text: Choose the dataset Iris, 4 qubits, and under Classes choose All 3 classes. Set the feature map to Angle encoding and the bandwidth to 1, then press Train. The decision regions now have three colours, and the test accuracy should reach at least 90%. Open the Evaluation tab: the confusion matrix is 3 × 3.
check: qml dataset iris
check: qml kernel classes >= 3
check: qml kernel test >= 0.9
```

```step
title: All ten digits
text: Choose MNIST, 8 qubits and All 10 classes, and train again (angle encoding, bandwidth 1). Chance is 10%; the classifier should reach at least 70%. In the Evaluation tab, find the pairs of digits most often confused, and the hardest class.
check: qml dataset mnist
check: qml kernel classes >= 10
check: qml kernel test >= 0.7
```

```step
title: Ten kinds of clothing
text: Choose Fashion-MNIST with the same settings and train. It is harder: the test accuracy is lower, at least 50%. Which classes does the confusion matrix mix up? Try fewer qubits (4) and see how much accuracy drops.
check: qml dataset fashion_mnist
check: qml kernel classes >= 10
check: qml kernel test >= 0.5
```

```step
title: One circuit for three species
text: Open the Variational Classifier (+ in Quantum ML). Choose Iris, 4 qubits and All 3 classes, set Trainable layers to 3 and press Train. The loss becomes cross-entropy, and the classes are read from 2 qubits. The test accuracy should reach at least 85%. Press Open in circuit simulator and run shots: the outcome on q0 q1 names the class (00, 01 or 10).
check: qml variational classes >= 3
check: qml variational test >= 0.85
```

```quiz
Q: MNIST reaches a higher accuracy with 8 qubits than with 4. Why?
* With one feature per qubit, 8 PCA components keep more of each image's variation than 4
- More qubits make the kernel exact
- Eight qubits allow eight classes
E: The data is reduced to as many features as qubits. More components keep more of what distinguishes the digits.
```
