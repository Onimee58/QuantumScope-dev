---
title: "Study guide: Quantum Principles"
area: principles
kind: guide
order: 0
objectives: See what this area covers and in which order | Check that you have the background you need | Know what you should be able to do at the end
---
# Study guide: Quantum Principles

## What this area is about

Quantum Principles builds the ideas that every other area uses: what a quantum state is, what a measurement does, why amplitudes interfere, and how two particles can share one state. Each lecture has an interactive experiment you can run while you read. No programming is needed.

**Who it is for:** anyone starting quantum computing or quantum physics, including people from industry with no physics background.

**Time:** about 10–12 hours in total — roughly 45 minutes per lecture and 45 minutes per lab.

## Before you start

You need comfort with algebra and basic trigonometry. Complex numbers and vectors help a lot; if they are new or rusty, read these Mathematics lectures first or alongside:

- [Complex numbers](qs:lesson/math/01-complex-numbers)
- [Vectors and Dirac notation](qs:lesson/math/02-vectors-and-dirac-notation)
- [Probability](qs:lesson/math/06-probability)

Each lecture also lists the mathematics it needs under **Math you need**.

## Suggested path

| Week | Lecture or lab | You will be able to |
|---|---|---|
| 1 | [Superposition and the Bloch sphere](qs:lesson/principles/01-superposition-and-bloch-sphere) | place any qubit state on a sphere |
| 1 | [Measurement and the Born rule](qs:lesson/principles/02-measurement-and-born-rule) | compute outcome probabilities along any axis |
| 1 | [Lab: find states on the Bloch sphere](qs:lesson/principles/90-lab-bloch-sphere) | check the Born rule against your own counts |
| 2 | [Interference: the double slit](qs:lesson/principles/03-double-slit-interference) | predict fringes from added amplitudes |
| 2 | [Lab: build up an interference pattern](qs:lesson/principles/91-lab-interference) | see fringes, envelope and which-path information |
| 2 | [Global and relative phase](qs:lesson/principles/05-global-and-relative-phase) | tell which phases are physical |
| 2 | [Lab: reveal a hidden phase](qs:lesson/principles/93-lab-hidden-phase) | make a phase visible with interference |
| 3 | [Entanglement and Bell states](qs:lesson/principles/04-entanglement-and-bell-states) | explain a Bell test and why it rules out pre-set answers |
| 3 | [Lab: run a Bell test](qs:lesson/principles/92-lab-bell-test) | beat the classical limit, then lose it to noise |
| 3 | [Measurement, information and no-cloning](qs:lesson/principles/07-measurement-information-no-cloning) | prove that unknown states cannot be copied |
| 4 | [Density matrices and mixed states](qs:lesson/principles/06-density-matrices-and-mixed-states) | tell superposition from ignorance |
| 4 | [Lab: pure, mixed and entangled](qs:lesson/principles/94-lab-pure-mixed-entangled) | tell entanglement from noise |
| 4 | [Observables and expectation values](qs:lesson/principles/08-observables) | compute ⟨O⟩ and state the variational principle |

The order differs slightly from the numbering: phase (lecture 5) is easiest right after interference, before entanglement.

## How to study each lecture

1. Read **The idea** first, and say it back in one sentence of your own.
2. Work through the **Worked example** with pen and paper before reading its numbers.
3. Run the **In the app** experiment and check that it agrees with your numbers.
4. Answer the four questions without looking back. If you miss one, reread that section.
5. Read **Common mistakes** last: you should recognize most of them by then.

## Check yourself at the end

You are ready to move on to Quantum Circuits when you can:

- write $\cos\frac{\theta}{2}|0\rangle + e^{i\varphi}\sin\frac{\theta}{2}|1\rangle$ for any point on the Bloch sphere, and back;
- compute $P = |\langle b|\psi\rangle|^2$ and explain why many shots are needed;
- explain why $|+\rangle$ and $|-\rangle$ differ although both give 50:50;
- state the CHSH limit 2 and the quantum value $2\sqrt{2}$;
- write the density matrix of a mixture and compute its purity.

## Where to go next

- [Quantum Circuits](qs:lesson/circuits/00-study-guide): gates, circuits and algorithms, built on these ideas.
- [Hydrogen](qs:lesson/hydrogen/00-study-guide): the same quantum rules, applied to a real atom.
