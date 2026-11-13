---
title: Quantum annealing
area: circuits
kind: lecture
order: 29
objectives: Write an optimization problem as an Ising energy whose ground state is the answer | Explain the adiabatic theorem and why the minimum gap sets the anneal time | Relate annealing, digitized annealing and QAOA
math: 05-eigenvalues, 09-matrix-exponentials
---
# Quantum annealing

Many hard problems ask for the best of $2^n$ choices: the best cut of a graph, the best split of a set of numbers, the lowest-energy arrangement of magnets. **Quantum annealing** looks for the answer without a gate-by-gate algorithm. It prepares a ground state that is easy, then changes the Hamiltonian slowly into one whose ground state is the answer.

## The problem as an energy

Give each choice a spin $Z_i = \pm 1$ (the qubit is 0 or 1). Many problems become an **Ising energy**:

$$H_p = \sum_{i<j} J_{ij} Z_i Z_j + \sum_i h_i Z_i$$

$H_p$ is diagonal: every bitstring $x$ has an energy $E(x)$, and the bitstrings with the lowest energy are the answers.

- **MaxCut**: $H_p = \frac{1}{2} \sum_{\mathrm{edges}} (Z_i Z_j - 1)$ is minus the number of cut edges (the same Hamiltonian as in the QAOA lecture).
- **Number partitioning**: put number $a_i$ in group A ($Z_i = +1$) or B ($Z_i = -1$). The difference of the sums is $\sum_i a_i Z_i$, so $H_p = (\sum_i a_i Z_i)^2$ is zero exactly for a perfect split.
- **Spin glass**: random couplings $J_{ij} = \pm 1$. No assignment satisfies every coupling (the glass is **frustrated**), which makes the best one hard to find.

## The anneal

The **driver** $H_d = -\sum_i X_i$ has the ground state $|+\rangle^{\otimes n}$: H on every qubit, every bitstring equally likely. The anneal moves from one to the other as $s = t/T$ goes from 0 to 1:

$$H(s) = (1 - s)\,H_d + s\,H_p$$

**The adiabatic theorem**: if $H(s)$ changes slowly enough, a system that starts in the ground state stays in the instantaneous ground state. At $s = 1$ that is an answer.

How slowly? What matters is the **gap** $\Delta(s)$ between the ground state and the first excited state it could jump to. The usual estimate is

$$T \gg T^{*} = \max_s \frac{|\langle 1(s)|\,\partial_s H\,|0(s)\rangle|}{\Delta(s)^2}$$

The gap enters **squared**: halve the minimum gap and the anneal must be about four times longer. Hard instances have gaps that shrink exponentially with $n$, so the anneal time grows exponentially too. This estimate is a guide, not a guarantee; rigorous bounds have the same dependence on the gap.

## Avoided crossings

Where two levels come close (an **avoided crossing**), a fast sweep jumps straight across, from the ground state into the excited state (a **Landau–Zener** transition). The probability of jumping falls off like $e^{-c\,\Delta^2 T}$, so a crossing whose gap is tiny is jumped by any practical anneal.

A surprise: making the anneal **slower** can then make things **worse**. A slow anneal arrives at the crossing entirely in the ground state, and jumps entirely into the excited state, which ends on a wrong answer. A fast anneal arrives with the state spread over several levels, and some of it ends on the answer by luck. Only an anneal much longer than $T^{*}$ follows the ground state through the crossing.

## Symmetry

In MaxCut and number partitioning every term has two Z's, so flipping every spin changes nothing: $x$ and its complement $\bar x$ are equally good answers. The driver and $|+\rangle^{\otimes n}$ share this symmetry, so the state never leaves the **symmetric** states $(|x\rangle + |\bar{x}\rangle)/\sqrt{2}$. Levels of the other kind may cross the ground level without harm. QuantumScope computes gaps among the symmetric levels for these problems, and says so on the chart.

## Digitized annealing and QAOA

A gate-based computer can **digitize** the anneal: split it into $r$ short slices of length $\Delta t = T/r$ and apply, in each, the problem and driver steps one after the other (Trotterization):

$$e^{-i H(s)\Delta t} \approx e^{-i\,s H_p \Delta t}\; e^{-i\,(1-s) H_d \Delta t}$$

A $Z_i Z_j$ term becomes CX, RZ, CX; a $Z_i$ term becomes RZ; the driver becomes RX on every qubit. More slices follow the exact anneal more closely.

That circuit is exactly **QAOA's** shape: H on every qubit, then alternating cost and mixer layers. QAOA keeps only a few layers and lets an optimizer choose their angles, instead of fixing them by a schedule. With many layers, QAOA can at least match the anneal, since the anneal's angles are one choice it could make.

## Annealing on hardware, and simulated annealing

Commercial quantum annealers (such as D-Wave's) run this physically, on thousands of superconducting qubits. They are not ideal: they are at a finite temperature, they lose coherence, and they can only couple certain pairs of qubits. Whether they outperform the best classical methods on useful problems is still debated: no general speedup has been shown.

**Simulated annealing** (one of the optimizers in the circuit tab) is a classical cousin: random moves at a falling temperature, climbing over barriers thermally. Quantum annealing can instead **tunnel** through tall, thin barriers.

## In QuantumScope

Open **+ → Quantum annealing** in the Quantum Circuits area. Choose a problem and an anneal time $T$:

- **Spectrum**: the lowest levels of $H(s)$, with the minimum gap marked and $T^{*}$ reported.
- **During the anneal**: the probability of the answer and the overlap with the instantaneous ground state, against $s$, and the likeliest bitstrings at any $s$.
- **Success against T**: the probability of the answer for anneals from $T = 0.5$ to 80.
- **Open as circuit**: the digitized anneal in the circuit simulator, with $H_p$ as the observable.

[Try it: open Quantum annealing](qs:open/annealing)

## Check your understanding

```quiz
Q: The minimum gap of one instance is three times smaller than another's. Roughly how much longer must its anneal be?
- Three times
* Nine times
- The same: the gap does not matter
E: The adiabatic time scale grows like 1/Δ², so a third of the gap needs about 3² = 9 times the time.
```

```quiz
Q: Why does the anneal start in |+⟩ on every qubit?
* It is the ground state of the driver −ΣX, where H(s) begins
- It is the answer to every problem
- It is the ground state of the problem Hamiltonian
E: At s = 0 the Hamiltonian is the driver; its ground state is |+…+⟩, which H on every qubit prepares.
```

```quiz
Q: A spin glass has an avoided crossing with a gap of 0.002. Anneals with T = 10 find the answer 45% of the time, but with T = 1,000 only 2%. What is happening?
- The simulation is wrong: slower anneals always do better
* The slow anneal reaches the crossing in the ground state and jumps it completely; only far longer anneals would follow the gap
- Longer anneals pick up more noise
E: A gap that small is jumped at any practical speed. A slow anneal arrives entirely in the ground state, so all of it jumps to the wrong level. The adiabatic theorem still holds, but only for T well beyond T*.
```

```quiz
Q: How does QAOA differ from a digitized anneal?
- QAOA uses a different problem Hamiltonian
- QAOA has no mixer layer
* QAOA uses the same layers, but few of them, with angles chosen by an optimizer
E: Both alternate cost and mixer layers starting from |+…+⟩. The anneal fixes the angles by its schedule and needs many slices; QAOA optimizes a few layers' angles.
```
