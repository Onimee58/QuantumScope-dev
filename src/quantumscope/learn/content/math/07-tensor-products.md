---
title: Tensor products
area: math
kind: lecture
order: 7
objectives: Compute tensor products of states and of gates | Explain why n qubits need 2ⁿ amplitudes | Tell a product state from an entangled one
---
# Tensor products

## The idea

Two qubits are not described by two separate vectors but by one longer vector: their **tensor product**. This one construction explains both the power of many qubits — the vector doubles with every qubit — and entanglement, which is simply a joint state that cannot be split back into two.

## Combining two states

The tensor product $\otimes$ multiplies every amplitude of the first state by every amplitude of the second:

$$\begin{pmatrix} a \\ b \end{pmatrix} \otimes \begin{pmatrix} c \\ d \end{pmatrix} = \begin{pmatrix} ac \\ ad \\ bc \\ bd \end{pmatrix}$$

The four entries are the amplitudes of $|00\rangle, |01\rangle, |10\rangle, |11\rangle$. Usually the $\otimes$ is left out: $|0\rangle \otimes |1\rangle = |01\rangle$.

Example: $|+\rangle \otimes |0\rangle = \frac{1}{\sqrt{2}}(1, 0, 1, 0)$, that is $\frac{1}{\sqrt{2}}(|00\rangle + |10\rangle)$.

## Growing fast: 2ⁿ amplitudes

Every extra qubit doubles the length of the vector: $n$ qubits need $2^n$ amplitudes. Ten qubits need 1,024; fifty would need about $10^{15}$. This exponential growth is why quantum states are hard to simulate, and why QuantumScope stops at ten qubits.

## Gates on several qubits

A gate on one qubit of a pair is a tensor product with the identity: $X$ on the first qubit is $X \otimes I$, a 4 × 4 matrix. Some gates are not tensor products at all, for example **CNOT**, which flips the second qubit when the first is 1:

$$\mathrm{CNOT} = \begin{pmatrix} 1 & 0 & 0 & 0 \\ 0 & 1 & 0 & 0 \\ 0 & 0 & 0 & 1 \\ 0 & 0 & 1 & 0 \end{pmatrix}$$

## Product states and entangled states

A two-qubit state is a **product state** if it can be written as $|\psi\rangle \otimes |\varphi\rangle$. Otherwise it is **entangled**.

There is a quick test: write the amplitudes of $|00\rangle, |01\rangle, |10\rangle, |11\rangle$ as $(w, x, y, z)$. The state is a product exactly when

$$w\,z - x\,y = 0$$

because a product has $w\,z = ac \cdot bd = ad \cdot bc = x\,y$.

The Bell state $\frac{1}{\sqrt{2}}(|00\rangle + |11\rangle)$ has $w = z = \frac{1}{\sqrt{2}}$ and $x = y = 0$, so $wz - xy = \frac{1}{2} \neq 0$: no choice of single-qubit states can produce it. Its correlations live only in the joint state.

## Worked example

Two states that look alike:

- $\frac{1}{2}(|00\rangle + |01\rangle + |10\rangle + |11\rangle)$: $wz - xy = \frac{1}{4} - \frac{1}{4} = 0$, a product, $|+\rangle|+\rangle$.
- $\frac{1}{2}(|00\rangle + |01\rangle + |10\rangle - |11\rangle)$: $wz - xy = -\frac{1}{4} - \frac{1}{4} = -\frac{1}{2} \neq 0$, **entangled**.

One minus sign makes the difference. The second state is what a CZ gate makes from $|+\rangle|+\rangle$: CZ flips the sign of $|11\rangle$ only, so it can entangle even though it changes no probability. Measured in the $z$ basis, both states give all four results equally often; the entanglement shows only in other bases.

## Common mistakes

- **Adding instead of multiplying.** $|0\rangle \otimes |1\rangle$ is not $|0\rangle + |1\rangle$; it is the single basis state $|01\rangle$.
- **Counting 2n amplitudes for n qubits.** It is $2^n$: six qubits need 64, not 12.
- **Judging entanglement from z-basis probabilities.** Equal probabilities can hide entanglement, as the worked example shows; use the amplitudes.

## In the app

Build H on both qubits, then CZ, and open the State Inspector: the amplitude table shows the minus sign on $|11\rangle$, and the **Reduced state** tab reports each qubit as maximally mixed — a sign of entanglement. In the calculator, `⊗` builds products: try `|+⟩ ⊗ |0⟩` or the Bell-state link below.

[Try it: H then CNOT makes a Bell pair](qs:circuit?n=2&gates=H:0;CX:0,1)

[Try it: CZ entangles |+⟩|+⟩](qs:circuit?n=2&gates=H:0;H:1;CZ:0,1&inspector=1)

[Try it in the calculator: CNOT (H ⊗ I)|00⟩](qs:calc?expr=CNOT%20%28H%20%E2%8A%97%20I%29%7C00%E2%9F%A9)

## Check your understanding

```quiz
Q: How many amplitudes does a 6-qubit state have?
- 12
- 36
* 64
E: Each qubit doubles the number: 2⁶ = 64.
```

```quiz
Q: Is ½(|00⟩ + |01⟩ + |10⟩ + |11⟩) entangled?
- Yes
* No, it is |+⟩ ⊗ |+⟩
E: wz − xy = ¼ − ¼ = 0, so it is a product state: |+⟩|+⟩.
```

```quiz
Q: What is |1⟩ ⊗ |+⟩ as a list of four amplitudes (|00⟩, |01⟩, |10⟩, |11⟩)?
- (1, 1, 0, 0)/√2
* (0, 0, 1, 1)/√2
- (0, 1, 0, 1)/√2
E: The first qubit is 1, so only |10⟩ and |11⟩ appear, each with amplitude 1/√2.
```

```quiz
Q: Is (|01⟩ + |10⟩)/√2 entangled?
* Yes
- No
E: w = z = 0 and x = y = 1/√2, so wz − xy = −½ ≠ 0. It is a Bell state.
```

## Summary

- $\otimes$ multiplies every amplitude by every amplitude; $n$ qubits need $2^n$ amplitudes.
- Gates on one qubit of many are tensor products with $I$; CNOT is not a product.
- Product states factor; for two qubits, entangled exactly when $wz - xy \neq 0$.
- A single sign, as CZ adds, can turn a product into an entangled state.
