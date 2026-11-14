---
title: "Lab: anneal fast and slow"
area: circuits
kind: lab
order: 110
objectives: Measure how the probability of success depends on the anneal time | Connect the minimum gap to the time an anneal needs | Digitize an anneal and see the Trotter error
---
# Lab: anneal fast and slow

You will anneal a MaxCut problem and a spin glass, and turn an anneal into a circuit. Read the lecture *Quantum annealing* first.

[Open Quantum annealing](qs:open/annealing)

```step
title: Anneal a hexagon slowly enough
text: Choose MaxCut: hexagon. Its answers are the alternating cuts 010101 and 101010, which cut all six edges. Press Anneal with T = 1, 3 and 10, noting the probability of the answer each time (about 7%, 26% and 73%). On Spectrum, read the minimum gap (about 0.69) and T* (about 6). Then choose a T long enough to find the answer at least 95% of the time.
check: anneal problem maxcut-ring6
check: anneal success >= 0.95
```

```step
title: Meet a tiny gap
text: Choose Spin glass with 8 spins, instance 0, and press Anneal. On Spectrum, find the marked minimum gap: about 0.002, near s = 0.45. Then press Success against T. The success rises, peaks near T = 15 at under 50%, then falls. Explain the fall with the lecture's section on avoided crossings, then try instances 1 and 2, whose gaps are much larger.
check: anneal problem glass-8-0
check: anneal gap <= 0.01
check: anneal curve glass-8-0
```

```step
title: Digitize the anneal
text: Go back to MaxCut: hexagon with T = 10. Set Steps to 5 and press Open as circuit: each slice lasts 2, too long, and ⟨O⟩ is only about −2.1. Return, set Steps to 20 and open the circuit again: ⟨O⟩ is about −5.5, as in the exact anneal. Measure: the two answers have about 74%.
check: qubits 6
check: observable
check: gates >= 400
check: expectation <= -5.4
```

```quiz
Q: The hexagon's Spectrum says it shows only the symmetric levels. Why may the others be ignored?
* Every term has two Z's, so the anneal never leaves the states (|x⟩ + |x̄⟩)/√2; the other levels can never be reached
- The other levels are always higher in energy
- They are ignored only to save time
E: Flipping every spin leaves H(s) and the starting state unchanged, so the state stays symmetric. Levels of the other kind may even cross the ground level without harm.
```

```quiz
Q: For the spin glass, why does a slower anneal do worse, and when does slowing down help again?
- Slower anneals collect more errors; slowing down never helps
* A slow anneal reaches the tiny gap entirely in the ground state and jumps it entirely; only anneals far longer than T* follow the ground state through
- The answer changes when the anneal is slower
E: The jump across a gap of 0.002 is almost certain at any practical speed. The adiabatic theorem still holds, but only once T is far beyond T*, here in the tens of thousands.
```

```quiz
Q: The circuit you opened has the shape of QAOA with 20 layers. What would QAOA with 2 layers do differently?
- Use a different problem Hamiltonian
* Choose the angles of its 2 layers with an optimizer instead of following the schedule
- Start from |0…0⟩ without H gates
E: QAOA and the digitized anneal share their structure; QAOA keeps few layers and optimizes the angles.
```
