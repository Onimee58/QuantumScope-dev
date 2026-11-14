---
title: "Lab: find states on the Bloch sphere"
area: principles
kind: lab
order: 90
objectives: Prepare states from their two angles | Predict measurement statistics along any axis | Find the axis along which a state gives a certain result
math: 01-complex-numbers, 06-probability
---
# Lab: find states on the Bloch sphere

You will prepare spin states by their angles θ and φ, measure many fresh copies along different axes, and check the Born rule $P(\uparrow) = (1 + \vec r\cdot\hat n)/2$ against the counts. Read *Superposition and the Bloch sphere* and *Measurement and the Born rule* first.

[Open the Superposition experiment](qs:open/superposition)

```step
title: An equal superposition, measured along z
text: Under Prepare, set θ = 90° and φ = 0°: the arrow lies on the equator along +x, the state |+⟩. Keep the Axis at 0° (along z), set the number of copies to at least 100 and press Measure many. About half the results should be +1.
hint: Axis 0° is the z direction; 90° is x. Measure many prepares a fresh copy for every measurement.
check: did superposition theta=90 phi=0 axis=0 copies>=100
```

```step
title: The same state, measured along x
text: Keep θ = 90°, φ = 0° and turn the Axis to 90°. Measure many again: now every result is +1, because the state points exactly along the measurement axis.
hint: P(↑) = (1 + r·n)/2 with r·n = 1.
check: did superposition theta=90 phi=0 axis=90 up>=0.99 copies>=100
```

```step
title: Check the Born rule at 60°
text: Prepare θ = 60°, φ = 0° and measure at least 500 copies along z (Axis 0°). The Born rule predicts P(↑) = (1 + cos 60°)/2 = 0.75; your fraction should be within a few percent.
hint: With 500 copies the typical spread is √(0.75 × 0.25 / 500) ≈ 0.02.
check: did superposition theta=60 axis=0 copies>=500 up=0.75±0.06
```

```step
title: Find the certain axis
text: Still with θ = 60°, φ = 0°, turn the Axis until Measure many gives +1 every time. Which angle is it, and why?
hint: The state is certain along the direction its arrow points.
check: did superposition theta=60 phi=0 axis=60 up>=0.99
```

## What you found

Each single result was random, but the fractions followed $(1 + \vec r\cdot\hat n)/2$. A state is never "undecided" in every direction: along its own axis it gives a certain result.

```quiz
Q: A state with θ = 120°, φ = 0° is measured along z. What fraction of +1 results do you expect?
- 0.75
* 0.25
- 0.5
E: P(↑) = (1 + cos 120°)/2 = (1 − 0.5)/2 = 0.25.
```

```quiz
Q: Along which axis does the state θ = 90°, φ = 0° give −1 with certainty?
- Along z
- Along +x
* Along −x (Axis −90°)
E: The state points along +x, so it is certainly "down" along the opposite direction.
```
