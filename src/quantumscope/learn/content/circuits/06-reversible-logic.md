---
title: Reversible logic
area: circuits
kind: lecture
order: 6
objectives: Explain why quantum gates must be reversible | Compute AND, XOR and copies with Toffoli and CX gates | Use work qubits and uncompute them
math: 03-matrices-acting-on-states, 07-tensor-products
---
# Reversible logic

## The idea

Quantum gates can always be run backwards, but AND and OR cannot: their output does not say what the input was. To use ordinary logic inside a quantum algorithm — oracles, arithmetic — we rewrite it in a reversible form, keeping extra bits so that no information is lost, and cleaning up those bits afterwards.

## Why reversibility?

Quantum gates are unitary, so every gate can be undone. Ordinary logic is not like that: from the output of AND you cannot tell whether the input was 00, 01 or 10. To compute such functions on a quantum computer, we keep enough information to run the computation backwards.

## The basic building blocks

| Gate | Inputs → outputs | Classical meaning |
|---|---|---|
| X | a → NOT a | NOT |
| CX | (a, b) → (a, a ⊕ b) | XOR into b; copy a when b = 0 |
| CCX (Toffoli) | (a, b, c) → (a, b, c ⊕ ab) | AND into c when c = 0 |
| CSWAP (Fredkin) | (s, x, y) → swap x, y if s = 1 | a controlled multiplexer |

The Toffoli gate alone is **universal** for reversible logic: any classical function can be computed with Toffolis and extra bits set to 0 or 1.

## A half adder

Adding two bits gives a sum $a\oplus b$ and a carry $ab$:

1. Toffoli with controls a, b writes the carry into a fresh qubit.
2. CX from a to b turns b into the sum $a\oplus b$.

[Try it: the half adder example](qs:example/Half%20adder%20%28a%3D1%2Cb%3D1%29)

## Work qubits and uncomputing

Larger circuits need temporary **work qubits** (ancillas) for intermediate results. Leaving them with junk entangles them with the answer and spoils interference later, so good reversible circuits **uncompute** them: they repeat the steps that wrote the junk, in reverse order, returning the work qubits to $|0\rangle$. QuantumScope's 2-bit comparator does exactly this with q6.

[Try it: the comparator example](qs:example/2-bit%20comparator)

## Worked example

Follow the half adder on $a = 1$, $b = 1$, with a fresh carry qubit $c = 0$, written $|a\,b\,c\rangle$:

$$|1\,1\,0\rangle \overset{\mathrm{Toffoli}}{\longrightarrow} |1\,1\,1\rangle \overset{CX_{a\to b}}{\longrightarrow} |1\,0\,1\rangle$$

The middle qubit now holds the sum $1 \oplus 1 = 0$ and the last the carry $1 \cdot 1 = 1$: one plus one is binary 10. Run the two gates backwards (CX, then Toffoli) and you get $|1\,1\,0\rangle$ again — nothing was lost, because $a$ was kept.

## Common mistakes

- **Overwriting an input.** A reversible circuit keeps enough to recover the inputs; that is why the half adder keeps $a$.
- **Leaving junk on work qubits.** Junk stays entangled with the answer and destroys later interference; uncompute it.
- **Thinking a Toffoli computes AND by itself.** It XORs the AND into the target, so the target must start at 0.

## In the app

Open the **Half adder** example and step through it in the State Inspector; change the inputs with the initial states. The **Full adder** and **2-bit comparator** examples show larger circuits, and the comparator uncomputes its work qubit at the end.

## Check your understanding

```quiz
Q: A Toffoli gate acts on (a, b, c) = (1, 1, 1). What is the output?
- (1, 1, 1)
* (1, 1, 0)
- (0, 0, 1)
E: c becomes c ⊕ ab = 1 ⊕ 1 = 0; the controls are unchanged.
```

```quiz
Q: Why uncompute work qubits?
- To save memory
* So they are not left entangled with the result
- Because gates cannot be applied to them twice
E: Leftover junk entangles the work qubits with the answer, which destroys the interference algorithms rely on.
```

```quiz
Q: A Toffoli's target starts at 1 instead of 0, with both controls 1. What is the target afterwards?
* 0
- 1
- It depends on the phase
E: The Toffoli XORs the AND (1) into the target: 1 ⊕ 1 = 0. It computes AND only on a target that starts at 0.
```

```quiz
Q: Why must work qubits be returned to |0⟩ at the end of a quantum subroutine?
- To save memory
* Leftover junk is entangled with the result and spoils later interference
- Because measurements need |0⟩
E: Uncomputing removes the entanglement between the work qubits and the answer, so the answer can interfere cleanly.
```

## Summary

- Quantum gates are reversible, so classical logic must keep its inputs.
- CX computes XOR, the Toffoli computes AND, and the Fredkin is a controlled swap.
- Work qubits hold intermediate results and should be uncomputed back to |0⟩.
