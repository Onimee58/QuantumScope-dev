---
title: Probability density and radial probability
area: hydrogen
kind: lecture
order: 3
objectives: Distinguish |ψ|² from the radial probability distribution | Find the most probable radius and the mean radius | Interpret clouds and enclosure surfaces
math: 01-complex-numbers, 06-probability
---
# Probability density and radial probability

## The idea

"Where is the electron?" has no single answer, only probabilities — and even those depend on how the question is asked. *Which small box is the electron most likely in?* and *at which distance from the nucleus is it most likely?* have different answers, and confusing them is the most common error with orbitals. This lecture separates the two and shows how pictures of orbitals choose what to display.

## Two different questions

$|\psi(\vec r)|^2$ is a **probability density**: the probability of finding the electron in a small volume $dV$ at $\vec r$ is $|\psi|^2 dV$. For 1s it is largest at the nucleus.

The **radial probability** asks instead how likely the electron is to be at distance $r$, in any direction. The thin shell at radius $r$ has volume $4\pi r^2 dr$, which grows with $r$, giving

$$P(r) = r^2 R_{n\ell}(r)^2$$

## Most probable and mean radius

For 1s, $P(r)$ peaks at exactly $r = a_\mu$ — the Bohr radius — although the density peaks at $r = 0$. The two answers differ because there is very little volume near the nucleus.

The mean distance is

$$\langle r\rangle = \frac{3n^2 - \ell(\ell+1)}{2}\,a_\mu$$

so $\langle r\rangle = 1.5\,a_\mu$ for 1s, $6\,a_\mu$ for 2s and $5\,a_\mu$ for 2p. The size grows roughly as $n^2$.

## Pictures of orbitals

An orbital has no sharp edge, so pictures choose what to show. QuantumScope's **enclosure surfaces** contain a chosen fraction of the probability (for example 90%); **clouds** shade the density. The "Fit to states" button in the Dynamics views uses the radius holding 99.5% of the probability — about $4.64\,a_\mu$ for 1s.

## Worked example

Compare 2s and 2p, which have the same energy. In units of $a_\mu$:

- **2p:** $P(r) \propto r^4 e^{-r}$, a single peak at $r = 4$; the mean is $\langle r\rangle = 5$.
- **2s:** $P(r) \propto r^2 (2 - r)^2 e^{-r}$. It is zero at the radial node $r = 2$, with a small inner peak at $r = 3 - \sqrt{5} \approx 0.76$ and a main peak at $3 + \sqrt{5} \approx 5.24$; the mean is $\langle r\rangle = 6$.

The 2s electron is on average farther out, yet its inner peak brings it closer to the nucleus more often than 2p. For 1s, a direct integral shows that only $1 - 5e^{-2} \approx 32\%$ of the probability lies inside one Bohr radius.

## Common mistakes

- **"The electron is most likely at the nucleus."** The density is largest there, but the radial probability is zero at $r = 0$: there is no volume there.
- **Treating the most probable radius as the mean.** For 1s they are $a_\mu$ and $1.5\,a_\mu$; the long tail pulls the mean outward.
- **Reading an enclosure surface as the atom's edge.** A 90% surface leaves 10% outside; at 99% it is noticeably larger.

## In the app

In the **Hydrogen Explorer**, the **Radial probability** chart plots $P(r) = r^2 R^2$ for the chosen state; compare 1s, 2s and 2p and find the peaks from the worked example. Switch **Representation** between *Density cloud* and *Probability enclosure*, and change **Enclosed probability** to see the surface grow.

[Try it: radial structure in the Hydrogen Explorer](qs:open/orbital)

## Check your understanding

```quiz
Q: Where is the 1s probability density |ψ|² largest?
* At the nucleus
- At r = a_μ
- At r = 1.5 a_μ
E: |ψ|² falls off as e^(−2r/a_μ) from r = 0; the peak at a_μ belongs to the radial probability r²R².
```

```quiz
Q: What is ⟨r⟩ for a 3d orbital?
- 9 a_μ
* 10.5 a_μ
- 13.5 a_μ
E: (3·9 − 2·3)/2 = (27 − 6)/2 = 10.5 a_μ.
```

```quiz
Q: Why is the radial probability P(r) zero at r = 0 even for 1s?
- Because ψ is zero at the nucleus
* Because the shell at radius r has volume 4πr²dr, which vanishes at r = 0
- Because the electron cannot enter the proton
E: For 1s, ψ is largest at the nucleus, but the factor r² in P(r) = r²R² makes the probability per distance zero there.
```

```quiz
Q: The enclosure surface is changed from 90% to 99%. What happens?
- Nothing: the orbital has a fixed edge
* The surface becomes larger
- The surface becomes smaller
E: Holding more of the probability needs a larger surface; orbitals have no sharp edge.
```

## Summary

- |ψ|² is a density per volume; P(r) = r²R² is the probability per distance.
- For 1s the most probable radius is a_μ but ⟨r⟩ = 1.5 a_μ; ⟨r⟩ = (3n² − ℓ(ℓ+1))a_μ/2.
- 2s has a radial node at 2 a_μ and two peaks; 2p has one peak at 4 a_μ.
- Clouds and enclosure surfaces are choices about how to show a distribution without an edge.
