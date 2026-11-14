---
title: The Schrödinger equation and the hydrogen atom
area: hydrogen
kind: lecture
order: 1
objectives: Write the time-independent Schrödinger equation for hydrogen | Explain the reduced mass and the length unit a_μ | Separate the wavefunction into radial and angular parts
math: 01-complex-numbers, 05-eigenvalues, 09-matrix-exponentials
---
# The Schrödinger equation and the hydrogen atom

## The idea

Hydrogen, one electron bound to one proton, is the simplest atom and the one quantum mechanics solves exactly. Its solutions explain why atoms have definite sizes, why they emit light only at certain colors, and where the shapes s, p and d come from. Every picture in the Hydrogen area is an exact solution of one equation.

## The equation

An electron bound to a proton by the Coulomb force obeys the time-independent Schrödinger equation

$$-\frac{\hbar^2}{2\mu}\nabla^2\psi - \frac{e^2}{4\pi\varepsilon_0 r}\psi = E\psi$$

The first term is the kinetic energy, the second the attraction between the charges. Its solutions $\psi$ are the stationary states (**orbitals**) and $E$ their energies. Only certain energies allow a solution that stays finite everywhere and vanishes far away: that is where quantization comes from.

## The reduced mass

The proton is not infinitely heavy: electron and proton both move around their common center of mass. This is handled exactly by replacing the electron mass with the **reduced mass**

$$\mu = \frac{m_e m_p}{m_e + m_p} \approx 0.99946\, m_e$$

QuantumScope uses $\mu$ throughout. Lengths are measured in the reduced-mass Bohr radius $a_\mu = a_0\, m_e/\mu \approx 52.95$ pm, slightly larger than the textbook $a_0 \approx 52.92$ pm, and energies come out about 0.05% smaller in magnitude than with an infinitely heavy proton.

## Separation of variables

Because the force depends only on distance, the solutions factor into a radial and an angular part:

$$\psi_{n\ell m}(r,\theta,\varphi) = R_{n\ell}(r)\,Y_{\ell m}(\theta,\varphi)$$

The **spherical harmonics** $Y_{\ell m}$ set the shape; the radial functions $R_{n\ell}$ set the size and the radial nodes. The three integers $n$, $\ell$, $m$ are the subject of the next lecture.

## Worked example

Does a 0.05% correction matter? Compare hydrogen with deuterium, whose nucleus (a proton and a neutron) is about twice as heavy:

$$\frac{\mu_{\mathrm{H}}}{m_e} = \frac{1836.15}{1837.15} \approx 0.999456, \qquad \frac{\mu_{\mathrm{D}}}{m_e} = \frac{3670.48}{3671.48} \approx 0.999728$$

Energies scale with $\mu$, so wavelengths scale with $1/\mu$. Hydrogen's red Balmer α line at 656.47 nm (in vacuum) moves to $656.47 / 1.000272 \approx 656.29$ nm for deuterium: a shift of 0.18 nm, easily seen with a good spectrometer. This tiny shift is how deuterium was discovered in 1931.

## Common mistakes

- **Using the electron mass and calling it exact.** With $m_e$ the model treats the proton as fixed; the reduced mass makes the two-body problem exact.
- **Thinking $\psi$ is the electron's charge cloud.** $|\psi|^2$ is a probability density for finding the electron; the electron is not smeared out.
- **Expecting the shape from $R$.** Size and radial nodes come from $R_{n\ell}$; the angular shape comes only from $Y_{\ell m}$.

## In the app

Open the **Hydrogen Explorer**, choose **Principal n**, **Angular l** and **Magnetic m**, and press **Render state**. The **Scientific information** box shows the state's energy and the reduced-mass Bohr radius used for the axes. Keep $n$ fixed and change $\ell$: the shape changes while the energy does not.

[Try it: the Hydrogen Explorer](qs:open/orbital)

## Check your understanding

```quiz
Q: Why does QuantumScope use the reduced mass μ instead of the electron mass?
* Because the proton also moves, about the common center of mass
- Because the electron is relativistic
- To make the equations simpler
E: Replacing m_e by μ accounts exactly for the motion of both particles in a two-body problem.
```

```quiz
Q: What determines the shape of an orbital?
- The radial function R(r)
* The spherical harmonic Y(θ, φ)
- The energy E
E: Y sets the angular dependence (s, p, d …); R sets size and radial nodes.
```

```quiz
Q: Why can the hydrogen wavefunction be split into R(r) times Y(θ, φ)?
- Because the electron moves in a circle
* Because the Coulomb force depends only on the distance r
- Because the proton is heavy
E: A force that depends only on distance has no preferred direction, so the radial and angular parts separate.
```

```quiz
Q: Deuterium's nucleus is heavier than hydrogen's. What happens to its spectral lines?
- They are identical
* They shift slightly to shorter wavelengths
- They shift to much longer wavelengths
E: A heavier nucleus makes μ closer to m_e, so the energies are slightly larger and the wavelengths slightly shorter (656.47 → 656.29 nm for Balmer α).
```

## Summary

- Hydrogen's stationary states solve −(ħ²/2μ)∇²ψ − e²/(4πε₀r)ψ = Eψ; only certain energies allow solutions.
- The reduced mass μ ≈ 0.99946 mₑ makes the two-body problem exact; lengths use a_μ ≈ 52.95 pm.
- The reduced mass is measurable: it shifts deuterium's lines by about 0.03%.
- ψ = R(r) Y(θ, φ): size from R, shape from Y.
