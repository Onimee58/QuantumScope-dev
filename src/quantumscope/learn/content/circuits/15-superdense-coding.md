---
title: Superdense coding
area: circuits
kind: lecture
order: 15
objectives: Send two classical bits by transmitting one qubit | Decode with a Bell measurement | Compare superdense coding with teleportation
math: 07-tensor-products, 10-pauli-algebra
---
# Superdense coding

## The idea

A single qubit, sent on its own, can carry at most one classical bit. But if sender and receiver already share an entangled pair, sending one qubit delivers **two** bits. Superdense coding shows that entanglement is a resource that can stand in for communication — the mirror image of teleportation.

## Two bits in one qubit

On its own, one qubit can carry at most one bit of classical information (the Holevo bound). With a shared Bell pair, Alice can send **two** bits by transmitting just her one qubit.

## Encoding

Alice and Bob share $|\Phi^+\rangle = \frac{1}{\sqrt{2}}(|00\rangle + |11\rangle)$, Alice holding q0. To send the bits $b_0 b_1$, she applies $X$ if $b_1 = 1$ and $Z$ if $b_0 = 1$ to her qubit:

| Message | Alice applies | Resulting Bell state |
|---|---|---|
| 00 | nothing | $\frac{1}{\sqrt{2}}(\vert 00\rangle + \vert 11\rangle)$ |
| 01 | X | $\frac{1}{\sqrt{2}}(\vert 10\rangle + \vert 01\rangle)$ |
| 10 | Z | $\frac{1}{\sqrt{2}}(\vert 00\rangle - \vert 11\rangle)$ |
| 11 | X, then Z | $\frac{1}{\sqrt{2}}(\vert 01\rangle - \vert 10\rangle)$ (up to a sign) |

The four results are the four Bell states, which are perfectly distinguishable.

## Decoding

Alice sends q0 to Bob. He applies CX from q0 to q1, then H to q0, and measures both: the result is exactly $b_0 b_1$.

[Try it: superdense coding](qs:example/Superdense%20coding)

## Teleportation in reverse

| Protocol | Uses | Sends |
|---|---|---|
| Teleportation | 1 Bell pair + 2 classical bits | 1 qubit state |
| Superdense coding | 1 Bell pair + 1 qubit | 2 classical bits |

Both show that shared entanglement is a resource that can be traded against communication.

## Worked example

Alice wants to send 11. Starting from $|\Phi^+\rangle$, she applies X to q0, then Z to q0:

$$\frac{|00\rangle + |11\rangle}{\sqrt{2}} \overset{X_0}{\longrightarrow} \frac{|10\rangle + |01\rangle}{\sqrt{2}} \overset{Z_0}{\longrightarrow} \frac{|01\rangle - |10\rangle}{\sqrt{2}}$$

Bob receives q0 and applies CX from q0 to q1: $|01\rangle$ stays, $|10\rangle$ becomes $|11\rangle$, giving $\frac{1}{\sqrt{2}}(|01\rangle - |11\rangle) = |-\rangle|1\rangle$. His H turns $|-\rangle$ into $|1\rangle$, and he measures $11$: the message, with certainty.

## Common mistakes

- **Thinking Alice sends two qubits.** Only q0 travels; q1 was shared with Bob beforehand.
- **Thinking the trick beats physics.** The Bell pair had to be distributed first; counting it, two qubits carry two bits.
- **Measuring before decoding.** Bob must apply CX and H first; measuring the Bell state directly gives random results.

## In the app

Open the **Superdense coding** example and change Alice's gates to send each of the four messages; the histogram shows the message every time. Step through with the State Inspector to see the four Bell states after encoding.

## Check your understanding

```quiz
Q: To send 10, what does Alice apply to her qubit?
- X
* Z
- X then Z
E: b0 = 1 means Z, and b1 = 0 means no X.
```

```quiz
Q: Can one qubit without shared entanglement carry two classical bits?
- Yes, using a superposition
* No: at most one bit (the Holevo bound)
E: Superdense coding needs the Bell pair; a lone qubit carries at most one bit.
```

```quiz
Q: Alice applies only X to her half of |Φ⁺⟩. Which two bits does Bob read?
- 00
* 01
- 10
- 11
E: X encodes b₁ = 1 and b₀ = 0, so Bob decodes 01.
```

```quiz
Q: Without a shared Bell pair, how many classical bits can one transmitted qubit carry?
* One
- Two
- Unlimited, since amplitudes are continuous
E: The Holevo bound limits one qubit to one bit; entanglement shared in advance doubles it.
```

## Summary

- With a shared Bell pair, transmitting one qubit sends two classical bits.
- Alice encodes with I, X, Z or XZ; Bob decodes with CX, H and two measurements.
- Superdense coding and teleportation are mirror images.
