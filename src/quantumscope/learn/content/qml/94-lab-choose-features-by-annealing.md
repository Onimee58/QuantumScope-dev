---
title: "Lab: choose features by annealing"
area: qml
kind: lab
order: 94
objectives: Turn a real dataset into a feature-selection Ising problem | See how anneal time and reads decide the choice | Compare annealed, greedy and PCA features on test data | Train a quantum classifier on the chosen features
---
# Lab: choose features by annealing

The breast cancer data has 30 measurements of cell nuclei; you will keep 3, one per qubit. Read the lecture *Choosing features by annealing* first.

[Open Quantum annealing](qs:open/annealing)

```step
title: Choose 3 of the 10 "mean" features
text: In Quantum annealing, choose the problem Feature selection (from data) and the data Breast Cancer Wisconsin. Under Candidates, untick everything except the ten features whose names start with "mean", so that radius, perimeter and area are all candidates. Keep 3 features, α = 0.7, Reads 100, T = 20, and press Anneal. Open Chosen features: the best read keeps mean texture, mean perimeter and mean concave points, the best of all 120 choices. Find radius, perimeter and area on the redundancy map: the yellow block.
check: did features dataset=breast_cancer k=3 candidates=10 rank=1 chosen~texture
```

```step
title: Anneal too fast
text: Set T = 0.5 and anneal again. The spins barely follow the problem: under half of the 100 reads keep exactly 3 features, and the best read is no longer the best choice (its place by energy is shown). Return to T = 20.
check: did features dataset=breast_cancer T<=1 valid<50
```

```step
title: Ignore redundancy
text: Set α = 1 and anneal at T = 20. Only relevance counts now: the anneal keeps mean radius, mean perimeter and mean concave points, the greedy choice, two of which are near-copies. Compare the mean redundancy in the table with the α = 0.7 choice (about 0.9 against 0.5). Then set α back to 0.7 and anneal again.
check: did features dataset=breast_cancer alpha=1 rank=1 chosen~radius
```

```step
title: Train a quantum classifier on the chosen features
text: With the α = 0.7 choice, press Use these features in the Datasets tab: the data is prepared with those 3 features instead of PCA. Open the Quantum Kernel Classifier, choose From the Datasets tab, the Angle encoding feature map, and press Train. The test accuracy reaches at least 90%. Try the ZZ feature map too: on these 3 features it does much worse, a reminder that the features and the model must be chosen together.
check: did featuresused k=3 chosen~texture
check: qml kernel map angle
check: qml kernel test >= 0.9
```

```quiz
Q: At T = 0.5, why do so few reads keep exactly 3 features?
- The penalty is switched off for fast anneals
* The state barely changes from the driver's ground state, a uniform superposition, so the reads are close to random bitstrings
- Fast anneals favour keeping all features
E: Of the 1,024 bitstrings, only 120 keep exactly 3, about 12%; a nearly uniform state gives about that.
```

```quiz
Q: The table scores the annealed choice, greedy selection, PCA and all candidates on the test samples. Why is that fair to the annealed choice?
* The choice was made from the training samples only, so the test samples are new to every method
- The test samples were used to choose α
- The annealer sees the test samples but not their labels
E: Relevance and redundancy come from the training split; the test split is only used for this comparison.
```

```quiz
Q: A colleague says this lab proves that quantum annealing chooses better features than classical methods. What do you answer?
- Yes: the annealed choice had the lowest energy
* No: all 120 choices could be checked classically in a moment, and the energy only stands in for accuracy
- No: annealing cannot find the lowest energy
E: The lab shows how the problem is formulated and solved; a speed-up would need far more candidates, and it is not established even then.
```
