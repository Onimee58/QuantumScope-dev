---
title: Energy levels and spectra
area: hydrogen
kind: lecture
order: 4
objectives: Compute hydrogen's energy levels | Predict the wavelengths of spectral lines | State the dipole selection rule
math: 05-eigenvalues
---
# Energy levels and spectra

## The idea

Heat hydrogen gas and it glows, but only at a few sharp colors. Each color is a photon carrying away exactly the energy difference between two levels of the atom. Because the levels follow one simple formula, a handful of numbers predicts the whole spectrum — this was one of the first great successes of quantum mechanics.

## Energy levels

The energies depend only on $n$:

$$E_n = -\frac{\mu}{m_e}\,\frac{13.606\ \mathrm{eV}}{n^2} \approx -\frac{13.598\ \mathrm{eV}}{n^2}$$

| n | Energy |
|---|---|
| 1 | −13.598 eV |
| 2 | −3.400 eV |
| 3 | −1.511 eV |
| 4 | −0.850 eV |

The negative sign means the electron is bound; 13.598 eV is needed to ionize the atom from its ground state. The levels crowd together as $n$ grows and approach 0, the ionization limit.

## Spectral lines

A jump from level $n_i$ to $n_f$ emits a photon of energy $E_{n_i} - E_{n_f}$ and wavelength $\lambda = hc/\Delta E$:

$$\frac{1}{\lambda} = R_\mu\left(\frac{1}{n_f^2} - \frac{1}{n_i^2}\right)$$

with $R_\mu \approx 1.0968\times10^{7}\ \mathrm{m^{-1}}$, the Rydberg constant for hydrogen's reduced mass.

| Line | Transition | Energy | Wavelength (vacuum) |
|---|---|---|---|
| Lyman α | 2 → 1 | 10.199 eV | 121.6 nm (ultraviolet) |
| Lyman β | 3 → 1 | 12.087 eV | 102.6 nm |
| Balmer α | 3 → 2 | 1.889 eV | 656.5 nm (red) |

Measured in air, Balmer α is the familiar 656.3 nm red line. Lines ending on $n = 1$ form the ultraviolet **Lyman series**; lines ending on $n = 2$ form the **Balmer series**, partly visible.

## Selection rules

Light emitted or absorbed in a single photon (electric dipole) changes $\ell$ by exactly one: $\Delta\ell = \pm 1$. So 2p → 1s is allowed, but 2s → 1s is not; the 2s state is **metastable** and lives far longer.

## Worked example

Balmer β is the jump $4 \to 2$:

$$\Delta E = E_4 - E_2 = -0.8499 - (-3.3996) = 2.5497\ \mathrm{eV}$$

$$\lambda = \frac{hc}{\Delta E} = \frac{1239.84\ \mathrm{eV\,nm}}{2.5497\ \mathrm{eV}} \approx 486.3\ \mathrm{nm}$$

a blue-green line. The Balmer series ends where $n_i \to \infty$: $\Delta E = 3.400$ eV, so $\lambda = 364.7$ nm, the **Balmer limit**. Every Balmer line lies between 364.7 nm and 656.5 nm.

## Common mistakes

- **Dropping the sign.** Bound energies are negative; an emitted photon's energy is the *difference*, always positive.
- **Mixing up $n_i$ and $n_f$ in the Rydberg formula.** The lower level is $n_f$ for emission; swap them and $1/\lambda$ turns negative.
- **Assuming any two levels give a line.** 2s → 1s has the right energy, but $\Delta\ell = 0$ forbids a single photon.

## In the app

In the **Hydrogen Explorer**, the **Scientific information** box gives each state's energy. Read off $E_2$ and $E_4$ and repeat the worked example. Note that changing ℓ or m does not change the energy. In **Hydrogen Dynamics**, the beat period of a superposition is the period of the light its transition would emit: for 1s + 2p it is 121.6 nm divided by the speed of light.

[Try it: energies in the Hydrogen Explorer](qs:open/orbital)

## Check your understanding

```quiz
Q: How much energy ionizes hydrogen from n = 2?
- 13.6 eV
- 10.2 eV
* 3.4 eV
E: The ionization energy from level n is −Eₙ; for n = 2, that is 13.598/4 ≈ 3.4 eV.
```

```quiz
Q: Which transition is allowed for a single photon?
* 3p → 1s
- 3d → 1s
- 2s → 1s
E: Δℓ must be ±1: p (ℓ = 1) → s (ℓ = 0) is allowed; d → s (Δℓ = 2) and s → s (Δℓ = 0) are not.
```

```quiz
Q: Which line has the shortest wavelength?
- Balmer α (3 → 2)
- Lyman α (2 → 1)
* Lyman β (3 → 1)
E: The largest energy gives the shortest wavelength: 12.087 eV for Lyman β, so 102.6 nm.
```

```quiz
Q: Why is the Lyman series in the ultraviolet while part of the Balmer series is visible?
* Jumps to n = 1 release at least 10.2 eV; jumps to n = 2 release at most 3.4 eV
- Lyman lines come from heavier atoms
- Balmer lines use two photons
E: Visible light carries about 1.7–3.1 eV. Every Lyman photon carries more than 10 eV; Balmer photons carry 1.9–3.4 eV.
```

## Summary

- Eₙ ≈ −13.598 eV / n² (with the reduced mass); levels crowd toward 0.
- Photon wavelengths follow the Rydberg formula; Lyman α is 121.6 nm, Balmer α 656.5 nm and Balmer β 486.3 nm in vacuum.
- Single-photon transitions obey Δℓ = ±1.
