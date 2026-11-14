---
title: What the model leaves out
area: hydrogen
kind: lecture
order: 6
objectives: List the physics beyond the Schrödinger model | Estimate the size of fine-structure and hyperfine effects | Know when the simple model is accurate enough
math: 05-eigenvalues
noglossary: Precision
---
# What the model leaves out

## The idea

Every model leaves something out; a good scientist knows what, and how much it matters. QuantumScope solves the non-relativistic Schrödinger equation with the reduced mass. That model explains the main features of hydrogen remarkably well, but nature has more detail — small effects that took decades to find and that tested physics at its deepest level.

## Electron spin

The electron has spin ½, so each orbital holds two states: every level has $2n^2$ states, not $n^2$. Spin does not change the energies in this model, but it matters for the corrections below.

## Fine structure

Relativistic effects and the coupling between spin and orbital motion (spin–orbit coupling) split levels with the same $n$ by an amount of order $\alpha^2 |E_n|$, where $\alpha \approx 1/137$ is the fine-structure constant. For $n = 2$ the splitting is about $4.5\times10^{-5}$ eV — tiny compared with the 10 eV between $n = 1$ and $n = 2$, but clearly visible in precise spectra.

## The Lamb shift

Quantum electrodynamics shifts 2s slightly above 2p (both with total angular momentum ½) by about $4.4\times10^{-6}$ eV. This small shift was historic evidence for quantum field theory.

## Hyperfine structure

The proton's own magnetic moment splits the ground state by $5.9\times10^{-6}$ eV. The transition between the two hyperfine levels emits the famous **21 cm line** used to map hydrogen in galaxies.

## Other simplifications

- The proton is treated as a point; its finite size shifts s levels by a very small amount.
- The atom is isolated: no external fields, and no emission or decay during the Dynamics animations.

## Worked example

How big is the $n = 2$ fine-structure splitting? The relativistic theory gives, for the two levels with total angular momentum $j = 1/2$ and $j = 3/2$,

$$\Delta E = \frac{\alpha^2 |E_2|}{4} = \frac{3.40\ \mathrm{eV}}{4 \times 137.04^2} \approx 4.5\times10^{-5}\ \mathrm{eV}$$

Compared with Balmer α (1.89 eV), that is a relative shift of about $2\times10^{-5}$: the red line is really a close group of lines, spread over about 0.016 nm. The 21 cm line goes the other way: an energy of $5.9\times10^{-6}$ eV gives $\lambda = 1239.84\ \mathrm{eV\,nm} / 5.87\times10^{-6}\ \mathrm{eV} \approx 2.1\times10^{8}$ nm, which is 21 cm.

## Common mistakes

- **"The model is wrong."** It is incomplete, not wrong: its errors are about one part in ten thousand or smaller.
- **Mixing up the three small effects.** Fine structure splits levels by $j$; the Lamb shift separates 2s from 2p; hyperfine structure comes from the proton's spin.
- **Expecting spin to change the pictures.** Spin doubles the number of states but not the orbital shapes in this model.

## In the app

In the **Hydrogen Explorer**, compare 2s and 2p: the **Scientific information** box gives them exactly the same energy, as the model says. In nature they differ by the fine structure and the Lamb shift, far below the digits that matter for the shapes you see. In **Hydrogen Dynamics**, a 1s + 2p superposition beats forever; a real atom would decay in about 1.6 ns.

[Try it: compare 2s and 2p energies](qs:open/orbital)

## Check your understanding

```quiz
Q: Roughly how large is the n = 2 fine-structure splitting compared with the 2 → 1 energy?
- About the same
- About one tenth
* Less than one ten-thousandth
E: About 4.5 × 10⁻⁵ eV compared with 10.2 eV: a ratio of a few millionths.
```

```quiz
Q: What causes the 21 cm line?
- The 2p → 1s transition
* The hyperfine splitting of the ground state
- The Lamb shift
E: The interaction between electron and proton magnetic moments splits 1s by 5.9 µeV, a 21 cm photon.
```

```quiz
Q: In QuantumScope's model, how many states (including spin) does the level n = 3 hold?
- 9
* 18
- 6
E: n² = 9 orbitals, each holding two spin states: 2n² = 18.
```

```quiz
Q: Which effect separates 2s₁/₂ from 2p₁/₂?
- Fine structure
* The Lamb shift
- The reduced mass
E: Fine structure leaves levels with the same n and j together; quantum electrodynamics shifts 2s₁/₂ slightly above 2p₁/₂.
```

## Summary

- Spin doubles the states; fine structure (∝ α²) splits levels of equal n, by 4.5 × 10⁻⁵ eV for n = 2.
- The Lamb shift and hyperfine structure (the 21 cm line) are smaller still.
- The Schrödinger model is excellent for shapes and main lines; precision work needs the corrections.
