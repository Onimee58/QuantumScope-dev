---
title: "Study guide: Quantum ML"
area: qml
kind: guide
order: 0
objectives: See what this area covers and in which order | Check that you have the background you need | Know what you should be able to do at the end
---
# Study guide: Quantum ML

## What this area is about

Quantum machine learning asks whether quantum circuits can help computers learn from data. In this area you encode data into quantum states, train two kinds of quantum classifiers, and evaluate them as a data scientist would — honestly, against chance and against classical methods. You work with real datasets, including handwritten digits, and with your own CSV files.

**Who it is for:** students and professionals with some data or machine-learning background who want to know what quantum methods can and cannot do. No prior quantum computing is assumed beyond the first lectures listed below.

**Time:** about 10–12 hours: 8 lectures of about 45 minutes and 5 labs of about an hour.

## Before you start

From the other areas:

- [Superposition and the Bloch sphere](qs:lesson/principles/01-superposition-and-bloch-sphere) and [Measurement and the Born rule](qs:lesson/principles/02-measurement-and-born-rule)
- [Tensor products](qs:lesson/math/07-tensor-products), [Probability](qs:lesson/math/06-probability) and [Gradients and optimization](qs:lesson/math/12-gradients-and-optimization)

Basic machine-learning ideas help (training and test data, accuracy), but every one used here is explained.

## Suggested path

| Week | Lecture or lab | You will be able to |
|---|---|---|
| 1 | [From data to quantum states](qs:lesson/qml/01-data-to-quantum-states) | encode data and compute a quantum kernel |
| 1 | [Kernel classifiers and the SVM](qs:lesson/qml/02-kernel-classifiers) | train kernel ridge and an SVM, and read decision regions |
| 1 | [Lab: classify the circles](qs:lesson/qml/90-lab-classify-the-circles) | train your first quantum kernel classifier |
| 2 | [Variational classifiers](qs:lesson/qml/03-variational-classifiers) | train a circuit with exact gradients |
| 2 | [Lab: train a quantum circuit](qs:lesson/qml/92-lab-train-a-circuit) | compare a variational model with a kernel |
| 3 | [Generalization, bandwidth and kernel concentration](qs:lesson/qml/04-generalization-and-its-limits) | spot overfitting and choose a bandwidth |
| 3 | [Preparing real data](qs:lesson/qml/05-preparing-real-data) | fix real data with PCA and scaling, without leakage |
| 3 | [Lab: MNIST, from pixels to qubits](qs:lesson/qml/91-lab-mnist-pixels-to-qubits) | prepare and classify images |
| 4 | [Evaluating a classifier](qs:lesson/qml/06-evaluating-classifiers) | read confusion matrices, ROC curves and cross-validation |
| 4 | [More than two classes](qs:lesson/qml/07-more-than-two-classes) | build and judge k-class classifiers |
| 4 | [Lab: from three species to ten digits](qs:lesson/qml/93-lab-ten-digits) | classify ten digits and ten kinds of clothing |
| 5 | [Choosing features by annealing](qs:lesson/qml/08-feature-selection-by-annealing) | write feature selection as an Ising problem and judge the choice |
| 5 | [Lab: choose features by annealing](qs:lesson/qml/94-lab-choose-features-by-annealing) | keep 3 of 30 breast-cancer measurements and classify with them |

## How to study

1. In each lecture, read **The idea** and redo the **Worked example** before opening the app.
2. Run the **In the app** experiment and change one setting at a time; write down what changed.
3. Answer the four questions; reread any section behind a wrong answer.
4. Do the labs in the order above: each lab step checks your result as you go.
5. Keep a test set untouched until the end of every experiment — the habit matters more than any single score.

## Check yourself at the end

You have finished this area when you can:

- compute an angle-encoding kernel by hand and explain what the ZZ map adds;
- explain why only the support vectors matter to an SVM;
- count the circuit runs a variational classifier needs per training step;
- recognize overfitting and kernel concentration, and say what to change;
- prepare a real dataset without leaking test information;
- judge a ten-class score against chance, using the confusion matrix and balanced accuracy;
- choose features by annealing, and say honestly what the annealer adds.

## Where to go next

- The variational lectures in [Quantum Circuits](qs:lesson/circuits/00-study-guide): VQE and QAOA use the same training ideas for physics and optimization.
