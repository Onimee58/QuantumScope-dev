---
title: "Interference: the double slit"
area: principles
kind: lecture
order: 3
objectives: Explain interference as adding amplitudes, not probabilities | Predict the fringe spacing | Explain why which-path information destroys interference
math: 01-complex-numbers
---
# Interference: the double slit

## The idea

Send particles one at a time through two slits. Each lands at a single spot, yet together they build up bright and dark stripes, as waves would. The reason is the central rule of quantum mechanics: when a result can happen in several indistinguishable ways, you add the **amplitudes** of the ways, and only then square. Amplitudes can cancel; probabilities cannot.

## Adding amplitudes

A particle reaches a point $y$ on the detector by two paths with amplitudes $\psi_1(y)$ and $\psi_2(y)$. Quantum mechanics adds the amplitudes, then squares:

$$P(y) = |\psi_1(y) + \psi_2(y)|^2 = |\psi_1|^2 + |\psi_2|^2 + 2\,\mathrm{Re}\,(\psi_1^*\psi_2)$$

The last term is **interference**: it can be positive (bright fringes) or negative (dark fringes), so at some points adding a second slit *reduces* the chance of arrival.

## Fringe spacing

For slits a distance $d$ apart, a screen at distance $L$ and wavelength $\lambda$ (for particles, the de Broglie wavelength $h/p$), the path difference sets the phase, and the bright fringes are separated by

$$\Delta y = \frac{\lambda L}{d}$$

Each slit's finite width $a$ adds a broad diffraction envelope that modulates the fringes, with its first zeros at $y = \pm\lambda L/a$. QuantumScope's double-slit view keeps the two apart: the ideal two-path pattern and the full diffraction pattern.

## Which-path information

If anything records which slit the particle used, the two paths become distinguishable and the cross term vanishes: the pattern becomes the plain sum of two single-slit patterns. Interference needs the paths to be indistinguishable.

## The same physics in a circuit

A Mach–Zehnder interferometer is two Hadamards: $H\,H|0\rangle = |0\rangle$ because the two paths to $|1\rangle$ cancel. A phase on one path, $P(\varphi)$ between the Hadamards, moves the fringe: $P(1) = \sin^2(\varphi/2)$.

## Worked example

Green light, $\lambda = 500$ nm, slits $d = 100$ µm apart, each $a = 20$ µm wide, screen $L = 1$ m away:

$$\Delta y = \frac{500\times10^{-9} \times 1}{100\times10^{-6}} = 5\ \mathrm{mm}$$

The envelope's first zeros are at $\lambda L/a = 25$ mm, so the central envelope holds about nine bright fringes, 5 mm apart. Doubling $d$ to 200 µm halves the spacing to 2.5 mm and fits about twice as many fringes under the same envelope.

## Common mistakes

- **Adding probabilities.** $|\psi_1|^2 + |\psi_2|^2$ has no dark fringes. The fringes come only from the cross term.
- **Mixing up the two scales.** Fringe spacing depends on the slit *separation* $d$; the envelope depends on the slit *width* $a$.
- **Thinking the detector "disturbs" the particle mechanically.** Any record of the path removes the fringes, however gentle; what matters is that the paths become distinguishable.

## In the app

In **Quantum Principles → Double slit**, the defaults are the worked example's values. Press **Fire particles** and watch single dots build up the pattern. Change **Slit separation** and **Slit width** to see the fringes and the envelope respond separately, then switch on **Which-path detectors at the slits**: the fringes disappear.

[Try it: the double-slit experiment](qs:open/doubleslit)

[Try it: H, phase π, H](qs:circuit?n=1&gates=H:0;P:0:pi;H:0&inspector=1)

## Check your understanding

```quiz
Q: The slit separation d is doubled. What happens to the fringe spacing?
- It doubles
* It halves
- It stays the same
E: Δy = λL/d, so doubling d halves Δy.
```

```quiz
Q: A detector records which slit each particle uses. What do you see?
- The same fringes, dimmer
* No interference fringes, just the sum of two single-slit patterns
- Fringes twice as fine
E: Which-path information makes the paths distinguishable and removes the interference term.
```

```quiz
Q: The slits are made narrower but kept the same distance apart. What changes?
- The fringes get closer together
* The envelope gets wider, so more fringes fit under it
- Nothing at all
E: The envelope's zeros sit at ±λL/a, so a smaller width a spreads the envelope; the spacing λL/d is unchanged.
```

```quiz
Q: In the circuit H, P(φ), H on |0⟩, which phase sends the qubit to |1⟩ with certainty?
- φ = 0
- φ = π/2
* φ = π
E: P(1) = sin²(φ/2), which is 1 at φ = π: the two paths to |0⟩ cancel instead.
```

## Summary

- Interference comes from adding amplitudes before squaring.
- Bright fringes are λL/d apart; the slit width sets a diffraction envelope with zeros at ±λL/a.
- Which-path information removes the interference term.
- Two Hadamards with a phase between them are the same interferometer, in a circuit.
