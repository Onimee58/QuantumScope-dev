---
title: Superposition and quantum beats
area: hydrogen
kind: lecture
order: 5
objectives: Explain why stationary states have time-independent densities | Compute the beat period of a two-state superposition | Interpret the Hydrogen Dynamics views correctly
math: 01-complex-numbers, 09-matrix-exponentials
---
# Superposition and quantum beats

## The idea

A single orbital never changes: its cloud sits still forever. Put the atom into two orbitals at once, though, and the cloud starts to move, sloshing back and forth with a period set by the energy difference. This **quantum beat** is the same interference as in the double slit, but in time instead of space, and it connects the orbitals you see to the light the atom emits.

## Stationary states

A single energy eigenstate evolves as $\psi(t) = \psi\,e^{-iEt/\hbar}$. The phase factor has magnitude one, so $|\psi(t)|^2$ never changes: that is why eigenstates are called **stationary**.

## Two states at once

A superposition of two levels,

$$\Psi(t) = \sqrt{p}\,\psi_a e^{-iE_a t/\hbar} + \sqrt{1-p}\,\psi_b e^{-iE_b t/\hbar}$$

has a density with a cross term oscillating at the energy difference. It repeats with the **beat period**

$$T = \frac{h}{|E_a - E_b|}$$

| States | Beat period |
|---|---|
| 1s + 2p | 0.4055 fs |
| 1s + 3d | 0.3421 fs |
| 2s + 2p | none (same energy: stationary) |

For 1s + 2p the cloud sloshes from one side of the nucleus to the other. A charge doing this radiates, which is how such a state emits light — but the 2p lifetime is about 1.6 ns, millions of beat periods, so the Dynamics views show the beating without the slow decay.

## What the animation is — and is not

The animation shows the exact time-dependent probability density. It is **not** a trajectory: the electron is not a particle moving along a path inside the cloud. Only the density changes, and only because of the interference between the two states.

## Worked example

Take 2s + 3p. The energies are $E_2 \approx -3.3996$ eV and $E_3 \approx -1.5109$ eV, so

$$T = \frac{h}{|E_3 - E_2|} = \frac{4.1357\times10^{-15}\ \mathrm{eV\,s}}{1.8887\ \mathrm{eV}} \approx 2.19\ \mathrm{fs}$$

That is the period of the light with energy 1.8887 eV: Balmer α, whose wavelength 656.5 nm divided by the speed of light is also 2.19 fs. The beat and the emitted light share one frequency. The fraction $p$ sets how strongly the cloud moves (most for $p = 0.5$), not how fast.

## Common mistakes

- **Expecting a single orbital to move.** One eigenstate's density is constant; motion needs two energies.
- **Thinking the electron orbits.** The changing cloud is a changing probability density, not a path.
- **Expecting equal energies to beat.** 2s + 2p has the same energy in this model, so it is itself stationary: a new, lopsided but motionless orbital.

## In the app

Open **Hydrogen Dynamics 2D** or **3D**. Choose **State A** and **State B**, set **State A probability** to 50%, and press **Play**. The period shown matches $h/|E_a - E_b|$; try 1s + 2p and 1s + 3d from the table. Then pick 2s + 2p: the density is lopsided but does not move. The **Time / beat period** slider steps through one period by hand.

[Try it: Hydrogen Dynamics 3D](qs:open/dynamics3d)

[Try it: Hydrogen Dynamics 2D](qs:open/dynamics2d)

## Check your understanding

```quiz
Q: Why does a 2s + 2p superposition not beat in this model?
* The two states have the same energy
- 2s is spherically symmetric
- The superposition is not normalized
E: T = h/|E_a − E_b| is infinite when the energies are equal, so the density stays constant.
```

```quiz
Q: What does the animated cloud represent?
- The electron's path around the nucleus
* How the probability density changes in time
- The shape of the emitted light
E: Quantum mechanics gives a probability density, not a trajectory.
```

```quiz
Q: Why does 1s + 3d beat faster than 1s + 2p?
* The energy difference is larger, and T = h/|ΔE|
- d orbitals are larger
- 3d has more nodes
E: E₃ − E₁ ≈ 12.09 eV is larger than E₂ − E₁ ≈ 10.20 eV, so the period is shorter: 0.3421 fs against 0.4055 fs.
```

```quiz
Q: In a 1s + 2p superposition, State A probability is changed from 50% to 90%. What changes?
- The beat period becomes shorter
* The cloud moves less, with the same period
- The cloud stops moving
E: The period depends only on the energies. A lopsided mixture has a smaller cross term, so the sloshing is weaker.
```

## Summary

- Eigenstates have constant densities; superpositions of different energies beat.
- The beat period is h/|E_a − E_b|: 0.4055 fs for 1s + 2p, the period of the light the transition emits.
- The mixture sets how much the cloud moves, not how fast.
- The animation shows probability density, not motion along a path.
