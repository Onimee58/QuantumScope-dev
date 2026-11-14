---
title: "Study guide: Quantum Circuits"
area: circuits
kind: guide
order: 0
objectives: See what this area covers and in which order | Check that you have the background you need | Know what you should be able to do at the end
---
# Study guide: Quantum Circuits

## What this area is about

Quantum Circuits is the core of quantum computing: how qubits are prepared, transformed by gates, measured and protected, and how algorithms combine these steps to solve problems. It runs from a single qubit to error-correcting codes, phase estimation, variational algorithms and quantum annealing. Every lecture links to circuits you can open, change and simulate, and the labs check your circuits step by step.

**Who it is for:** university students in a quantum computing course, and professionals who want a working understanding of quantum algorithms. Modules 1 and 2 make a short introduction on their own.

**Time:** about 35–40 hours in total — a semester-long module. Each lecture takes about 45 minutes and each lab about an hour.

## Before you start

- From Quantum Principles: [Superposition and the Bloch sphere](qs:lesson/principles/01-superposition-and-bloch-sphere) and [Measurement and the Born rule](qs:lesson/principles/02-measurement-and-born-rule).
- From Mathematics: [Complex numbers](qs:lesson/math/01-complex-numbers), [Vectors and Dirac notation](qs:lesson/math/02-vectors-and-dirac-notation) and [Matrices acting on states](qs:lesson/math/03-matrices-acting-on-states). Later modules list more under **Math you need**.

## Suggested path

Work through the modules in order; within a module, read the lectures first, then do the labs.

### 1. Foundations

*States, gates, entanglement and measurement.*

- Lectures: [Qubits, state vectors and bit order](qs:lesson/circuits/01-qubits) · [Single-qubit gates](qs:lesson/circuits/02-single-qubit-gates) · [Multi-qubit gates and tensor products](qs:lesson/circuits/03-multi-qubit-gates) · [Entanglement in circuits](qs:lesson/circuits/04-entanglement-in-circuits) · [Measurement in circuits](qs:lesson/circuits/05-measurement)
- Labs: [Lab: make a Bell pair](qs:lesson/circuits/90-lab-bell-pair) · [Lab: build a GHZ state](qs:lesson/circuits/91-lab-ghz)

### 2. First algorithms

*Reversible logic, oracles, Grover search, the QFT and circuit cost.*

- Lectures: [Reversible logic](qs:lesson/circuits/06-reversible-logic) · [Phase kickback and oracles](qs:lesson/circuits/07-phase-kickback-and-oracles) · [Grover search](qs:lesson/circuits/08-grover-search) · [The quantum Fourier transform](qs:lesson/circuits/09-qft) · [Circuit cost: depth, T-count and Clifford gates](qs:lesson/circuits/10-circuit-cost)
- Labs: [Lab: see phase kickback](qs:lesson/circuits/92-lab-phase-kickback) · [Lab: Grover search by hand](qs:lesson/circuits/93-lab-grover-by-hand) · [Lab: build a half adder](qs:lesson/circuits/94-lab-half-adder) · [Lab: QFT of a basis state](qs:lesson/circuits/95-lab-qft)

### 3. Noise and dynamic circuits

*Decoherence, mid-circuit measurement, feed-forward, teleportation.*

- Lectures: [Noise and decoherence](qs:lesson/circuits/11-noise-and-decoherence) · [Mid-circuit measurement and classical bits](qs:lesson/circuits/12-mid-circuit-measurement) · [Classical control, feed-forward and reset](qs:lesson/circuits/13-feed-forward-and-reset) · [Quantum teleportation](qs:lesson/circuits/14-teleportation) · [Superdense coding](qs:lesson/circuits/15-superdense-coding) · [The deferred-measurement principle](qs:lesson/circuits/16-deferred-measurement)
- Labs: [Lab: watch a Bell pair decohere](qs:lesson/circuits/96-lab-bell-decoherence) · [Lab: measure in the middle](qs:lesson/circuits/97-lab-measure-in-the-middle) · [Lab: reset by feed-forward](qs:lesson/circuits/98-lab-reset-by-feed-forward) · [Lab: teleport a qubit](qs:lesson/circuits/99-lab-teleport-a-qubit) · [Lab: send two bits with one qubit](qs:lesson/circuits/100-lab-superdense-coding) · [Lab: defer the measurement](qs:lesson/circuits/101-lab-defer-the-measurement)

### 4. Error correction

*Repetition codes, logical error rates and the Shor code.*

- Lectures: [Error correction: the bit-flip code](qs:lesson/circuits/17-bit-flip-code) · [Error correction: the phase-flip code](qs:lesson/circuits/18-phase-flip-code) · [Logical error rates and thresholds](qs:lesson/circuits/19-logical-error-rates) · [The Shor code and stabilizers](qs:lesson/circuits/20-shor-code)
- Labs: [Lab: build the bit-flip code](qs:lesson/circuits/102-lab-bit-flip-code) · [Lab: beat the noise](qs:lesson/circuits/103-lab-beat-the-noise)

### 5. Phase estimation and variational algorithms

*QPE, parameters, gradients, VQE, QAOA and VQLS.*

- Lectures: [Quantum phase estimation](qs:lesson/circuits/21-phase-estimation) · [Parameterized circuits](qs:lesson/circuits/22-parameterized-circuits) · [The parameter-shift rule](qs:lesson/circuits/23-parameter-shift-rule) · [The variational quantum eigensolver](qs:lesson/circuits/24-vqe) · [Optimizers, landscapes and plateaus](qs:lesson/circuits/25-optimizers-and-landscapes) · [QAOA and MaxCut](qs:lesson/circuits/26-qaoa-maxcut) · [The variational quantum linear solver](qs:lesson/circuits/27-vqls) · [Optimizing with shots](qs:lesson/circuits/28-optimizing-with-shots)
- Labs: [Lab: phase estimation precision](qs:lesson/circuits/104-lab-phase-estimation) · [Lab: tune a circuit by hand](qs:lesson/circuits/105-lab-tune-by-hand) · [Lab: find H₂'s ground energy](qs:lesson/circuits/106-lab-h2-ground-energy) · [Lab: not enough layers](qs:lesson/circuits/107-lab-not-enough-layers) · [Lab: cut a graph with QAOA](qs:lesson/circuits/108-lab-qaoa-maxcut) · [Lab: solve a linear system](qs:lesson/circuits/109-lab-solve-a-linear-system)

### 6. Quantum annealing

*Adiabatic evolution, gaps and digitized annealing.*

- Lectures: [Quantum annealing](qs:lesson/circuits/29-quantum-annealing)
- Labs: [Lab: anneal fast and slow](qs:lesson/circuits/110-lab-anneal-fast-and-slow)

## How to study each lecture

1. Read **The idea**, then build the first circuit the lecture mentions before reading on.
2. Redo the **Worked example** on paper, then check it in the State Inspector.
3. Follow **In the app** and change one thing at a time — a gate, an angle, a noise level.
4. Answer the four questions; reread the section behind any wrong answer.
5. Read **Common mistakes** and the **Summary** before the module's labs.

## Check yourself at the end

You have finished this area when you can:

- write the state of a small circuit by hand, in either bit order, and test it for entanglement;
- explain phase kickback and why Deutsch–Jozsa, Grover and the QFT need interference;
- predict how a noise channel changes a state, and use mid-circuit measurement and feed-forward;
- encode, diagnose and correct a single error with a repetition code, and compute its logical error rate;
- estimate a phase, compute an exact gradient with the parameter-shift rule, and run VQE and QAOA;
- explain why an anneal must be slow compared with one over the minimum gap squared.

## Where to go next

- [Quantum ML](qs:lesson/qml/00-study-guide): variational circuits and kernels applied to data.
- [Mathematics](qs:lesson/math/00-study-guide): the tools behind every lecture, when you want them in depth.
