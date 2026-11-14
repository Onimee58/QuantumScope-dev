---
title: Quantum teleportation
area: circuits
kind: lecture
order: 14
objectives: Follow the teleportation protocol step by step | Explain the four measurement results and their corrections | Explain why teleportation is neither faster than light nor cloning
math: 07-tensor-products, 10-pauli-algebra
---
# Quantum teleportation

## The idea

Teleportation moves an unknown qubit state from Alice to Bob without sending the qubit itself. It combines everything so far — entanglement, measurement and feed-forward — and shows the rules of quantum information at work: the state cannot be read, cannot be copied, and cannot outrun light.

## The task

Alice has a qubit in an unknown state $|\psi\rangle = \alpha|0\rangle + \beta|1\rangle$ and wants Bob, far away, to have it. She cannot measure $\alpha$ and $\beta$ — one measurement reveals one bit and destroys the state — and she cannot copy it. Teleportation moves the state using a shared Bell pair and **two classical bits**.

## The protocol

1. Alice (q1) and Bob (q2) share a Bell pair $|\Phi^+\rangle$.
2. Alice applies CX from q0 to q1, then H to q0.
3. Alice measures q0 into c0 and q1 into c1, and sends both bits to Bob.
4. Bob applies X if c1 = 1, then Z if c0 = 1.

Before the measurement, the three-qubit state can be rewritten as

$$\frac{1}{2}\sum_{a,b\,\in\,\{0,1\}} |a\,b\rangle\;X^{b}Z^{a}|\psi\rangle$$

so each of the four results $(a, b)$ leaves Bob with $|\psi\rangle$ rotated by a known Pauli operator, which his correction undoes:

| c0 c1 | Bob's qubit before correcting | Correction |
|---|---|---|
| 00 | $\vert \psi\rangle$ | none |
| 01 | $X\vert \psi\rangle$ | X |
| 10 | $Z\vert \psi\rangle$ | Z |
| 11 | $XZ\vert \psi\rangle$ | X then Z |

[Try it: the Teleportation experiment](qs:open/teleportation)

[Try it: teleportation as a circuit](qs:example/Quantum%20teleportation)

## No faster-than-light signalling

All four results are equally likely, whatever $|\psi\rangle$ is. Until Bob receives the two bits, his qubit is the average of the four rotated states — the maximally mixed state $I/2$ — and carries no information at all. The bits travel at most at the speed of light, so nothing is transmitted faster.

## No cloning

Alice's measurement collapses q0 to $|a\rangle$: her copy is destroyed as Bob's appears. Teleportation moves a state; it never duplicates one, consistent with the no-cloning theorem.

## Worked example

Teleport $|\psi\rangle = 0.6|0\rangle + 0.8|1\rangle$, and suppose Alice measures $c_0 c_1 = 11$. Bob's qubit is then

$$XZ|\psi\rangle = X(0.6|0\rangle - 0.8|1\rangle) = -0.8|0\rangle + 0.6|1\rangle$$

Bob applies X, giving $0.6|0\rangle - 0.8|1\rangle$, then Z, giving $0.6|0\rangle + 0.8|1\rangle = |\psi\rangle$. Had he applied Z first, he would have got $-|\psi\rangle$ — the same state, since a global phase is unobservable, so the order does not matter here. Without the two bits he cannot know which of the four corrections to apply.

## Common mistakes

- **Thinking teleportation sends the qubit or its amplitudes.** Only two classical bits travel; the amplitudes are never known to anyone.
- **Forgetting the corrections.** Without them Bob's qubit is the right state only in one case out of four.
- **Thinking Bob's qubit changes when Alice measures.** On its own it stays maximally mixed until the bits arrive.

## In the app

The **Teleportation** experiment walks through the protocol step by step with Bloch spheres for Alice and Bob; choose the state to send and watch Alice's qubit collapse as Bob's takes on the state. The **Quantum teleportation** example builds the same protocol as a circuit with mid-circuit measurements and conditional gates.

## Check your understanding

```quiz
Q: Alice's measurement gives c0c1 = 01. What must Bob do?
- Nothing
* Apply X
- Apply Z
- Apply X then Z
E: Result 01 leaves Bob with X|ψ⟩, so X restores |ψ⟩.
```

```quiz
Q: Why can't Bob learn anything before the bits arrive?
* All four results are equally likely, so his qubit is the maximally mixed state I/2
- Because his qubit is still |0⟩
- Because Alice's measurement has not happened yet
E: Averaged over the four equally likely results, Bob's qubit is I/2 for every input state.
```

```quiz
Q: Alice's results are c0 = 1, c1 = 0. What must Bob do?
* Apply Z
- Apply X
- Nothing
- Apply X then Z
E: Result 10 leaves Bob with Z|ψ⟩, which Z undoes.
```

```quiz
Q: How many classical bits must Alice send per teleported qubit?
- One
* Two
- As many as the amplitudes need
E: Two bits pick one of the four Pauli corrections; no more information is needed or sent.
```

## Summary

- One Bell pair plus two classical bits teleports one qubit state.
- Each of the four results needs its own Pauli correction.
- No signal travels faster than light, and the original is destroyed: no cloning.
