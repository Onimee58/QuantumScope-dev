---
title: Entanglement and Bell states
area: principles
kind: lecture
order: 4
objectives: Describe the spin singlet and its correlations | State what a Bell inequality tests | Explain why entanglement cannot send signals
math: 07-tensor-products, 08-density-matrices-and-projectors
---
# Entanglement and Bell states

## The idea

Two particles can share a single quantum state that cannot be split into a state for each. Their results are then correlated more strongly than any pre-arranged plan could explain, even when the particles are far apart. This is **entanglement**: it is what Einstein called "spooky action at a distance", and what Bell showed can be tested.

## The singlet

Two spin-½ particles can share the **singlet** state

$$|\Psi^-\rangle = \frac{1}{\sqrt{2}}(|\uparrow\downarrow\rangle - |\downarrow\uparrow\rangle)$$

Measured along the same axis — any axis — the two always give opposite results. Each result on its own is completely random. No product of two single-particle states gives this: the singlet is **entangled**.

## Correlations at different angles

If the two spins are measured along directions at an angle $\alpha$ to each other, the average product of the results ($\pm 1$ each) is

$$E(\alpha) = -\cos\alpha$$

## Bell's inequality

Any theory where each particle carries pre-set answers ("local hidden variables") obeys the CHSH inequality, which combines four correlations with two axes for each side:

$$|E(a,b) + E(a,b') + E(a',b) - E(a',b')| \leq 2$$

For the singlet, quantum mechanics predicts up to $2\sqrt{2} \approx 2.83$ for suitable angles, and experiments agree. No pre-set answers can explain entanglement.

## No signalling

Measuring one particle does not change the other's statistics: on its own, each particle is maximally mixed whatever is done to its partner. The correlation only appears when the two lists of results are compared, which needs ordinary communication. Entanglement cannot send messages.

## Worked example

Take the singlet with Alice's axes $a = 0°$, $a' = 90°$ and Bob's axes $b = 45°$, $b' = -45°$. Each correlation is $-\cos$ of the angle between the two axes:

- $E(a,b) = -\cos 45° \approx -0.707$, and $E(a,b') = -\cos 45° \approx -0.707$
- $E(a',b) = -\cos 45° \approx -0.707$, but $E(a',b') = -\cos 135° \approx +0.707$

So $S = -0.707 - 0.707 - 0.707 - 0.707 \approx -2.83$, and $|S| = 2\sqrt{2}$, well above the classical limit 2. If only a fraction $v$ of the pairs are clean (the rest random), every correlation shrinks by $v$, and the violation survives only while $2.83\,v > 2$, that is $v > 0.71$.

## Common mistakes

- **"Measuring Alice's particle changes Bob's."** Bob's own results are 50:50 whatever Alice does. Only the comparison shows the correlation.
- **"Perfect correlation proves entanglement."** A classical mixture of $|00\rangle$ and $|11\rangle$ is also perfectly correlated along $z$. Entanglement shows when the axes are changed, as in the Bell test.
- **Forgetting the signs.** The CHSH combination has one minus sign; which term carries it depends on the convention, so use the same one throughout.

## In the app

In **Quantum Principles → Entanglement**, choose a **State**, aim **Alice axis** and **Bob axis**, and press **Send many** to watch the correlation table fill. **Run Bell test** measures the four CHSH settings and compares $|S|$ with 2. Lower **Clean pairs** to see the violation disappear near 71%, and pick the classically correlated state to see that it never exceeds 2.

[Try it: entangled electron spins](qs:open/entanglement)

[Try it: a Bell pair in the State Inspector](qs:circuit?n=2&gates=X:1;H:0;CX:0,1;Z:0&inspector=1)

## Check your understanding

```quiz
Q: For the singlet, both spins are measured along the same axis. What is the correlation E?
* −1: always opposite
- 0: uncorrelated
- +1: always equal
E: E(0°) = −cos 0 = −1.
```

```quiz
Q: What does a CHSH value of 2.7 tell you?
- The particles exchanged a signal
* No local hidden-variable model can explain the results
- The measurement was faulty
E: Local hidden variables obey |S| ≤ 2; quantum entanglement allows up to 2√2.
```

```quiz
Q: Alice measures her half of a singlet along x. What does Bob see if he only looks at his own results?
- Always "up"
- Always the opposite of a value he cannot know yet, so 0% "up"
* "Up" and "down" 50:50, exactly as before
E: Each particle alone is maximally mixed. Alice's choice changes nothing Bob can see on his own, so no message is sent.
```

```quiz
Q: The singlet is measured with axes 60° apart. What is the correlation?
- −1
* −0.5
- 0
- +0.5
E: E(α) = −cos α = −cos 60° = −0.5: the results are opposite three times out of four.
```

## Summary

- The singlet gives perfectly opposite results along any common axis.
- Correlations follow −cos α; the CHSH combination reaches 2√2, beyond the classical limit 2.
- Noise shrinks the correlations; below about 71% clean pairs the violation is gone.
- Entanglement creates correlations, not communication.
