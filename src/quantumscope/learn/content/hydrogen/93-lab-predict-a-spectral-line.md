---
title: "Lab: predict a spectral line"
area: hydrogen
kind: lab
order: 93
objectives: Read energy levels from the Hydrogen Explorer | Compute photon wavelengths with λ = hc/ΔE | Find the limit of a spectral series
math: 05-eigenvalues
---
# Lab: predict a spectral line

You will read hydrogen's energy levels from the app, compute the wavelengths of its spectral lines in the calculator, and compare them with the measured values. Read *Energy levels and spectra* first.

[Open the Hydrogen Explorer](qs:open/orbital)

```step
title: Read two energy levels
text: Draw any state with n = 2 and then any state with n = 4, and note their energies from the Scientific information box: about −3.3996 eV and −0.8499 eV.
check: did orbital n=2
check: did orbital n=4
```

```step
title: Balmer β
text: Open the calculator and compute the wavelength of the 4 → 2 line in nanometres: 1239.84 divided by the energy difference in eV. You should get about 486.3 nm, a blue-green line.
hint: For example 1239.84/(3.3996 - 0.8499).
check: calc gives 486.27±0.3
```

```step
title: The edge of the Balmer series
text: Lines ending on n = 2 crowd toward a limit as the upper level goes to infinity, where its energy is 0. Compute that wavelength: 1239.84/3.3996.
check: calc gives 364.71±0.3
```

```step
title: Into the ultraviolet
text: Draw n = 1 to read its energy, then compute Lyman α, the 2 → 1 line. It lies far in the ultraviolet, near 121.6 nm.
check: did orbital n=1
check: calc gives 121.57±0.2
```

## What you found

Every line is the energy difference of two levels: Balmer lines end on n = 2 and lie between 364.7 nm and 656.5 nm, Lyman lines end on n = 1 and are all ultraviolet.

[Open the calculator](qs:open/calculator)

```quiz
Q: Which transition gives the Balmer α line at 656.5 nm?
* 3 → 2
- 2 → 1
- 4 → 2
E: E₃ − E₂ ≈ 1.889 eV, and 1239.84/1.889 ≈ 656.5 nm.
```
