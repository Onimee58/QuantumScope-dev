---
title: Measurement, information and no-cloning
area: principles
kind: lecture
order: 7
objectives: Explain what a measurement does to a quantum state | State and prove the no-cloning theorem | Connect no-cloning to teleportation and secure communication
math: 02-vectors-and-dirac-notation, 04-hermitian-and-unitary
---
# Measurement, information and no-cloning

## The idea

Classical information can be copied freely: photocopiers, backups, "save as". Quantum information cannot. A single unknown qubit cannot be duplicated, and measuring it gives away only one bit while destroying the rest. This limit sounds like a weakness, but it is exactly what makes quantum teleportation honest and quantum cryptography secure.

## Measurement changes what it measures

Measuring a qubit gives a classical result and leaves the qubit in the matching basis state. The information about the original amplitudes is lost: one measurement of $\alpha|0\rangle + \beta|1\rangle$ yields one bit, not $\alpha$ and $\beta$. To estimate them you need many identically prepared copies — which raises the question of whether copies can be made.

## The no-cloning theorem

No device can copy an unknown quantum state. Suppose a unitary $U$ did, for every state: $U|\psi\rangle|0\rangle = |\psi\rangle|\psi\rangle$. For two states $|\psi\rangle$ and $|\varphi\rangle$, inner products are preserved by $U$, so

$$\langle\psi|\varphi\rangle = \langle\psi|\varphi\rangle^2$$

which only holds if $\langle\psi|\varphi\rangle$ is 0 or 1: the states are identical or orthogonal. A copier can work for a set of mutually orthogonal states, such as $|0\rangle$ and $|1\rangle$ (a CX does it), but never for arbitrary states such as $|+\rangle$ as well.

## Consequences

- **No faster-than-light signalling.** If entangled states could be cloned, one could read out a partner's measurement choice instantly; no-cloning prevents it.
- **Teleportation moves, never copies.** Alice's original is destroyed by her measurement as Bob's appears.
- **Secure communication.** In quantum key distribution, an eavesdropper cannot copy the qubits in transit, and measuring them disturbs them detectably.

## Worked example

CX copies basis states: $|0\rangle|0\rangle \to |0\rangle|0\rangle$ and $|1\rangle|0\rangle \to |1\rangle|1\rangle$. Try it on $|+\rangle$:

$$\mathrm{CX}\,|+\rangle|0\rangle = \frac{|00\rangle + |11\rangle}{\sqrt{2}} \qquad \text{but} \qquad |+\rangle|+\rangle = \frac{|00\rangle + |01\rangle + |10\rangle + |11\rangle}{2}$$

The overlap of the two is $\frac{1}{\sqrt{2}} \cdot \frac{1}{2} \cdot 2 = \frac{1}{\sqrt{2}}$, so the "copy" has fidelity $1/2$ with the real thing. Instead of two copies we made a Bell pair. The proof's equation shows why no gate can do better for both $|0\rangle$ and $|+\rangle$: their overlap is $1/\sqrt{2}$, and $1/\sqrt{2} \neq 1/2$.

## Common mistakes

- **"Measure it, then rebuild it."** One measurement gives one bit, and the state collapses; there is nothing left to measure again.
- **"No-cloning forbids copying anything quantum."** Known states can be prepared as often as you like, and orthogonal sets can be copied. Only *unknown* states drawn from non-orthogonal sets cannot.
- **"Teleportation copies the state."** The original is gone after Alice's measurement; only one copy exists at any time.

## In the app

Build the worked example: H on q0, then CX. The State Inspector shows the Bell state, not $|+\rangle|+\rangle$, and each qubit's reduced state is maximally mixed. In the **Teleportation** experiment, watch Alice's qubit collapse at the moment Bob's correction makes his qubit match the original.

[Try it: CX "copies" |+⟩ into a Bell pair](qs:circuit?n=2&gates=H:0;CX:0,1&inspector=1)

[Try it: watch the original collapse in the Teleportation experiment](qs:open/teleportation)

## Check your understanding

```quiz
Q: Why does a CX not violate the no-cloning theorem when it copies |0⟩ and |1⟩?
* |0⟩ and |1⟩ are orthogonal; CX does not copy superpositions such as |+⟩
- CX is not unitary
- The theorem only applies to two qubits
E: CX on |+⟩|0⟩ gives a Bell state, not |+⟩|+⟩.
```

```quiz
Q: What does one measurement of a qubit reveal?
- Both amplitudes α and β
* One classical bit, and the state collapses
- Nothing
E: The result is 0 or 1; amplitudes can only be estimated from many copies, which cannot be made from one unknown state.
```

```quiz
Q: For which set of states could a single machine make perfect copies?
* {|+⟩, |−⟩}
- {|0⟩, |+⟩}
- Every single-qubit state
E: |+⟩ and |−⟩ are orthogonal, so a copier exists (H, then CX, then H on both qubits). |0⟩ and |+⟩ overlap, so no unitary copies both.
```

```quiz
Q: An eavesdropper intercepts qubits sent as |0⟩, |1⟩, |+⟩ or |−⟩. Why can't she copy them unnoticed?
- They are encrypted with a classical key
* The set is not orthogonal, so she must measure, and measuring in the wrong basis disturbs the qubits
- Qubits cannot travel through cables
E: This is the idea behind the BB84 protocol: disturbance shows up as errors that the two parties can detect.
```

## Summary

- Measurement yields one bit and collapses the state.
- No-cloning: unknown states cannot be copied; only mutually orthogonal sets can.
- CX on |+⟩ makes entanglement, not a copy (fidelity 1/2).
- No-cloning underlies teleportation's "move, not copy", no-signalling and quantum cryptography.
