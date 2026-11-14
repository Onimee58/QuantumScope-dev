---
title: "Lab: a tour of orbitals"
area: hydrogen
kind: lab
order: 90
objectives: Draw orbitals from their quantum numbers | Compare the complex and real p orbitals | Read nodes from the sign of ψ
math: 05-eigenvalues
---
# Lab: a tour of orbitals

You will draw hydrogen orbitals from their three quantum numbers and learn to read their shapes: the size from n, the shape from ℓ, the orientation from m — and the nodes from the sign of ψ. Read *Quantum numbers and orbitals* first.

[Open the Hydrogen Explorer](qs:open/orbital)

```step
title: The ground state
text: Set Principal n = 1 (Angular l and Magnetic m are then 0) and press Render state. The 1s orbital is a sphere; the Scientific information box gives its energy, −13.598 eV.
check: did orbital n=1 l=0
```

```step
title: A ring and a dumbbell
text: Draw n = 2, l = 1, m = 1 with Orbital basis Complex Y(l,m): the density is a ring around the z axis. Then switch the basis to Real cosine and render again: the same energy, now a dumbbell along x — chemistry's 2pₓ.
hint: Complex m = ±1 states carry angular momentum about z; the real combinations point along x and y.
check: did orbital n=2 l=1 m=1 basis=complex
check: did orbital n=2 l=1 m=1 basis=cosine
```

```step
title: Count the nodes of a d orbital
text: Draw n = 3, l = 2, m = 0 and set Representation to Real(psi). The two colors are the signs of ψ; the boundaries between them are the nodes. A 3d orbital has two angular nodes (here two cones) and no radial node.
check: did orbital n=3 l=2 view=real
```

```step
title: Three radial nodes' worth of shells
text: Draw n = 4, l = 0 with Real(psi). How many nested shells of alternating sign do you see? Compare with n − ℓ − 1.
hint: Zoom in if the inner shells are small: they sit close to the nucleus.
check: did orbital n=4 l=0 view=real
```

## What you found

The orbital's size grows with n, its shape follows ℓ, and m turns or rotates it. Nodes split between spheres (n − ℓ − 1) and angular surfaces (ℓ), always n − 1 in total: 4s shows three spherical nodes, four shells.

```quiz
Q: How many radial nodes does the 4s orbital have?
- 4
* 3
- 0
E: n − ℓ − 1 = 4 − 0 − 1 = 3: four shells separated by three spherical nodes.
```

```quiz
Q: Do the complex 2p (m = 1) and the real 2pₓ orbitals have the same energy?
* Yes: energy depends only on n in this model
- No: the real one is lower
- No: the complex one is lower
E: All states with the same n share one energy; the bases are just different combinations.
```
