---
title: Vectors and Dirac notation
area: math
kind: lecture
order: 2
objectives: Write qubit states as column vectors and kets | Normalize a state | Compute inner products and recognize orthogonal states
---
# Vectors and Dirac notation

## The idea

A qubit's state is a **vector** of two complex amplitudes. Physicists write such vectors in **Dirac notation**: compact, and the same for one qubit or ten. Two operations do most of the work: **normalizing** a state so its probabilities add to one, and the **inner product**, which measures how much two states overlap.

## States as column vectors

The two basis states of a qubit are

$$|0\rangle = \begin{pmatrix} 1 \\ 0 \end{pmatrix}, \qquad |1\rangle = \begin{pmatrix} 0 \\ 1 \end{pmatrix}$$

Every state is a combination of them:

$$|\psi\rangle = \alpha|0\rangle + \beta|1\rangle = \begin{pmatrix} \alpha \\ \beta \end{pmatrix}$$

The symbol $|\psi\rangle$ is called a **ket**. It is just a name for a column vector.

## Normalization

The amplitudes give probabilities $|\alpha|^2$ and $|\beta|^2$, which must add up to 1:

$$|\alpha|^2 + |\beta|^2 = 1$$

A vector with this property is **normalized**. To normalize any nonzero vector, divide it by its length. For example $|0\rangle + |1\rangle$ has length $\sqrt{2}$, so the normalized state is

$$|+\rangle = \frac{1}{\sqrt{2}}\left(|0\rangle + |1\rangle\right)$$

## Bras and inner products

The **bra** $\langle\psi|$ is the conjugate transpose of the ket: a row vector with conjugated entries.

$$\langle\psi| = \begin{pmatrix} \bar{\alpha} & \bar{\beta} \end{pmatrix}$$

Putting a bra and a ket together gives the **inner product**, a single complex number:

$$\langle\varphi|\psi\rangle = \bar{\gamma}\,\alpha + \bar{\delta}\,\beta \qquad \text{for } |\varphi\rangle = \gamma|0\rangle + \delta|1\rangle$$

It measures how much two states overlap:

- $\langle\psi|\psi\rangle = |\alpha|^2 + |\beta|^2 = 1$ for a normalized state.
- $\langle 0|1\rangle = 0$: the two states are **orthogonal**, completely distinguishable.
- $|\langle\varphi|\psi\rangle|^2$ is the probability of finding $|\varphi\rangle$ when the system is in $|\psi\rangle$. This is the **fidelity** between two pure states.

## Bases

Two orthogonal, normalized states form a **basis**: every state can be written as a combination of them. Besides $|0\rangle, |1\rangle$, the most useful basis is

$$|\pm\rangle = \frac{1}{\sqrt{2}}\left(|0\rangle \pm |1\rangle\right)$$

Measuring "along $x$" means measuring in this basis.

## Worked example

Normalize $(1 + i)|0\rangle + |1\rangle$. Its length squared is $|1 + i|^2 + 1 = 2 + 1 = 3$, so

$$|\psi\rangle = \frac{1 + i}{\sqrt{3}}|0\rangle + \frac{1}{\sqrt{3}}|1\rangle, \qquad P(0) = \frac{2}{3},\ P(1) = \frac{1}{3}$$

How likely is it to be found in $|+\rangle$? The bra $\langle +|$ has entries $\frac{1}{\sqrt{2}}, \frac{1}{\sqrt{2}}$, so

$$\langle +|\psi\rangle = \frac{1}{\sqrt{2}}\cdot\frac{(1 + i) + 1}{\sqrt{3}} = \frac{2 + i}{\sqrt{6}}, \qquad |\langle +|\psi\rangle|^2 = \frac{5}{6}$$

## Common mistakes

- **Forgetting to conjugate the bra.** For complex states, $\langle\varphi|\psi\rangle$ uses $\bar{\gamma}$ and $\bar{\delta}$; without the bar, even $\langle\psi|\psi\rangle$ can come out wrong.
- **Normalizing by the sum of amplitudes.** Divide by the length $\sqrt{|\alpha|^2 + |\beta|^2}$, not by $\alpha + \beta$.
- **Reading ⟨φ|ψ⟩ as a probability.** It is an amplitude, possibly complex; the probability is its modulus squared.

## In the app

The State Inspector's **Amplitudes** tab lists each basis state with its amplitude and probability: check that the probabilities add to 1. In the calculator, kets and bras are typed directly, for example `⟨+|-⟩` or `normalize((1+i)|0⟩ + |1⟩)`.

[Try it: inspect amplitudes and probabilities in the State Inspector (a |+⟩ qubit)](qs:circuit?n=1&gates=H:0)

[Try it in the calculator: ⟨+|-⟩](qs:calc?expr=%E2%9F%A8%2B%7C-%E2%9F%A9)

## Check your understanding

```quiz
Q: Which vector is normalized?
- (1, 1)
* (0.6, 0.8i)
- (0.5, 0.5)
E: |0.6|² + |0.8i|² = 0.36 + 0.64 = 1. The others give 2 and 0.5.
```

```quiz
Q: What is ⟨+|−⟩?
* 0
- 1
- 1/2
E: ⟨+|−⟩ = ½(1·1 + 1·(−1)) = 0: |+⟩ and |−⟩ are orthogonal, so they form a basis.
```

```quiz
Q: What is ⟨1|ψ⟩ for |ψ⟩ = α|0⟩ + β|1⟩?
- α
* β
- β̄
- 1
E: ⟨1| picks out the |1⟩ component: ⟨1|ψ⟩ = α⟨1|0⟩ + β⟨1|1⟩ = β.
```

```quiz
Q: A qubit is in |0⟩. What is the probability of finding it in |−⟩?
- 0
* 1/2
- 1
E: ⟨−|0⟩ = 1/√2, and |1/√2|² = 1/2.
```

## Summary

- A ket $|\psi\rangle$ is a column vector of amplitudes; its bra $\langle\psi|$ is the conjugate row vector.
- States are normalized: the squared amplitudes add up to 1; divide by the length to normalize.
- $\langle\varphi|\psi\rangle$ measures overlap; $|\langle\varphi|\psi\rangle|^2$ is a probability, and 0 means orthogonal.
