---
title: Noise and decoherence
area: circuits
kind: lecture
order: 11
objectives: Describe noise as a quantum channel | Relate amplitude and phase damping to T₁ and T₂ | Predict how noise lowers fidelity and algorithm success
math: 06-probability, 08-density-matrices-and-projectors
---
# Noise and decoherence

## The idea

Real qubits are never perfectly isolated, so their quantum information leaks away: superpositions fade, excited states relax, and gates and readouts make mistakes. This lecture describes noise precisely — as channels that shrink the Bloch vector — and measures the damage with fidelity, so you can see why long circuits suffer most.

## Why real qubits are noisy

A qubit is never perfectly isolated. Its environment slowly learns about its state, and every interaction leaves it a little more mixed. This loss of quantum information is **decoherence**; together with imperfect gates and measurements, it is why today's quantum computers are called *noisy*.

## Channels

Noise is described by a **channel**, a map on density matrices written with Kraus operators:

$$\rho \rightarrow \sum_k K_k\,\rho\,K_k^\dagger, \qquad \sum_k K_k^\dagger K_k = I$$

The condition on the right keeps probabilities summing to one.

| Channel | What it does | Bloch sphere |
|---|---|---|
| Bit flip (p) | X with probability p | y and z shrink by 1 − 2p |
| Phase flip (p) | Z with probability p | x and y shrink by 1 − 2p |
| Depolarizing (p) | replaces the state by I/2 with probability p | everything shrinks by 1 − p |
| Amplitude damping (γ) | \|1⟩ decays to \|0⟩ | pulled towards \|0⟩ |
| Phase damping (λ) | phase is lost, populations kept | x and y shrink by √(1 − λ) |

Double-click any noise channel in the palette for its Noise Explorer: equations, Kraus operators and live numbers.

## T₁ and T₂

Hardware is described by two times. **T₁** is the energy-relaxation time: amplitude damping over a time $t$ has $\gamma = 1 - e^{-t/T_1}$. **T₂** is the coherence time, the lifetime of superpositions, set by relaxation and pure dephasing together. Every gate takes time, so deeper circuits suffer more — QuantumScope's *idle noise* option makes waiting qubits decay too.

## Fidelity

How close is the noisy result to what we wanted? For a pure target $|\psi\rangle$, the **fidelity** is

$$F = \langle\psi|\,\rho\,|\psi\rangle$$

For a Bell pair with depolarizing noise of strength $p$ on one qubit, $F = 1 - \frac{3p}{4}$: 0.85 at $p = 0.2$.

[Try it: a Bell pair with 20% depolarizing](qs:circuit?n=2&gates=H:0;CX:0,1&elements=depolarizing:1:2:0.2&inspector=1)

## Noise and algorithms

Errors accumulate with every gate, so long circuits suffer most. With QuantumScope's *Moderate* preset, the 3-qubit Grover search drops from a success probability of 0.945 to about 0.577, while the much shorter Bernstein–Vazirani circuit still finds its answer with probability 0.919.

[Try it: Grover with moderate noise](qs:algorithm/grover?n=3&marked=101&iterations=-1&noise=Moderate)

Readout error adds a final layer: each measured bit may be reported wrongly, even when the state was right.

## Fighting back

Noise cannot be avoided, but it can be managed: shorter circuits, better hardware, error **mitigation**, and ultimately quantum **error correction**, which spreads one logical qubit over many physical ones — the subject of the lectures from *The bit-flip code* on.

## Worked example

Send $|+\rangle$ (Bloch vector $(1, 0, 0)$) through three channels and compute the fidelity $F = \frac{1}{2}(1 + \vec r \cdot \hat x)$ with the intended $|+\rangle$:

- **Bit flip, $p = 0.1$:** X does nothing to $|+\rangle$, so $F = 1$.
- **Phase flip, $p = 0.1$:** $x$ shrinks by $1 - 2p = 0.8$, so $F = 0.9$.
- **Depolarizing, $p = 0.2$:** everything shrinks by $0.8$, so $F = 0.9$ too.

The same noise can be harmless or harmful depending on the state. Over time: with $T_1 = 100$ µs, a qubit idling for 10 µs has $\gamma = 1 - e^{-0.1} \approx 0.095$.

## Common mistakes

- **Treating every channel as the same.** Bit flip leaves $|+\rangle$ alone but ruins $|0\rangle$; phase flip does the opposite.
- **Thinking noise only acts during gates.** Waiting qubits decay too, which the idle-noise option shows.
- **Confusing T₁ and T₂.** T₁ is energy relaxation; T₂, the coherence time, is never longer than 2T₁.

## In the app

Drag noise channels from the noise palette onto a wire, or choose a preset noise model; the State Inspector then shows the density matrix, purity and fidelity. Double-click a channel in the palette to open its **Noise Explorer** with equations, Kraus operators and live numbers. Compare Grover with and without the *Moderate* preset to see a long circuit suffer.

## Check your understanding

```quiz
Q: Which channel leaves |0⟩ and |1⟩ unchanged but destroys superpositions?
- Bit flip
* Phase damping
- Amplitude damping
E: Phase damping keeps populations and shrinks coherences. Amplitude damping changes |1⟩, and bit flip swaps |0⟩ and |1⟩.
```

```quiz
Q: Depolarizing noise with p = 0.4 acts on one qubit of a Bell pair. What is the fidelity?
- 0.6
* 0.7
- 0.9
E: F = 1 − 3p/4 = 1 − 0.3 = 0.7.
```

```quiz
Q: Which channel leaves the state |+⟩ unchanged?
* Bit flip
- Phase flip
- Depolarizing
E: |+⟩ is an eigenstate of X, so applying X with some probability changes nothing.
```

```quiz
Q: A qubit with T₁ = 50 µs waits for 50 µs. What is the amplitude-damping strength γ?
- 1
* About 0.63
- About 0.37
E: γ = 1 − e^{−t/T₁} = 1 − e^{−1} ≈ 0.63.
```

## Summary

- Noise is a channel ρ → Σ K ρ K†; the common channels shrink or shift the Bloch vector.
- T₁ (energy relaxation) and T₂ (coherence) set how long quantum information survives.
- Fidelity ⟨ψ|ρ|ψ⟩ measures the damage; deep circuits such as Grover suffer most.
