<div align="center">
  <img src="src/quantumscope/assets/quantumscope-128.png" alt="QuantumScope logo" width="96">

  # QuantumScope

  **Explore quantum mechanics. Build quantum circuits. Visualize quantum states.**

  A cross-platform quantum visualization and circuit simulation studio built with Python and PySide6.

  [![Version](https://img.shields.io/badge/version-v1.0.0-1878b9)](https://github.com/Onimee58/QuantumScope/releases)
  [![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
  [![Platforms](https://img.shields.io/badge/platforms-Linux%20%7C%20Windows%20%7C%20macOS-555)](https://github.com/Onimee58/QuantumScope/releases)

  **[Download releases](https://github.com/Onimee58/QuantumScope/releases)** · **[Features](#what-you-can-explore)** · **[Getting started](#getting-started)** · **[Contributing](CONTRIBUTING.md)** · **[Report an issue](https://github.com/Onimee58/QuantumScope/issues)**
</div>

---

## What is QuantumScope?

QuantumScope is a desktop application for exploring quantum phenomena *and* building quantum circuits in one environment. It connects wavefunctions, probability distributions, superposition and entanglement to gate-based quantum computation through interactive visualizations and an editable statevector circuit simulator.

Use it for self-study, classroom demonstrations, coursework or experimenting with small ideal quantum circuits. No programming is required to use the graphical interface.

## What you can explore

| Workspace | Experiments and tools |
|---|---|
| **Hydrogen** | Hydrogen Orbital Explorer; coherent-state Hydrogen Dynamics in 2D and 3D; probability density, amplitude and phase visualization; available image/data exports |
| **Quantum Principles** | Double-Slit Experiment; interactive quantum superposition and Bloch sphere; quantum entanglement demonstrations |
| **Quantum Circuits** | Drag-and-drop circuit editor, statevector simulation, simulation stepping, Bloch spheres for every qubit, measurements, example circuits, verification, QASM Converter and PDF export |
| **Quantum ML** | Datasets (nine built-in, offline, plus your own CSV or .npz) with a checker and visible preprocessing; Quantum Kernel Classifier (angle and ZZ feature maps, bandwidth, shot noise, SVM or kernel ridge, two classes or all of them, decision regions); Variational Classifier (live training, two classes or all of them, open the trained circuit in the simulator) |

### Quantum circuit studio

- **Up to 10 simulated qubits**, with a dynamically expanding operation-column layout.
- **Drag-and-drop gate placement** and movement of existing gates; multi-qubit placement with guided operand selection and temporary anchors.
- **Edit parameters after placing gates** using the gate's dedicated parameter dialog. Expressions such as `pi/2` and `-pi/4` are supported.
- **Undo/Redo**, column insertion and removal, canvas panning, Ctrl+wheel zoom, Fit Circuit and Reset Zoom.
- **Step-by-step statevector inspection**, theoretical output probabilities, measurement sampling and Bloch sphere views.
- **Terminal measurement (`M`) gates**: measured-qubit outcomes are distinguished from diagnostic sampling of the complete state.
- **Circuit verification** and example circuits, including Bell/GHZ and reversible logic/arithmetic demonstrations.
- **Save/open `.qscope` circuits**, import/export supported **OpenQASM 2** instructions, and **export circuit diagrams to PDF**.
- **Quantum Gate Explorer**: double-click a gate in the *left palette* for its definition, circuit symbol, matrix/operation and basic state transformations. Double-clicking a placed parameterized gate opens its parameter editor instead.

**Supported operations:** `H`, `X`, `Y`, `Z`, `S`, `T`, `Sdg`, `Tdg`, `SX`, `RX`, `RY`, `RZ`, `U`/`U3`, `P`, `CX`, `CZ`, `SWAP`, `CCX`, `CSWAP`, and terminal `M`.

## System requirements

**Systems:** Windows 10 (version 1809 or later) or Windows 11, 64-bit; macOS 14.4 or later on Apple Silicon; Ubuntu 24.04 or Debian 13 or later, 64-bit.

| | Minimum | Recommended | Best |
|---|---|---|---|
| **Processor** | 64-bit, 2 cores | 4 cores | 6 or more cores |
| **Memory (RAM)** | 4 GB | 8 GB | 16 GB |
| **Graphics** | OpenGL 3.2 (most integrated graphics since 2015) | Recent integrated graphics (Intel Iris Xe, AMD Radeon, Apple M1) | A dedicated graphics card (NVIDIA or AMD) |
| **Disk space** | 1.5 GB free | 2 GB free | 2 GB free (SSD) |
| **Screen** | 1280 × 720 | 1920 × 1080 | 1920 × 1080 or larger |
| **What runs well** | 3-D orbitals up to 96 points per axis; circuits up to 10 qubits; Quantum ML up to a few hundred samples | Everything, including the comparison 3-D view and larger datasets | The finest 3-D grids (160 points per axis) with both viewers, and the largest models, smoothly |

## What's new in v1.0.0?

**The first release for the classroom.** QuantumScope now opens with a license file, given by your instructor: it is asked for once, checked offline, and shown in About. QuantumScope is no longer open source; its terms of use will be announced.

## What's new in v0.9.19?

**See your data before you import it.** A CSV opens in a preview where you scroll through it, choose the label column and leave out columns such as IDs.

## What's new in v0.9.18?

**Graphs in their own windows, search and dots.** Any graph of the Quantum ML experiments and annealing opens in its own window, a search box finds experiments by name or topic, and a dot marks a tab with something new; the double-slit drawing's words no longer stretch.

## What's new in v0.9.17?

**Easier on small screens.** The window fits laptop screens, number boxes have clear arrows, side panels have an easy-to-find fold button and groups that fold, and long runs such as a grid search say when they have finished.

## What's new in v0.9.16?

**Run your circuit on real quantum hardware.** File → Run on IBM Quantum hardware… writes ready-to-paste Python for your circuit: try it on your computer with a real device's simulated noise, then run it on an IBM quantum computer with your own account. QuantumScope never sees your API key.

## What's new in v0.9.15?

**A more flexible window.** Side panels fold to a named strip, any tab can open in its own window of any size and shape, the variational classifier gains gradient descent with a learning rate, and the palettes no longer clip their names with larger fonts.

## What's new in v0.9.14?

**Readable PDFs of long circuits.** Export PDF… now draws a long circuit in readable parts across pages, instead of shrinking it to one line.

## What's new in v0.9.13?

**Choosing features by annealing.** Quantum annealing can now choose which features of a dataset to keep, your own CSV included: the answer predicts the classes well without features that repeat each other. Compare it with greedy selection and PCA, then use it in the classifiers. A new lecture and lab explain how it works, and what annealing does and does not add.

## What's new in v0.9.12?

**Linux start-up fix.** 0.9.11 closed right after starting on Wayland desktops (Ubuntu's default); 0.9.12 starts normally.

## What's new in v0.9.11?

**A lighter 3-D engine.** The Hydrogen and Quantum ML 3-D views now draw with OpenGL through pyqtgraph instead of VTK. They look and work as before (clouds, enclosures, phase colours, cameras, comparison view, image and GIF export), and the installed app is under half its size of two versions ago (on Linux, about 350 MB instead of 785 MB).

## What's new in v0.9.10?

**Faster and smaller.** Changing only how an orbital is shown (representation, opacity, camera) no longer recomputes it, and retraining a quantum kernel classifier with a different C or λ, or searching settings, reuses kernel matrices it has already computed; both are forgotten automatically when memory runs short. The installers leave out parts of Qt that QuantumScope never uses and, on Linux and macOS, the libraries' debugging data: the installed app is about a fifth smaller.

## What's new in v0.9.9?

**Labs in every area.** Fifteen new labs bring hands-on practice to Quantum Principles (the Bloch sphere, interference, a Bell test, hidden phases, pure versus mixed states), Hydrogen (orbitals, radial probability, quantum beats, spectral lines) and Mathematics (six calculator labs, from complex numbers to the parameter-shift rule). Their steps tick as you work in the experiments and the calculator.

## What's new in v0.9.8?

**A fuller course.** Every one of the 62 lectures now follows the same shape — the idea, the main content, a worked example with numbers, common mistakes, what to try in the app, four questions and a summary — and each of the five areas opens with a study guide: who it is for, how long it takes, what to read first, the suggested path through lectures and labs, and what you should be able to do at the end.

## What's new in v0.9.7?

**Protected code.** The installers now carry QuantumScope's own code compiled to native machine code instead of Python bytecode, which free tools can turn back into readable source. Nothing changes in how the app looks or works.

## What's new in v0.9.6?

**Lighter, and watching its own use.**

- **Installers about 20% smaller:** only the parts of VTK (the 3-D library) that QuantumScope uses are bundled.
- **A resource meter** in the status bar shows QuantumScope's memory, how full the computer's memory is, and how busy the processor is. It warns when memory is nearly full, and asks before a very fine 3-D grid or a large kernel that may not fit.
- **System requirements** (minimum, recommended, best) are stated here, in the guide and on the releases page.
- **Check boxes** are now clearly visible in the dark theme (and the light one).

## What's new in v0.9.5?

**Report a problem, and news.**

- **⚑ Report a problem** shows the whole report (your description, version, system and tab; nothing personal) and fills in an email or a GitHub issue for you to send. QuantumScope sends nothing itself.
- **Unexpected errors** no longer pass silently: QuantumScope keeps running and offers to report them, with the details filled in.
- **News:** with your permission, QuantumScope reads one public file once a week and shows announcements of new courses, workshops and features in a bar under the header, one at a time.

## What's new in v0.9.4?

**One circuit, many classes.**

- **The Variational Classifier separates any number of classes:** it measures ⌈log₂ k⌉ qubits and each outcome names a class (4 qubits for ten digits), trained by cross-entropy with exact gradients.
- **Everything follows:** decision regions, many-class evaluation and cross-validation, saved models, and **Open in circuit simulator** with the readout qubits measured.
- **Lessons:** the lecture "More than two classes" and its lab cover the circuit approach.

## What's new in v0.9.3?

**More than two classes, and four more datasets.**

- **The Quantum Kernel Classifier separates all classes at once** (one-vs-rest, sharing one kernel matrix): all ten MNIST digits, three penguin species, six kinds of glass.
- **Evaluation for many classes:** a k × k confusion matrix, macro-averaged precision, recall and F1, balanced accuracy, and a ROC curve per class. Saved models, the 3-D view and predictions on new files handle many classes too.
- **Four new built-in datasets,** with their licences: a Fashion-MNIST subset, Palmer Penguins, Seeds and Glass Identification.
- **A new lecture and lab** on multi-class classification, and two glossary terms.

## What's new in v0.9.2?

**Quantum annealing.**

- **A Quantum annealing experiment** in the Quantum Circuits area: MaxCut, spin glasses, number partitioning or your own Ising problem, annealed exactly.
- **See why the anneal time matters:** the spectrum with its minimum gap and the adiabatic time scale, the state during the anneal, and the probability of success against the anneal time.
- **Open the anneal as a circuit** (digitized annealing) in the simulator, and compare it with QAOA.
- **A new lecture and lab** on quantum annealing, and six glossary terms.

## What's new in v0.9.1?

**More optimizers, and optimizing with shots.**

- **Five new optimizers** for parameterized circuits: Adam, SPSA, Rotosolve, the quantum natural gradient and simulated annealing, beside BFGS, gradient descent, COBYLA and Nelder–Mead.
- **Optimize with shots:** the optimizer sees noisy measured energies, as on real hardware, and the chart compares them with the true energy.
- **A new lecture** on optimizing with shots, and five glossary terms.

## What's new in v0.9.0?

**The Math tab: a quantum calculator.**

- **Quantum mathematics in Dirac notation:** kets, bras, ⊗, †, gates and your own matrices, with eigenvalues, partial traces, entropy, Bloch vectors, Pauli decompositions and more.
- **Exact or in digits:** exact answers keep √2, i, π and symbols such as θ; digits mode computes numbers.
- **See the working:** every step, the matrix, and a Bloch sphere for single-qubit states; send a state to the circuit simulator.
- **Try it from the lessons:** every Mathematics lesson opens the calculator with its example.

## What's new in v0.8.5?

- **The user guide's text is readable again** (it printed pale grey on white in v0.8.2 to v0.8.4), and its cover now shows a quantum circuit and a Bloch sphere.

## What's new in v0.8.4?

- **The start-up logo now shows on Linux and macOS** too, not only on Windows.
- **The user guide has a new cover.**

## What's new in v0.8.3?

**Evaluating and tuning the Quantum ML classifiers.**

- **Evaluation:** test-set metrics (accuracy, precision, recall, F1, AUC and more), the confusion matrix and the ROC curve, plus k-fold cross-validation, in both classifiers.
- **Hyperparameter search:** cross-validate many kernel settings in seconds, see them ranked, and apply the best with one click.
- **Training controls** for the variational classifier: the loss, learning rate, mini-batches, a validation split with its own curves, and early stopping.
- **A new lesson** on evaluating classifiers, and seven glossary terms.

## What's new in v0.8.2?

**Saving models, seeing kernels, and a 3-D decision view.**

- **Save, load and use trained models:** a small, safe file holds the classifier and its preprocessing; **Predict on a file…** classifies new CSV or `.npz` data and exports the results.
- **See the kernel:** a kernel map (the data as the kernel sees it), an interactive kernel matrix, and a sample viewer that shows the images for Digits and MNIST.
- **A 3-D decision view:** rotate the decision boundary, the SVM's margins and the support vectors, and save an image or a rotating GIF.
- **Fixes:** the updater no longer freezes and retries GitHub's temporary errors, and the Quantum ML controls scroll instead of squashing.

## What's new in v0.8.1?

**Speed, and no more frozen windows.**

- **The circuit optimizer is about 20 times faster:** **Optimize** on the 6-qubit QAOA example takes 0.6 s instead of 13 s, and **Best of 3** 1.4 s instead of 40. It uses exact adjoint gradients and a vectorized simulator, and finds the same results.
- **The variational classifier** trains up to 15 times faster, and **the SVM** 35–55 times faster.
- **Long computations run in the background,** with progress, **Stop** and **Cancel**, so the window never freezes.
- **Right-click any chart** to save it as an image, copy it, or save its data as CSV.

## What's new in v0.8.0?

**Quantum machine learning, a linear solver, and an upgraded user guide.**

- **A fourth area, Quantum ML,** with three experiments:
  - **Datasets:** Iris, Wine, Breast Cancer, Digits and an MNIST subset, all offline, or your own CSV or .npz file. A checker says what stands in the way and suggests each fix, and the preprocessing (classes, PCA, scaling, subsampling, missing values, text columns) stays visible and adjustable.
  - **Quantum Kernel Classifier:** angle or ZZ feature maps, a bandwidth, kernels estimated from shots, an SVM or kernel ridge, a kernel heatmap, and decision regions for any number of features.
  - **Variational Classifier:** a trainable circuit, trained live with exact parameter-shift gradients; open the trained circuit in the simulator.
- **VQLS** in **Algorithms**: solve A x = b with a variational circuit, on preset systems or your own, with a live view of the solution.
- **Lessons:** five Quantum ML lectures and three labs whose steps tick as you run the experiments, a VQLS lecture and lab, and 14 new glossary terms (105 in total).
- **The user guide** (21 pages) now has a title page, a table of contents with page numbers, bookmarks, numbered figures with a list of figures, chapters on Quantum ML and VQLS, and 41 references, each checked against its source.

## What's new in v0.7.8?

**A user guide:** a 13-page PDF with screenshots, covering installing and updating, every area and experiment, the circuit simulator, Learn, Settings, troubleshooting, and a mouse and keyboard reference.
- **Open it** from **ⓘ → User guide**. It is also attached to every release.
- **Its source** is `docs/user-guide.md`. Authors rebuild the screenshots and the PDF with `python tools/make_user_guide.py`, which photographs the real app.

## What's new in v0.7.7?

**Learn → Mathematics:** 12 lessons on the math behind everything else, assuming only high-school algebra and trigonometry:
- complex numbers and Dirac notation;
- matrices, Hermitian and unitary matrices, eigenvalues;
- probability and shot noise;
- tensor products, density matrices and the partial trace;
- matrix exponentials, Pauli algebra, the Fourier transform;
- gradients.

**"Math you need":** every physics lecture now says which of them it builds on, with links. The glossary gains ten mathematics terms.

## What's new in v0.7.6?

**Teleportation, redesigned:**

- **Follow the protocol on three Bloch spheres,** with the circuit above highlighting each step. Play it or step through it.
- **Watch Alice's two bits travel** to Bob before he corrects his qubit.
- **Try a noisy pair, or skip Bob's correction,** and measure the average fidelity of many teleports against the classical limit of ⅔.

## What's new in v0.7.5?

**Entanglement, redesigned:**

- **Pairs fly to Alice and Bob,** and each qubit's own Bloch sphere shows that, alone, it is completely random.
- **Aim the detectors** by dragging their axes.
- **Watch the correlations build up** in a grid and on a curve.
- **Run a Bell test:** the meter shows entangled pairs beating the classical limit of 2. Try noisy pairs, or a classically correlated pair, which never can.
- **Every Bloch sphere now turns:** right-drag, or Shift + left-drag. Double-click resets the view.

## What's new in v0.7.4?

**Quantum Principles, redesigned (part 1):**

- **Superposition:**
  - **drag the arrow** on a shaded Bloch sphere, or pick a preset;
  - turn the amber measurement axis;
  - **Measure once** to watch the state collapse;
  - **Measure many** to watch the counts grow toward the Born-rule targets.
- **Double-Slit:**
  - particles land **one by one** as glowing dots, and the fringes build up before your eyes;
  - the wavelength sets the **colour of the light**;
  - **drag the slits** to change their separation.

Entanglement and Teleportation follow in v0.7.5.

## What's new in v0.7.3?

- **A glossary in Learn:** **81 terms**, such as *Hermitian*, *Hamiltonian*, *eigenvalue* and *density matrix*, are underlined where they first appear in a lesson.
  - Click one for a short definition, related terms, and **Learn more**, which opens the lesson that teaches it.
  - Every term is also listed on the new **Glossary** page.
  - PDF handouts end with the terms they use.
- **A start-up splash:** QuantumScope's Q, on a transparent background, appears while the app loads.

## What's new in v0.7.2?

- **Learn's PDF export** prints at a readable size: 11-pt text, with the headings above it. The body text used to come out microscopic.
- **The circuit sidebar:** the Noise buttons no longer drift down on tall pages.
- **Updating on Ubuntu:** QuantumScope now waits for the installer and offers **Restart now**.

## What's new in v0.7.1?

Improvements suggested by a tester:

- **A compact circuit tab:**
  - the sidebar holds the gates (6 per row), **Shots** and the **verification table**, beside the results;
  - the canvas height fits the qubits;
  - there's no sideways scrolling.
- **Parameters:** **Randomize all**, **🎲** per parameter, **Best of N random starts**, and two columns of sliders on wide windows.
- **Every tab can close.** Closed tabs come back as you left them, and an empty area shows what you can open.
- **Fixes:**
  - the Error-correction explorer opens in Quantum Circuits;
  - keyboard selection no longer highlights rows of the circuit canvas.

## What's new in v0.7.0?

- **Parameterized circuits:**
  - type a parameter name as a gate angle (Greek letters as in LaTeX: `\theta` → θ), and share it among gates with factors such as `2*\gamma`;
  - move the sliders and watch an **observable**'s expectation value ⟨O⟩, next to its exact minimum.
- **Optimize:** BFGS and gradient descent with exact **parameter-shift** gradients, plus COBYLA and Nelder–Mead, with a live convergence plot and **energy landscapes**.
- **VQE:** the ground-state energy of the **H₂ molecule** and of Ising and Heisenberg spin chains, checked against exact diagonalization.
- **QAOA for MaxCut:** five graphs, with a live graph view of the likeliest cut and the probability of each cut size.
- **Updates:** **ⓘ About → Check for updates…**. It asks first, makes one request to GitHub, verifies a checksum, and installs after you confirm. From this version on, QuantumScope can update itself.
- **Learn:** 6 new lectures and 4 labs on observables, parameters, the parameter-shift rule, VQE, optimizers and QAOA.

See [VARIATIONAL.md](VARIATIONAL.md) and [CHANGELOG.md](CHANGELOG.md).

## What's new in v0.6.2?

- **Quantum error correction:**
  - the **bit-flip** and **phase-flip codes** (syndromes measured mid-circuit and corrected with two-bit conditions), and the **9-qubit Shor code**;
  - each with checks for every single error.
- **Logical error rates:**
  - **Plot logical error rate** sweeps your circuit's noise and compares it with an unprotected qubit;
  - the new **Error-correction explorer** shows which code helps against which noise.
- **Quantum phase estimation** in the Algorithms menu, with exact and inexact phases.
- **Conditions on several classical bits:** "Run only if c0c1 = 10".
- **Example titles and qubit labels:**
  - examples show a title bar with **Change parameters…** and **Learn more**;
  - you can label the qubits of any circuit (data, syndrome, Alice…).
- **Learn:** 5 new lectures and 3 labs on error correction and phase estimation.

See [ERROR_CORRECTION.md](ERROR_CORRECTION.md) and [CHANGELOG.md](CHANGELOG.md).

## What's new in v0.6.1?

- **Mid-circuit measurement and feed-forward:**
  - **M→c** measures a qubit anywhere and stores the result in a classical bit;
  - any gate can be set to **run only if** a bit is 0 or 1;
  - **Reset** returns a qubit to |0⟩.
- **Exact branches:** every measurement outcome is followed exactly, and the State Inspector's new **Branches** tab shows each outcome's probability and state.
- **Teleportation and superdense coding:**
  - both are new examples, with checks that test your circuit on many inputs;
  - a new **Quantum Teleportation** experiment in Quantum Principles tells the story with Alice, Bob and a classical channel.
- **OpenQASM 2:** mid-circuit measurement, `if` conditions and `reset` are exported and imported.
- **Learn:**
  - 6 new lectures (mid-circuit measurement, feed-forward, teleportation, superdense coding, deferred measurement, no-cloning) and 5 new labs;
  - quizzes now check your answer as you click;
  - lab steps tick off live.
- **Windows dark mode:** the category tabs and drop-down lists are now themed correctly.

See [MEASUREMENT.md](MEASUREMENT.md) and [CHANGELOG.md](CHANGELOG.md).

## What's new in v0.6.0?

- **Noise and mixed states:** circuits can now be simulated with noise, using a density matrix.
  - **Noise button:** global noise on every gate, with presets, separate error rates, idle noise and readout error.
  - **Noise palette:** bit flip, phase flip, depolarizing, amplitude damping and phase damping channels to place on any wire.
  - **Noise Explorer:** double-click a channel for its equations, Kraus operators, effect on the Bloch sphere, and live numbers.
- **Results under noise:** Bloch arrows shrink as qubits lose purity, every step shows purity and fidelity with the ideal state, and shots include readout error.
- **The State Inspector** shows the density matrix. Algorithm checks report the success probability under noise.
- **Learn:** new lectures *Density matrices and mixed states* and *Noise and decoherence*, and the lab *Watch a Bell pair decohere*.
- **Palette:** gates in a compact 3-column grid.

See [NOISE.md](NOISE.md) and [CHANGELOG.md](CHANGELOG.md).

## What's new in v0.5.2?

- **Learn:** a 📖 Learn button in every area opens 21 lectures and 6 guided labs, covering Quantum Circuits, Quantum Principles and Hydrogen.
  - **Lectures** have rendered equations, ▶ Try it links that set up the experiment, and questions with answers.
  - **Labs** tick off each step as your circuit reaches it.
  - **Teachers** can add their own Markdown lessons under My course (see [LEARN.md](LEARN.md)).
- **A new Settings window:**
  - theme (including Follow system) and interface size;
  - graphics device (NVIDIA on Linux);
  - gate angle units, bit order (textbook or Qiskit) and exact or decimal amplitudes;
  - default folder, autosave with crash recovery, and Restore defaults.
- **Circuit tab:**
  - starts empty, with a File menu and a tidier toolbar;
  - **Tools → Simplify** removes redundant gates, verified against the unitary;
  - **Check equivalence** compares two circuits.

See [CHANGELOG.md](CHANGELOG.md).

## What's new in v0.5.1?

- **Algorithms menu:** Deutsch, Deutsch–Jozsa, Bernstein–Vazirani, Grover search and the quantum Fourier transform. Each is checked against its specification as you edit.
- **Expandable blocks:** oracles and subroutines appear as labeled boxes. Double-click one to see its real gates inside a light outline; Collapse, Edit block… and Ungroup are on the right-click menu.
- **New reversible-logic examples:** full adder, comparator, controlled increment, AND and multiplexer, each with a truth-table check.
- **The CP (controlled phase) gate**, plus a Worked identity tab and a Try it button in the Gate Explorer.

See the [Algorithms guide](ALGORITHMS.md) and [CHANGELOG.md](CHANGELOG.md).

## What's new in v0.5.0?

- **Choose each qubit's initial state:** |0⟩, |1⟩, |+⟩, |−⟩, |+i⟩, |−i⟩ or any custom (θ, φ) state, by clicking the wire label.
- **State Inspector window:**
  - exact amplitudes and phases;
  - the statevector in Dirac notation, with LaTeX and CSV export;
  - reduced density matrices with purity and entanglement entropy;
  - circuit statistics such as T-count, Clifford counts and minimum depth.
- **Better Hydrogen Dynamics views:**
  - a working 3D Reset camera, plus Top, Front and Side views;
  - quick Max and preset buttons for parameters;
  - Fit to states;
  - a 2D contrast option that reveals weak lobes.

See the [State Inspector guide](STATE_INSPECTOR.md) and [CHANGELOG.md](CHANGELOG.md).

## What's new in v0.4.3?

An internal maintenance release: the circuit editor's rules now live in a tested, Qt-free model, preparing for the v0.5 education features. The app looks and works the same, with a few small editing fixes. See [CHANGELOG.md](CHANGELOG.md).

## What's new in v0.4.2?

- **Readable Light Mode circuits:** gates, control dots, targets and results now use theme-aware colors that meet WCAG 2.1 AA contrast.
- **Richer Gate Explorer:** full matrices (including multi-qubit gates), exact amplitudes, properties such as inverse, Clifford membership and eigenvalues, related gates, and angle fields that accept expressions like `pi/2`.
- **More reliable releases:** every packaged app is launch-tested in CI on Linux, Windows and macOS.
- Shell scripts work right after cloning, with no `chmod` needed.

See [CHANGELOG.md](CHANGELOG.md) for details.

## What's new in v0.4.1?

A maintenance release focused on circuit-file integrity:

- `.qscope` files now keep the circuit's column layout (parallel gates and intentional spacing) across save and reopen, while staying readable by v0.4.0.
- QASM import packs simultaneous gates into shared columns, and `barrier` statements are reported instead of silently ignored.
- Safer, bounded parsing of QASM gate angles.
- Arithmetic example circuits keep checking their specification after you edit them, so broken edits show FAIL rows.

See [CHANGELOG.md](CHANGELOG.md) for details.

## What's new in v0.4.0?

QuantumScope v0.4.0 builds on the v0.3.0 circuit studio with:

- **Post-placement gate parameter editing** and mathematical angle expressions.
- **PDF circuit export**, including an optional simulation summary.
- **Gate Explorer** reference dialogs launched from the gate palette.
- **Improved drag-and-drop editing** of existing gates, multi-qubit gate placement previews and column insertion.
- **Fit Circuit improvements and Reset Zoom** for navigating long circuits.
- **Light-theme contrast improvements** and consistent `v0.4.0` application labeling.
- **macOS packaging in GitHub Actions** alongside existing Debian/Linux and Windows installer builds.

**Release status:** macOS CI packaging has completed successfully, but the resulting app still needs hands-on testing on a Mac. The packages are not represented as signed or notarized. Some remaining small visual refinements, such as symbol contrast in light mode, may be addressed in later updates.

## Screenshots

Screenshots of the Hydrogen, Quantum Principles and Quantum Circuits workspaces will be added here. Contributions with platform-specific screenshots are welcome.

## Getting started

### Download a desktop package

Check **[GitHub Releases](https://github.com/Onimee58/QuantumScope/releases)** for the latest available files. Package availability depends on whether the release artifacts have been published.

| Platform | Package | Basic installation |
|---|---|---|
| **Ubuntu/Debian (x86-64)** | `.deb` | `sudo apt install ./<downloaded-file>.deb`, then launch QuantumScope |
| **Windows** | `Setup.exe` | Run the setup wizard and launch QuantumScope from the Start Menu |
| **macOS** | `.dmg` | Open the disk image, drag `QuantumScope.app` to Applications, then launch it |

**macOS note:** The current DMG is unsigned/not notarized. macOS Gatekeeper may require explicit user approval under **System Settings → Privacy & Security**. Install only builds you trust. The successful macOS Actions build does **not** by itself confirm runtime or graphics compatibility.

**Graphics note:** 3D rendering uses OpenGL (through pyqtgraph) and requires a compatible graphical environment and drivers; GPU availability and behavior differ by machine and operating system.

### Run from source (Python 3.11+)

Clone the repository and install the application in a virtual environment:

```bash
git clone https://github.com/Onimee58/QuantumScope.git
cd QuantumScope
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
quantumscope
```

On **Windows PowerShell**, activate with `.venv\Scripts\Activate.ps1` and use `python` instead of `python3`. Alternatively, use the included `install_and_run_windows.bat` and `run_windows.bat` launchers. On Linux, `install_and_run.sh` and `run.sh` are also available.

For Ubuntu, the following host packages may be necessary before installing Python dependencies:

```bash
sudo apt update
sudo apt install python3-venv python3-pip libgl1 libegl1 libxkbcommon-x11-0 libxcb-cursor0
```

More setup details: [Windows guide](WINDOWS.md) · [Packaging and builds](PACKAGING.md).

## Your first quantum circuit

1. Launch QuantumScope and open **Quantum Circuits → Gate Circuit Simulator**.
2. Choose **2 qubits** (or leave the current qubit count if already set).
3. Drag **H** from the left palette onto `q0` in the first operation column.
4. Drag **CX** into the next column, then choose its remaining operand as prompted. To prepare a Bell state, use `q0` as control and `q1` as target.
5. Step through the circuit or play the simulation to inspect state probabilities and Bloch spheres.
6. Optionally add terminal **M** gates and press **Run shots** (in the sidebar), or use **Export PDF** to save the circuit diagram.

For the Bell state, the ideal output is `(|00⟩ + |11⟩)/√2`, with theoretical probabilities of **50%** for `00` and **50%** for `11` (up to the displayed bit-order convention). Finite-shot measurements will vary statistically.

**Editor tips:** Drag from the palette to add a gate; click a placed gate to select it; double-click a placed parameterized gate to edit it. Double-click a palette gate to learn about it in the Gate Explorer. Use middle-drag or Shift+left-drag to pan, Ctrl+wheel to zoom, and **Reset Zoom** to restore a readable working size.

## Files and interoperability

| Format | Purpose |
|---|---|
| `.qscope` | QuantumScope's native circuit file |
| `.qasm` / `.qasm2` | Import/export for the implemented **OpenQASM 2 subset** |
| `.pdf` | Exported circuit diagram; optional simulation-related report content |

OpenQASM support is **not** a complete implementation of all OpenQASM 2 features. Unsupported instructions must be handled explicitly rather than silently discarded. The current circuit simulator supports **terminal** measurements, not arbitrary mid-circuit measurement and feed-forward.

## Scientific scope and limitations

QuantumScope aims for scientifically meaningful *models*, but visual demonstrations should be understood within their documented assumptions:

- **Circuit simulation:** ideal statevector evolution on at most 10 qubits, starting from |0⟩ or chosen single-qubit product states; no physical hardware execution, hardware noise, or decoherence model in the current release.
- **Measurements:** terminal measurement statistics are obtained from simulated quantum-state probabilities. Sampling error depends on shot count.
- **Hydrogen:** nonrelativistic isolated-atom model; finite numerical grids approximate bounded portions of wavefunctions. Spin, relativistic and other advanced corrections are outside the current model.
- **Double slit:** idealized far-field/Fraunhofer interference and diffraction model. The apparatus drawing and animated wavefronts are illustrative, not particle paths or a complete propagation simulation.
- **Graphics:** screen representations (cloud brightness, phase coloring and rendered meshes) are visualization choices and should not be mistaken for additional physical observables.

Explore the accompanying documentation: [Dynamics](DYNAMICS.md) · [Circuit simulator](CIRCUIT_SIMULATOR.md) · [Circuit verification](CIRCUIT_VERIFICATION_GUIDE.md) · [Entanglement demo](ENTANGLEMENT_DEMO.md) · [State Inspector & initial states](STATE_INSPECTOR.md) · [Algorithms & blocks](ALGORITHMS.md) · [Learn & your own lessons](LEARN.md) · [Noise & mixed states](NOISE.md) · [Mid-circuit measurement](MEASUREMENT.md) · [Error correction](ERROR_CORRECTION.md) · [Variational algorithms](VARIATIONAL.md).

## For educators and students

QuantumScope can support demonstrations of complex amplitudes, superposition, interference, Bloch-sphere rotations, entanglement, quantum gates, measurement, reversible computation and basic circuit design. The Gate Explorer and step-by-step simulator help connect mathematical descriptions with observable circuit outputs.

**Planned future additions (not present in v0.4.0)** include more guided lessons, richer state/matrix inspection, additional quantum algorithms, noise/error-correction education and quantum kernel visualization. These are roadmap goals, not currently shipped features.

## Tests and development

Install development dependencies and run the regression suite:

```bash
python -m pip install -e '.[dev]'
python -m pytest -q
```

The v0.7.8 source passes **1434 automated tests**. GUI interactions, installers and graphical rendering still require platform-specific testing.

Build configuration and workflows live in `.github/workflows/`, and desktop packaging scripts live in `packaging/`. Please report reproducible errors with your OS version, installation method, screenshots or logs, and a short reproduction sequence.

## Contributing

Issues, pull requests, documentation improvements, classroom exercises and scientific validation cases are welcome. Please keep physics calculations separate from UI logic, add regression tests for changed behavior, and document numerical and physical assumptions.

See [CONTRIBUTING.md](CONTRIBUTING.md) or [open an issue](https://github.com/Onimee58/QuantumScope/issues).

## License

QuantumScope is not open source. From v1.0.0 it opens with a license file, given by your instructor or the developer. Terms of use will be announced.

---

<div align="center">
  <strong>QuantumScope</strong> — bringing quantum physics and quantum circuits together in one interactive desktop studio.
</div>
