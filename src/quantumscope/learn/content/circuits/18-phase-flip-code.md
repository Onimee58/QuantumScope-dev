---
title: "Error correction: the phase-flip code"
area: circuits
kind: lecture
order: 18
objectives: Protect a qubit against phase flips by changing basis | Explain why the bit-flip code fails against phase errors
math: 10-pauli-algebra
---
# Error correction: the phase-flip code

## The idea

The bit-flip code catches X errors but is blind to Z errors, which change phases rather than bits. A change of basis fixes this: in the $|\pm\rangle$ basis a phase flip looks exactly like a bit flip. The same three-qubit idea, wrapped in Hadamards, becomes a code for phase errors.

## A blind spot of the bit-flip code

A Z error on any data qubit of $\alpha|000\rangle + \beta|111\rangle$ gives $\alpha|000\rangle - \beta|111\rangle$: a logical phase flip. The syndrome is 00 — the bit-flip code cannot even see it. Worse, any of the three qubits can cause it, so the code makes phase errors *three times* as likely.

## Change the basis

Z flips $|+\rangle \leftrightarrow |-\rangle$ just as X flips $|0\rangle \leftrightarrow |1\rangle$. So encode in the $|\pm\rangle$ basis: after the two CX gates, apply H to all three qubits,

$$\alpha|0\rangle + \beta|1\rangle \;\rightarrow\; \alpha|{+}{+}{+}\rangle + \beta|{-}{-}{-}\rangle$$

To read the syndrome, apply H to the data qubits, measure the same parities as before, and apply H again. A Z error now shows up exactly like an X error did, and is corrected by a **Z** on the flagged qubit.

[Try it: the phase-flip code with an error on q2](qs:algorithm/phase_flip_code?logical=%2B&error=q2&p=0.1)

## One code per error type

| Code | Corrects | Blind to |
|---|---|---|
| Bit-flip | one X error | Z errors |
| Phase-flip | one Z error | X errors |

Real qubits suffer both — the Shor code combines the two.

[Try it: compare the codes in the Error-correction explorer](qs:open/qec)

## Worked example

Encode $\alpha|{+}{+}{+}\rangle + \beta|{-}{-}{-}\rangle$, and let a Z hit q2. Z swaps $|+\rangle$ and $|-\rangle$, so the state becomes $\alpha|{+}{+}{-}\rangle + \beta|{-}{-}{+}\rangle$.

To read the syndrome, H on the data turns this into $\alpha|001\rangle + \beta|110\rangle$. The parities are $q_0 \oplus q_1 = 0$ and $q_1 \oplus q_2 = 1$: syndrome 01, so the error is on q2. After the Hadamards are undone, a Z on q2 restores the code, again without learning $\alpha$ or $\beta$.

## Common mistakes

- **Correcting a phase error with X.** In this code the flagged qubit gets a Z.
- **Forgetting the Hadamards around the syndrome.** Without them the parity checks see nothing, as in the bit-flip code.
- **Expecting one repetition code to handle all noise.** Each is blind to the other error type.

## In the app

**Algorithms → Phase-flip code** builds the circuit with a chosen logical state and error. The **Error-correction explorer** compares both codes under each noise type, side by side with an unprotected qubit.

## Check your understanding

```quiz
Q: A Z error hits q1 of the bit-flip code α|000⟩ + β|111⟩. What does the syndrome show?
* 00: the error is invisible
- 11
- 10
E: Z leaves the parities unchanged; it only changes the relative sign, a logical phase error.
```

```quiz
Q: How does the phase-flip code correct the qubit it flags?
- With an X gate
* With a Z gate
- With a measurement
E: In the |±⟩ basis the error is a Z, so the correction is a Z on that qubit.
```

```quiz
Q: Which error is the phase-flip code blind to?
* An X error
- A Z error
- Both
E: X leaves |+⟩ alone and gives |−⟩ a minus sign, so an X on any qubit turns α|+++⟩ + β|−−−⟩ into α|+++⟩ − β|−−−⟩: a logical error with syndrome 00.
```

```quiz
Q: In the phase-flip code, what is the encoded |0⟩?
- |000⟩
* |+++⟩
- (|000⟩ + |111⟩)/√2
E: The two CX gates make |000⟩, and H on all three gives |+++⟩.
```

## Summary

- Z errors are invisible to the bit-flip code, which even multiplies them by three.
- Hadamards turn the bit-flip code into the phase-flip code, which corrects one Z error.
- Each repetition code handles one error type.
