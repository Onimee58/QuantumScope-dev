---
title: Quantum numbers and orbitals
area: hydrogen
kind: lecture
order: 2
objectives: List the allowed values of n, ℓ and m | Count states per energy level | Predict the number of radial and angular nodes
noglossary: Orbital
math: 05-eigenvalues
---
# Quantum numbers and orbitals

## The idea

Each hydrogen state is labeled by three whole numbers, $n$, $\ell$ and $m$. They are not arbitrary tags: each one answers a physical question — how much energy, how much angular momentum, which orientation — and together they predict an orbital's size, its shape and where it is exactly zero. Learning to read them lets you sketch any orbital before you see it.

## The three quantum numbers

| Number | Name | Allowed values | Sets |
|---|---|---|---|
| n | principal | 1, 2, 3, … | energy and overall size |
| ℓ | orbital angular momentum | 0, 1, …, n − 1 | shape (s, p, d, f for ℓ = 0, 1, 2, 3) |
| m | magnetic | −ℓ, …, +ℓ | orientation about the z axis |

## Counting states

For each $\ell$ there are $2\ell + 1$ values of $m$, so level $n$ holds

$$\sum_{\ell=0}^{n-1}(2\ell+1) = n^2$$

[[orbitals|Orbital]], all with the same energy in this model (spin doubles this to $2n^2$). For $n = 2$: one 2s and three 2p orbitals.

## Nodes

An orbital has $n - \ell - 1$ **radial nodes** (spheres where $\psi = 0$) and $\ell$ **angular nodes** (planes or cones), $n - 1$ in total. The 2s orbital has one radial node; 2p has one nodal plane; 3d has two angular nodes.

## Complex and real orbitals

The states $\psi_{n\ell m}$ with $m \ne 0$ are complex: their density is symmetric around $z$ and they carry angular momentum about that axis. Chemistry's familiar $p_x$ and $p_y$ are **real** combinations of $m = +1$ and $m = -1$; they have the same energy, and they point along $x$ and $y$.

## Worked example

List every orbital with $n = 3$ and its nodes:

| Orbital | ℓ | Values of m | Count | Radial nodes | Angular nodes |
|---|---|---|---|---|---|
| 3s | 0 | 0 | 1 | 2 | 0 |
| 3p | 1 | −1, 0, +1 | 3 | 1 | 1 |
| 3d | 2 | −2 … +2 | 5 | 0 | 2 |

The count is $1 + 3 + 5 = 9 = 3^2$, and every row has $n - 1 = 2$ nodes in total. As $\ell$ grows, nodes move from spheres to planes and cones: 3s is three nested shells, 3d has no radial node at all.

## Common mistakes

- **Allowing ℓ = n.** For $n = 2$, ℓ is 0 or 1 only; there is no 2d orbital.
- **Reading m as a size.** $m$ changes orientation and angular momentum about $z$, not energy or size.
- **Expecting p orbitals to look like dumbbells for every m.** With the complex basis, $m = \pm 1$ gives a ring around the $z$ axis; the dumbbells along $x$ and $y$ are the real combinations.

## In the app

In the **Hydrogen Explorer**, set **Principal n** to 3 and step **Angular l** through 0, 1 and 2. Use **Representation → Real(psi)** to see the sign of ψ: each node is a boundary between colors. Then set ℓ = 1, m = 1 and switch **Orbital basis** between *Complex Y(l,m)* (a ring) and *Real cosine* (a dumbbell along $x$). The **Radial probability** chart shows the radial nodes as zeros.

[Try it: compare orbitals in the Hydrogen Explorer](qs:open/orbital)

## Check your understanding

```quiz
Q: How many orbitals (ignoring spin) have n = 3?
- 3
- 6
* 9
- 18
E: n² = 9: one 3s, three 3p and five 3d.
```

```quiz
Q: How many radial nodes does a 3p orbital have?
- 0
* 1
- 2
E: n − ℓ − 1 = 3 − 1 − 1 = 1.
```

```quiz
Q: Which of these states does not exist?
- n = 3, ℓ = 2, m = −2
- n = 1, ℓ = 0, m = 0
* n = 2, ℓ = 2, m = 0
- n = 4, ℓ = 3, m = 3
E: ℓ can be at most n − 1, so n = 2 allows only ℓ = 0 or 1.
```

```quiz
Q: How many nodes, radial and angular together, does any orbital with n = 4 have?
- 4
* 3
- It depends on m
E: Radial nodes n − ℓ − 1 plus angular nodes ℓ always add to n − 1 = 3.
```

## Summary

- n ≥ 1, 0 ≤ ℓ ≤ n − 1, −ℓ ≤ m ≤ ℓ; level n holds n² orbitals.
- Radial nodes: n − ℓ − 1; angular nodes: ℓ; always n − 1 in total.
- Real orbitals such as pₓ are combinations of the complex m = ±1 states.
