---
title: Quantum phase estimation
area: circuits
kind: lecture
order: 21
objectives: State what phase estimation computes | Follow the circuit from controlled powers to the inverse QFT | Predict the result when the phase is not an exact binary fraction
math: 05-eigenvalues, 11-fourier-transform
---
# Quantum phase estimation

## The idea

Many questions in physics and computing — energies of molecules, periods of functions, factors of numbers — come down to the phase a unitary gives its eigenstate. Phase estimation reads that phase out as a binary number. It combines three earlier ideas: phase kickback writes the phase onto counting qubits, and the inverse QFT turns the phase pattern into a readable number.

## The problem

A unitary $U$ with an eigenstate $|u\rangle$ satisfies

$$U|u\rangle = e^{2\pi i\varphi}|u\rangle$$

for some phase $\varphi$ between 0 and 1. **Phase estimation** finds $\varphi$ to $t$ binary digits. It is the engine inside Shor's factoring algorithm and inside quantum algorithms for chemistry, which estimate energies as phases.

## The circuit

1. Put $t$ **counting** qubits in superposition with H, and the target in $|u\rangle$.
2. Counting qubit $j$ controls $U^{2^{t-1-j}}$. By **phase kickback**, each counting qubit picks up the phase $e^{2\pi i\,\varphi\,2^{t-1-j}}$ on its $|1\rangle$ part — the target never changes.
3. The counting register now holds the quantum Fourier transform of the number $2^t\varphi$ — exactly so when that number is whole — so the **inverse QFT** turns it back into that number, or into its closest neighbours.
4. Measure the counting qubits: the result $m$ gives $\varphi \approx m/2^t$.

In QuantumScope, $U = P(2\pi\varphi)$ and $|u\rangle = |1\rangle$, so the controlled powers are controlled-phase gates.

[Try it: estimate φ = 5/16 with 4 counting qubits](qs:algorithm/qpe?t=4&phase=5/16)

## Exact and inexact phases

If $2^t\varphi$ is a whole number, the result is certain. Otherwise the probability spreads over neighbouring values, but the closest $t$-bit estimate still wins with probability at least

$$\frac{4}{\pi^2} \approx 0.405$$

and more counting qubits sharpen the estimate: each one adds a binary digit.

[Try it: estimate φ = 1/3 with 4 counting qubits](qs:algorithm/qpe?t=4&phase=1/3)

## Worked example

With $t = 4$ counting qubits and $\varphi = 5/16$, $2^t\varphi = 5$ is whole: the counting register ends in $|0101\rangle$ with certainty, and $5/16 = 0.3125$ exactly.

With $\varphi = 1/3$, $2^t\varphi = 5.33$ is not whole. The exact probabilities are about 0.685 for $m = 5$ (estimate 0.3125), 0.172 for $m = 6$ (0.375) and 0.044 for $m = 4$ (0.25). The closest estimate wins, well above the guaranteed 0.405, and the nearest neighbour takes most of the rest. More counting qubits would bring the estimate closer to 0.333.

## Common mistakes

- **Expecting an exact answer for every phase.** Only phases with $t$ binary digits are found with certainty.
- **Forgetting the target must be an eigenstate.** For other states the result mixes the phases of several eigenstates.
- **Using the forward QFT at the end.** The readout needs the inverse QFT.

## In the app

**Algorithms → Phase estimation** takes the number of counting qubits and the phase. Run shots to see the histogram: one bar for 5/16, a spread around 5 for 1/3. Increase the counting qubits and watch the peak sharpen.

## Check your understanding

```quiz
Q: With t = 3 counting qubits and φ = 3/8, what is measured?
- 011 with probability 4/π²
* 011 with certainty
- A uniform spread
E: 2³ · 3/8 = 3 exactly, so the counting register ends in |011⟩.
```

```quiz
Q: Why does the target qubit stay unchanged?
* It is an eigenstate of U; the phase kicks back onto the counting qubits
- The controlled gates never act on it
- It is measured first
E: Controlled-U on an eigenstate only multiplies the control's |1⟩ part by the eigenphase.
```

```quiz
Q: With t = 3 counting qubits, which phase is found with certainty?
* 3/8
- 1/3
- 1/10
E: 2³ × 3/8 = 3 is a whole number; the other two are not 3-bit binary fractions.
```

```quiz
Q: The counting register reads m = 0110 with t = 4. What is the estimate of φ?
- 6
* 6/16 = 0.375
- 0.6
E: φ ≈ m/2^t = 6/16.
```

## Summary

- Phase estimation finds φ in U|u⟩ = e^{2πiφ}|u⟩ to t bits.
- Controlled powers of U kick the phase back onto counting qubits; the inverse QFT reads it out.
- Exact binary fractions are found with certainty; otherwise the closest estimate wins with probability at least 4/π².
