---
title: "Lab: build up an interference pattern"
area: principles
kind: lab
order: 91
objectives: Watch single detections build an interference pattern | Relate fringe spacing to the slit separation and the envelope to the slit width | See which-path information remove the fringes
math: 01-complex-numbers
---
# Lab: build up an interference pattern

Particles arrive one at a time at single spots, yet together they draw stripes. You will change the slits and see each part of the pattern respond, then switch on which-path detectors. Read *Interference: the double slit* first.

[Open the Double-slit experiment](qs:open/doubleslit)

```step
title: Build the pattern from single particles
text: Keep the default slits (wavelength 500 nm, width 20 µm, separation 100 µm, screen 1 m) and press Fire particles until at least 1,000 have arrived. The info line gives the fringe spacing: λL/d = 5 mm.
hint: Change the speed to Instant if you do not want to wait.
check: did slit wavelength=500 width=20 separation=100 distance=1 whichpath=0 particles>=1000
```

```step
title: Move the slits apart
text: Set the Slit separation to 200 µm and fire at least 1,000 particles again. The fringes are now 2.5 mm apart, but the envelope that holds them has not changed.
hint: Spacing λL/d halves when d doubles; the envelope depends on the slit width.
check: did slit separation=200 whichpath=0 particles>=1000
```

```step
title: Make the slits narrower
text: Set the Slit width to 10 µm (any separation) and fire again. The envelope widens — its first zeros move from ±25 mm to ±50 mm — so more fringes fit under it.
check: did slit width=10 whichpath=0 particles>=1000
```

```step
title: Ask which slit
text: Tick Which-path detectors at the slits and fire at least 1,000 particles. The fringes vanish: what is left is the sum of the two single-slit patterns.
hint: Any record of the path makes the two paths distinguishable, which removes the interference term.
check: did slit whichpath=1 particles>=1000
```

## What you found

Each particle lands at one point, but the probabilities that build the pattern come from adding two amplitudes. The slit separation sets the fringe spacing, the slit width sets the envelope, and path information removes the fringes altogether.

```quiz
Q: The wavelength is changed from 500 nm to 600 nm, everything else kept. What happens to the fringe spacing?
* It grows by 20%, to 6 mm
- It shrinks to about 4.2 mm
- It stays 5 mm
E: Δy = λL/d is proportional to λ: 600/500 × 5 mm = 6 mm.
```
