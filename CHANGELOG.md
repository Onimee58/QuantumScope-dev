## v0.9.12 — Linux start-up fix

- **Fixed: on Linux, 0.9.11 closed right after starting** on Wayland desktops (Ubuntu's default). The 3-D views' OpenGL library chose its connection to the graphics system from the desktop session (EGL on Wayland) rather than from Qt, and the installers carried only the X11 one (GLX). It now always uses the same one as Qt, and the installers carry both. The packaged self-test checks both are present.

## v0.9.11 — A lighter 3-D engine

### The 3-D views now draw with OpenGL through pyqtgraph, instead of VTK
- **Hydrogen Explorer, Hydrogen Dynamics 3D and the Quantum Kernel Classifier's 3-D view** use one new view (`visualization/gl3d.py`) built on pyqtgraph, which QuantumScope already used for its charts. VTK, PyVista and pyvistaqt are no longer needed.
- **Everything the views did, they still do:** the density cloud, probability enclosures (also coloured by phase, with a colour bar), Real(ψ) and Imag(ψ) surfaces, the axes marker, the coordinate box, the symbolic nucleus; the same camera positions, views and magnification; synchronized comparison cameras; PNG export at 1–4× and the Dynamics and decision-view GIFs; clicking a point in the decision view to see its sample. Exported images include the captions, colour bar and axes marker.
- **Real(ψ) and Imag(ψ):** the lobes are now clearly red (positive) and blue (negative), with a caption saying so, instead of two pale tints and a colour bar whose ends no surface ever had.
- **Panning** in the 3-D views is Ctrl-drag or middle-drag (it was Shift-drag in the decision view).
- **Settings → Graphics:** the "3D volume rendering" choice (Auto/GPU/CPU) is gone: it chose between VTK's renderers. **Graphics device** and the renderer information stay.

### Smaller
- **Measured on Linux:** the installed app is about 350 MB, from about 640 MB in v0.9.10 and 785 MB in v0.9.9 (under half), and the download about 150 MB, from about 220 MB. VTK and the libraries only it needed (matplotlib among them) were most of the difference.
- The release workflow no longer lists VTK modules (`tools/pyinstaller_vtk_args.py` and `visualization/vtk_modules.py` are removed); the packaged self-test builds a contour, a lit mesh and a volume with the new libraries.

### Tests
- New tests check the surfaces (closed, welded, in world coordinates), normals, colour maps, cameras and that nothing loads VTK; GUI tests now draw in the real OpenGL view (`tools/run_gui_tests.sh` starts a virtual display when there is none).

## v0.9.10 — Faster and smaller

### Faster
- **Remembered orbitals:** the Hydrogen Explorer keeps the last four 3-D grids. Changing only the representation, opacity, camera or enclosed probability redraws at once instead of recomputing ψ on the grid (about 0.05 s at 96 points per axis, 0.4 s at 160).
- **Remembered kernel matrices:** a quantum kernel is computed once for each dataset, feature map, repetitions and bandwidth. Retraining with another C or λ, the decision-region grid, and the combinations Search tries reuse it. Kernels estimated with shots are never remembered: each estimate is fresh, as on hardware.
- **Memory first:** remembered results are read-only, kept within a budget (512 MB for grids, 256 MB for kernels), and all forgotten as soon as the memory meter turns amber.
- **No C++ rewrite, on purpose:** profiling showed the numbers already run in compiled code (NumPy, SciPy, VTK, Qt, and QuantumScope's own Cython-compiled modules). A 1,500-sample ten-class SVM trains in about 0.6 s and a 160³ orbital grid takes 0.4 s, so a hand-written core would add build risk on three systems for little gain.

### Smaller
- **Unused Qt parts left out:** Qt Quick and QML (needed only by the on-screen virtual keyboard), the PDF image plugin, Qt Data Visualization, the embedded-Linux display plugins, and Qt's own dialog translations — 126 files (`tools/pyinstaller_trim.py`, applied after PyInstaller's analysis; a test checks that the libraries the app needs always stay).
- **Debugging data stripped** from the bundled libraries on Linux and macOS (PyInstaller cannot on Windows).
- **Measured on Linux:** about 785 MB installed → about 640 MB, and the download about 12% smaller. The packaged self-test passes and the app starts and draws as before.

## v0.9.9 — Labs in every area

### New labs (15)
- **Quantum Principles (5):** find states on the Bloch sphere; build up an interference pattern; run a Bell test; reveal a hidden phase; pure, mixed and entangled.
- **Hydrogen (4):** a tour of orbitals; where is the electron?; watch a quantum beat; predict a spectral line.
- **Mathematics (6), in the calculator:** complex numbers and interference; states, overlaps and gate products; unitary gates and eigenvalues; tensor products and entanglement; Pauli algebra and rotations; an exact gradient from two circuits.
- Each has 3–5 checked steps and one or two questions; the three study guides place them in the suggested path. The course now has 40 labs.

### Labs that follow the experiments
- **The experiments and the calculator tell the labs what the student did:** an orbital drawn, spin copies measured along an axis, particles fired at the slits, pairs sent or a Bell test run, a superposition played, a calculator result. Steps tick at once, with no button to press, and stay ticked once done.
- **New lab checks** for teachers' own labs: `did KIND key=value …` (with >=, <=, >, <, !=, ~ for contains and ± for a tolerance) and `calc gives EXPRESSION` / `calc typed TEXT`; documented in LEARN.md.

### Also
- Tests solve every new lab the way it describes, check that wrong answers do not tick, and check that each experiment records what it should.

## v0.9.8 — A fuller course

### Lectures
- **All 62 lectures follow one shape:** **The idea** (what and why, in a few sentences), the main content, a **Worked example** with real numbers, **Common mistakes**, **In the app** (what to try, step by step, with Try it links), **Check your understanding** and a **Summary**. Most run 450–700 words; a few longer ones keep their extra material.
- **Four questions per lecture** (from two): 249 in all, each with an explanation. The new questions practice the worked examples and the common mistakes.
- **Worked examples are checked against the app's own physics,** for example the H₂ Hartree–Fock energy (−1.116998 Ha) and correlation energy, phase-estimation probabilities for φ = 1/3, Grover's overshoot, Balmer β (486.3 nm), the deuterium isotope shift, quantum-kernel values and the parameter-shift derivative. New Try it links (a partly entangled pair, CZ entangling |+⟩|+⟩, a mid-circuit measurement destroying interference, feed-forward disentangling a Bell pair, SWAP from three CX gates and others) open exactly the circuits described.
- **Two outdated sentences fixed:** measurement is no longer described as end-only, and error correction no longer as "planned".

### Study guides
- **Each area starts with a study guide:** what the area covers and for whom, the time it takes, what to read first, a suggested path through every lecture and lab (by week, block or module), how to study a lecture, and a checklist for the end. The Quantum Circuits guide organizes its 29 lectures and 21 labs into six modules for a semester course.
- **📖 Learn opens the study guide** of the current area; in the contents it comes first, above Lectures and Labs. Teachers can write their own with `kind: guide` (LEARN.md).

### Also
- **Search** ranks a lesson higher when a section heading contains the word, so "hadamard" finds *Single-qubit gates* first.
- Tests check every lecture's sections, length and questions, every study guide's links, and the worked examples' numbers.

## v0.9.7 — Protected code

- **QuantumScope's own code is compiled to native machine code in the installers** (.so on Linux and macOS, .pyd on Windows, with Cython). Before, the installers carried Python bytecode, which free tools turn back into readable source. All 94 modules the app uses are compiled; only the package files (`__init__`) and the start script remain Python, and they hold no logic.
- **How:** `tools/cython_compile.py` compiles the modules in the release workflow; PyInstaller still analyses the Python source (so it finds every library exactly as before), and `tools/pyinstaller_compiled.py` then swaps each module's bytecode for its compiled file. The build stops if any module would ship as bytecode, and the packaged self-test fails on all three systems if a loaded module is not native.
- **Behaving exactly like Python:** compiled with Python's own rules (no strict type checks from annotations). Cython computes `2 ** len(x)` as a decimal (8.0) where Python gives a whole number; three places did this (a reshape, a truth table and the Gate Explorer's "8×8" text) and are written with `<<` now, and the build stops if such a power appears again. The whole test suite and the GUI test suite pass against the compiled modules.
- **Size:** the compiled modules add about 16 MB to the installed app (built small, without debugging data); the VTK savings of v0.9.6 remain.
- **Error reports** still name the file, line and function where an error happened.
- The packaged self-test also checks that the memory meter can read memory (psutil is bundled).

## v0.9.6 — Lighter, and watching its own use

### Smaller installers
- **Only the VTK modules QuantumScope uses are bundled** (38 of about 150; tools/pyinstaller_vtk_args.py builds the list into the release workflow). In a test build on Linux, the installed app went from 970 MB to 770 MB and the compressed download from 314 MB to 258 MB; Windows and macOS shrink similarly.
- **Safeguards:** the list came from every module the whole GUI test suite and the user-guide build load; a test checks that nothing the app loads is missing from it, and the packaged self-test now imports every listed module and builds a contour and a volume pipeline, so a missing piece fails the build instead of a student's session.

### Memory and processor
- **A meter in the status bar** shows QuantumScope's own memory, how full the computer's memory is, and how busy the processor is, every few seconds (psutil, on all three systems).
- **Warnings:** amber when memory is getting full, red when it is nearly full; then QuantumScope says once what to do (save, lower the grid, fewer samples, close other programs, restart), until memory recovers. A processor fully busy for 30 seconds is noted in the status bar, without a dialog.
- **Asking before a big task:** a 3-D orbital grid (once per grid size and viewer count) and a quantum kernel estimate the memory they need, from measurements, and ask first if it would take more than 70% of what is free.
- **⚙ → Graphics and performance** (renamed from Graphics) has **Watch memory and processor use**, on by default.

### System requirements
- **Minimum, recommended and best** (processor, memory, graphics, disk, screen, and what runs well at each) are in the guide, the README and the public releases page, from measurements of the app's memory use: about 0.5 GB on its own, plus 0.1–0.3 GB for a fine 3-D grid per viewer, and up to about 0.15 GB for a 1,000-sample kernel.
- **Supported systems** follow what the installers are built with: Windows 10 (1809 or later) or 11; macOS 14.4 or later on Apple Silicon; Ubuntu 24.04 or Debian 13 or later. PySide6 is held below 6.13, because Qt 6.12 is the last version that supports Windows 10.
- **The Linux package says what it needs:** glibc 2.39 or later (so apt refuses an older system with a clear message instead of the app failing to start) and libxcb-cursor0 (which Qt's X11 support needs).

### Fixed
- **Check boxes** were nearly invisible on dark panels (the Double-Slit's which-path detectors, among others): unticked boxes had no visible edge. Every check box now has an outlined box and a white tick on a coloured fill, in both themes; a test measures their contrast.

## v0.9.5 — Report a problem, and news

### Report a problem
- **⚑ in the header** (and **Report a problem…** in **ⓘ**) opens a report: what happened, what you expected, and a preview of everything the report contains — the QuantumScope version, how it was installed, the system, Python, PySide6 and NumPy versions, and the area and tab you were in. No names, paths or files.
- **QuantumScope sends nothing itself.** **Send by email…** opens your email program with the report filled in; **Open a GitHub issue…** opens a new public issue in your browser. The full report is always copied to the clipboard, and long reports are shortened in the link with a note to paste the full one.
- **A screenshot** of the window can be saved to your Files folder, to attach.
- **The email button** appears once a support address is published in the news (see below); until then, GitHub and Copy report work.

### The crash catcher
- **An unexpected error** used to print only to a hidden console. Now QuantumScope keeps running, says what happened, and offers **Report it…** with the error's details in the report. Each distinct error is offered once; developers still see it printed.

### News
- **The first start asks once**, in a bar under the header, whether QuantumScope may read its news: one public file (news.json in github.com/Onimee58/QuantumScope), at most once a week, with nothing about the user sent.
- **If allowed,** the first current announcement appears in that bar, with **Learn more ↗** when it has a link; **✕** closes it for good. Announcements can be limited to dates and versions, and are plain text only.
- **Offline,** the last news read is shown, and the next start tries again.
- **⚙ → Updates and news** holds the choice (Ask me, Read weekly, Never). Restore defaults asks again but keeps closed announcements closed.
- **Maintainers** edit news.json on GitHub, with no new release; docs/releases-repository/NEWS-HOWTO.md explains the format.

### Also
- **The About page** describes QuantumScope as teaching software for all five areas.
- **The guide** covers Report a problem, the crash catcher and news.
- **Tests:** news files (valid, malformed, dates, versions, dismissal, the weekly rhythm, downloads refused when they are not news), reports (contents, nothing personal, titles, email and issue links, shortening), and in the window the news bar's consent, announcements, links, closing and offline behaviour, the report dialog's email and GitHub routes with the screenshot, the crash catcher, and the setting.

## v0.9.4 — One circuit, many classes

### The Variational Classifier, for any number of classes
- **All classes** now works in the Variational Classifier (and the Datasets tab shares many-class data with both classifiers).
- **One circuit, one outcome per class:** the first r = ⌈log₂ k⌉ qubits are measured; outcome c, in binary on q0 … q(r−1), is class c (2 qubits for three classes, 4 for ten). Outcomes that name no class are discarded and the rest renormalized, with a learned offset per class: P(c | x) = p_c e^(b_c) / Σ p_c′ e^(b_c′).
- **Training** lowers the cross-entropy with exact gradients (adjoint, or the parameter-shift rule as on hardware), with BFGS or Adam, mini-batches, validation and early stopping, exactly as for two classes. The Loss list switches to cross-entropy while all classes are chosen, and returns to your choice afterwards.
- **Results:** decision regions in each class's colour, the many-class Evaluation tab (confusion matrix, macro averages, per-class ROC), cross-validation, saved models (file version 2, with one offset per class) and predictions on new files, which give each prediction's probability.
- **Open in circuit simulator** loads the trained circuit for a test sample with its readout qubits measured, and says which outcome is which class.
- **Too few qubits** to name the classes (such as ten digits on 3 qubits) is explained instead of failing.
- **Typical results** (test accuracy; chance in brackets): Iris 92% (33%), Wine 89%, Penguins 87%, Digits on 6 qubits 65% (10%), MNIST on 8 qubits about 50% (10%). The kernel classifier scores higher on the harder datasets: a small circuit must separate every class at once.

### Lessons
- **"More than two classes"** has a new section, "One circuit, many outcomes", and a quiz on readout qubits; **"Variational classifiers"** points to it.
- **The lab "From three species to ten digits"** has a fourth step: three species with one circuit, read on two qubits in the simulator.
- **The guide** describes All classes and the readout in the Variational Classifier.

### Quality
- **Tests:** the readout's qubit count and outcome order; outcome probabilities against the circuit simulator, gate by gate; the class probabilities by hand; adjoint and parameter-shift gradients against finite differences (angles and offsets); three species with BFGS and Adam; ten digits far above chance; validation and early stopping; cross-validation; two-class training unchanged; saving, loading, predicting and refusing damaged files; and in the whole window, training, the loss switch, evaluation, the model summary, the circuit in the simulator with its outcome probabilities, and the too-few-qubits message.
- **The variational model's code** now has one readout hook, shared by two and many classes, so both use the same training loop.

## v0.9.3 — More than two classes, and four more datasets

### Multi-class quantum kernel classification
- **All classes at once:** under Classes, the Quantum Kernel Classifier (and the Datasets tab) now offers **All classes** beside a pair. One-vs-rest: one SVM or kernel ridge per class, each telling its class from the rest, all sharing one kernel matrix, so no extra circuits are needed; the prediction is the most confident class.
- **The checker** uses every class with at least 10 samples (smaller ones are left out, and it says which) and keeps at least 40 samples per class when it subsamples. A pair stays the default, so existing labs and scripts behave as before.
- **Decision regions** in each class's colour, with every region's edge and a legend; the **kernel matrix** sorted by class with all class borders; the **kernel map** coloured by class with a legend; the **sample viewer** gives the winning class's confidence and the runner-up.
- **The 3-D view** draws each class's region as a coloured surface; **Separating axes** follow the spread of the class centres (completed by the data's own directions).
- **Evaluation:** accuracy, balanced accuracy, macro-averaged precision, recall and F1, the hardest class, a k × k confusion matrix drawn as a picture (green where a class was recognized, red where it was taken for another), and a one-vs-rest ROC curve per class with the mean AUC. **Cross-validation** and the **hyperparameter search** work with many classes.
- **Saved models** of more than two classes (file version 2) store one weight column and offset per class over the points any classifier uses; **Predict on a file** shows each prediction's confidence. Two-class models are still saved as version 1, so older versions of QuantumScope open them.
- **The Variational Classifier** still separates two classes, and says so if the Datasets tab prepared more.

### Four more datasets (offline, with their licences in DATASETS.md)
- **Fashion-MNIST** (MIT): the first 200 images of each of ten kinds of clothing from the official test set, checked against its published checksums. Harder than digits.
- **Palmer Penguins** (CC0): 344 penguins of three species, kept as published, with text columns and missing values for the checker to handle.
- **Seeds** (CC BY 4.0): 210 wheat kernels of three varieties.
- **Glass Identification** (CC BY 4.0): 214 fragments of six unevenly represented types, for learning about imbalance.
- Seeds and Glass come from copies of the UCI files and were checked against UCI's published sample and class counts.

### Lessons
- **A new lecture, "More than two classes":** one-vs-rest and one-vs-one, regions, chance at 1/k, the k × k confusion matrix, macro averages and balanced accuracy, per-class ROC curves, unbalanced classes, and easy and hard datasets.
- **A new lab, "From three species to ten digits",** whose steps tick as you train (a new `qml kernel classes` check).
- **Two glossary terms** (125 in total): one-vs-rest, macro average. "Preparing real data" now mentions All classes.
- **The guide** covers the new datasets, All classes, many-class evaluation and models, with a new screenshot.

### Quality
- **Tests:** the new datasets against their published counts; one-vs-rest equal to k separate SVMs on one kernel; ten digits on eight qubits; many-class metrics by hand and the two-class metrics as a special case; per-class ROC areas against the rank statistic; cross-validation and search; saving, loading and predicting with many classes, and damaged files refused; the 3-D view's axes, grid and agreement; and in the window, every many-class view, the pair choice, the Datasets tab's sharing, and the 3-D view.
- **The Evaluation tab clears an earlier model's cross-validation result** when a new model is trained, so the shown result always belongs to the current model.
- **The self-test** checks all nine bundled datasets, so a build missing the new CSV file fails it.
- **Example images** are labelled with full class names, in the theme's text colour.

## v0.9.2 — Quantum annealing

### The Quantum annealing experiment
- **Open it with + in the Quantum Circuits area.** The anneal follows H(s) = (1 − s)·(−ΣX) + s·H_p from |+…+⟩, simulated exactly (each short slice exponentiated), for MaxCut on five graphs, a frustrated spin glass (choose the spins and the instance), number partitioning (your numbers) or your own Ising problem (Z terms).
- **Spectrum:** the lowest levels of H(s) with the minimum gap circled, refined between grid points so narrow avoided crossings are not missed, and the adiabatic time scale T* = max |⟨1|∂H/∂s|0⟩| / Δ².
- **Symmetry handled correctly:** when every term has an even number of Z's (MaxCut, partitioning), the anneal never leaves the symmetric states (|x⟩ + |x̄⟩)/√2, so gaps are computed there and the chart says so. Problems with degenerate answers use the gap to the first level that is not an answer.
- **During the anneal:** the probability of the answer and the overlap with the instantaneous ground state against s, and the likeliest bitstrings at any s.
- **Success against T** for anneals from T = 0.5 to 80, with the chance of guessing and T*. A spin glass with a tiny gap shows the surprise of the lecture: slower anneals can do worse until T is far beyond T*.
- **Open as circuit:** the anneal as gates (H, then per slice RZ or CX–RZ–CX for each term and RX for the driver), with the problem as the observable and every qubit measured, in the circuit simulator; one Undo restores the previous circuit. QAOA has the same structure with free angles.
- **Everything slow runs in the background;** the window never freezes.

### Lessons
- **A new lecture, "Quantum annealing":** Ising energies, the adiabatic theorem and the minimum gap, avoided crossings, symmetry, digitized annealing and QAOA, hardware annealers and simulated annealing.
- **A new lab, "Anneal fast and slow",** whose steps tick as you anneal (a new `anneal` lab check) and as you build the circuit.
- **Six glossary terms** (123 in total): quantum annealing, Ising Hamiltonian, adiabatic theorem, minimum gap, avoided crossing, digitized annealing.
- **The guide** has a Quantum annealing section with a screenshot.

### Quality
- **Tests:** the symmetric-sector evolution against the full space, the sector's levels against the full spectrum, the circuit against the exact Trotter product, convergence of the time slicing, the adiabatic trend, the problem definitions, cancellation; and in the whole window, the experiment's results, its input checks, the success curve, and the circuit's energy and undo.

## v0.9.1 — More optimizers, and optimizing with shots

### Optimizing with shots
- **A Shots choice beside Optimize:** **Exact**, or 100, 1,000 or 10,000 measurements of each term of the observable. Each term's estimate is drawn from the exact distribution of ±1 outcomes, so the noise is unbiased and shrinks like 1/√shots, as on hardware.
- **With shots the optimizer only sees noisy energies,** and gradients come from the parameter-shift rule on them (the adjoint method needs the exact state, which hardware never gives).
- **The Optimize chart draws the measured ⟨H⟩ (thin) beside the true ⟨H⟩ (bold),** and the summary reports the true result and the number of measurements used.

### Five new optimizers
- **Adam:** momentum and a step size per parameter.
- **SPSA:** a gradient estimate along a random direction from two circuit runs per step, however many parameters; the usual choice on hardware. Its gains follow Spall, with a calibrated step size.
- **Rotosolve:** each parameter in turn set to its exact minimum, from a trigonometric fit (3 values for a parameter driving one rotation; more for a parameter shared by several gates). No learning rate.
- **Quantum natural gradient:** steps along g⁻¹∇⟨H⟩, with the Fubini–Study metric g computed exactly from the state's derivatives; stronger regularization and smaller steps with shots.
- **Simulated annealing:** random moves, uphill ones accepted with probability e^(−ΔE/T) as the temperature falls.
- **Every method has a tooltip.** "Max steps" means the same for all of them (for Rotosolve, parameter updates).
- **Best of N** works with every method and with shots.

### Lessons
- **A new lecture, "Optimizing with shots":** shot noise, SPSA, Rotosolve, the quantum natural gradient, simulated annealing, and how to choose an optimizer.
- **The optimizer lecture's table** lists all nine methods.
- **Five glossary terms** (117 in total): shot noise, SPSA, Rotosolve, quantum natural gradient, simulated annealing.

### Quality
- **Tests:** the state derivatives and the metric against finite differences and the fidelity expansion; shot noise unbiased and shrinking like 1/√shots; every method reaching the ground state with exact energies; SPSA's cost and its success under shots, where Nelder–Mead fails; Rotosolve's fit equal to the energy; annealing's uphill moves; repeatable random methods; the chart's measured curve unbiased for every method.
- **A timing-dependent GUI test** (editing the circuit during an optimization) now uses a run long enough on any machine.

## v0.9.0 — The Math tab: a quantum calculator

### The Quantum Calculator
- **A fifth area, Math,** with the **Quantum Calculator**: quantum mathematics in Dirac notation.
- **Two modes, one meaning.** **Exact** (SymPy) keeps √2, i and π, and leaves names without values, such as θ, as symbols: exp(−i θ X / 2) gives the rotation matrix in θ. **Digits** (NumPy) computes numbers, and still shows familiar values exactly. Both evaluate the same parsed expression, and tests compare them.
- **Notation:** kets, bras and brackets (⟨a|b⟩, ⟨a|M|b⟩), ⊗, †, powers, matrices, named values, and a keyboard form for every symbol (|0>, <0|, (x), ').
- **Built in:** |0⟩, |1⟩, |±⟩, |±i⟩ and strings of them; I, X, Y, Z, H, S, T, CNOT, CZ, SWAP, RX, RY, RZ, P and U.
- **Functions:** exp (the matrix exponential), tr, det, inv, norm, normalize, kron, comm, acomm, eig, dm, ptrace, expect, fidelity, purity, entropy, bloch and pauli.
- **The result:** one line (states in Dirac form), the matrix labelled by basis states, the working step by step, and a Bloch sphere for single-qubit states. Named values and history; errors say what is wrong and where.
- **Send to circuit simulator:** a product state becomes the circuit's starting state exactly (undoable); an entangled state is explained instead.

### Lessons and guide
- **Every Mathematics lesson has a Try it in the calculator link** that opens the calculator with the lesson's example worked out, from exp(iπ/4) to the parameter-shift rule, which gives −√3/2 exactly.
- **A new Math chapter in the user guide.**

### Requirements
- **SymPy** is now a dependency (loaded only when exact mode is first used, so start-up is unchanged).

### Quality
- **Tests:** the parser and its errors; the two modes agreeing on over 40 expressions; textbook identities (the Bell state, [X, Y] = 2iZ, HXH = Z, exp(−iθX/2) = RX(θ)); the quantum functions; sending states to the circuit simulator; every calculator link in the lessons.

## v0.8.5 — The user guide's text is readable again

### Fixes
- **The user guide's body text was nearly invisible** (pale grey on white) in the guides shipped with v0.8.2 to v0.8.4; only captions and screenshots stood out. The guide is built after the screenshots, which switch the app to its dark theme, and text without its own colour took that theme's near-white. Pages now print in a fixed palette (dark text, blue links), whatever the app's theme.

### User guide
- **The cover now shows a quantum circuit and a Bloch sphere** over the double-slit detections: a three-qubit GHZ circuit, and a sphere in a true 3-D projection with one state vector.

### Quality
- **New tests:** a text page drawn under the dark theme must be dark, and the committed guide's contents page must have dark ink. Both fail on the v0.8.4 builder and PDF.

## v0.8.4 — The start-up logo on every system, and a new guide cover

### Fixes
- **The start-up logo (the Q) now shows on Linux and macOS,** not only on Windows. There, a new window appears only when the window manager shows it, a moment later; QuantumScope moved on to its slow start-up work before that, so the logo never painted. It now waits until the logo is on screen, for at most half a second. (Reproduced under X11 with a window manager: painted in 0 of 5 starts before, 5 of 5 now.)

### User guide
- **A new cover:** a double-slit pattern built from single detections, as QuantumScope's own detector screen draws it, with the title, the version and date, the author and affiliation, and the project's address and licence.

### Quality
- **Tests:** the splash under X11 with a real window manager (run where xvfb-run and openbox are installed); the cover's content.

## v0.8.3 — Evaluating and tuning the Quantum ML classifiers

### Evaluation
- **An Evaluation tab in both classifiers:** the test set's accuracy, balanced accuracy, precision, recall, specificity, F1 and AUC, the confusion matrix (labelled with the class names), and the ROC curve with the chance diagonal.
- **Cross-validate** (k folds, stratified) gives the mean ± spread and every fold's score. The kernel classifier shares one training kernel across all folds, with no new kernel values needed; the variational classifier trains a fresh model per fold.
- **All metrics are checked against independent computations,** and the AUC is computed two ways: the area under the curve, and the equivalent rank statistic.

### Hyperparameter search (kernel classifier)
- **A Search tab:** choose the feature maps, classifiers, bandwidths, repetitions, C or λ values and folds.
- **Every combination is cross-validated on the training data** (the test set is never used), sharing each kernel across folds and classifier settings: 54 settings × 5 folds take about a second.
- **The results are listed best first** (the highest mean, then the steadiest), and **Use best** applies the winner and trains it.

### Training controls (variational classifier)
- **Loss:** mean squared error, hinge or cross-entropy, each with exact gradients.
- **Learning rate** and **Batch size** for Adam (random mini-batches, reproducible from the seed).
- **Validation share:** held-out training data, with its loss and accuracy drawn as dashed curves. **Early stopping** ends training when the validation loss stops improving, and keeps the best step.
- **Saved models record their loss.**

### Lessons
- **A new lecture, "Evaluating a classifier":** the confusion matrix and its measures, the ROC curve and what its area means, training, validation and test sets, cross-validation, the optimistic bias of a hyperparameter search, and early stopping.
- **Seven glossary terms** (112 in total): confusion matrix, precision, recall, ROC curve, cross-validation, hyperparameter, early stopping.

### Quality
- **Automated tests:** 1604 passing, plus 160 opt-in GUI tests.

## v0.8.2 — Saving models, seeing kernels, and a 3-D decision view

### Saving and using trained models
- **Both classifiers have a Model panel:** a summary of the current model, **Save model…**, **Load model…** and **Predict on a file…**.
- **A model file holds everything a prediction needs:** the classifier, its settings, and the preprocessing it was trained with (classes, missing-value means, PCA and scaling, all fitted on the training data), so new data is prepared exactly like the training data.
  - **Small:** an SVM keeps only its support vectors (a 3-vs-8 MNIST model is about 26 KB).
  - **Safe:** a NumPy `.npz` file with a JSON header, never unpickled.
  - **Open in Python** with `numpy.load`.
  - **Clear messages** for files that are not models, damaged, incomplete, or from a newer QuantumScope.
- **Loading a model sets the controls to match it,** so **Train** rebuilds the same model.
- **Predict on a file…** reads `.csv` (columns matched by name, in any order; the label column is optional) or `.npz` (images flattened). It runs in the background and shows each sample's prediction and decision value, with the true class, correctness and accuracy when the file has labels; samples of other classes are counted separately. **Export CSV…** saves the results.

### Seeing the kernel
- **Kernel map** (a new tab beside the kernel matrix): the data as the kernel sees it, by kernel PCA of the kernel the classifier already computed. It equals ordinary PCA for a linear kernel, and flags kernel concentration.
- **The kernel matrix is interactive:** hover over a cell for its value and the two samples' classes; click it to see both samples.
- **A sample viewer** shows what you click (the image, for Digits and MNIST).
- **A draggable divider** sets the space between the decision regions and the kernel views.

### 3-D decision view
- **A new tab beside the decision regions:** the points along **Principal components** or **Separating axes**, with the decision boundary as a surface and, for an SVM, the **Margins**. Support vectors have a halo; test points are cubes and mistakes red.
- **Drag to rotate,** scroll to zoom; **Front**, **Top**, **Side**, **Isometric** and **Reset**; click a point to see its sample.
- **With more than three features it is a slice,** and the caption gives how often the slice agrees with the classifier (100% with three features).
- **Save image…** and **Save rotating GIF…** (a full turn, for slides).
- **Computed in the background,** only when the tab is first opened.

### Fixes
- **The Quantum ML control columns scroll instead of squashing** when the window is short. Every control keeps its natural size, lists show long names in full when opened, and the columns fit every dataset's controls.
- **The updater never freezes the window:** checking and downloading run in the background with **Cancel**. GitHub's temporary errors (500, 502, 503, 504, timeouts) are retried up to three times, and lasting trouble is explained with a link to the release page. (Reported: updating from 0.8.0 stopped responding, then showed error 504.)
- **The test comparing adjoint and parameter-shift optimization** now accepts rounding differences (paths agree to 10⁻⁶; step counts within two), which had failed v0.8.1's first release build.

### Quality
- **Automated tests:** 1587 passing, plus 157 opt-in GUI tests, including layout checks across datasets and window sizes, and the updater under slow and failing networks.

## v0.8.1 — Speed, and no more frozen windows

### Faster
- **The circuit simulator is vectorized:** each gate is one array operation instead of a Python loop over every amplitude (17× faster at 10 qubits), and a simulation no longer runs the circuit twice. Results are the same up to rounding (about 10⁻¹⁶): checked gate by gate against the original code.
- **The circuit optimizer uses adjoint gradients:** one forward and one backward pass give every derivative at once, instead of two circuit runs per bound gate, with each gate's exact derivative (RX, RY, RZ, P, CP, U). Noisy and dynamic circuits keep the parameter-shift rule. The optimizer follows the same path up to rounding in the last digits, which can change by a step when it stops.
  - **Optimize** on the 6-qubit, 3-layer QAOA example: 13.2 s → 0.6 s.
  - **Best of 3:** about 40 s → 1.4 s.
  - **The landscape:** 6.1 s → 1.6 s.
- **The variational classifier** uses adjoint gradients too, and computes its loss, gradient and progress from one pass: 10 qubits, 107 s → 7 s; 8 qubits, 11 s → 1.3 s.
- **The SVM solver** picks the maximal violating pair (as LIBSVM does): 35–55× faster, reaching the same optimum (checked against SciPy).
- **ZZ feature-map states:** 3.6× faster at 10 qubits.

### No more frozen windows
- **Training, Optimize, Best of N and the landscape run in the background,** with progress shown, so the window stays responsive.
  - **Stop** and **Cancel** end a run early; closing its window stops it too.
  - **The optimizer works on a copy of the circuit,** and its result is applied only if the circuit was not edited meanwhile.

### Fixes
- **Chart menus:** right-clicking a chart offered "Plot Options" (FFT, log scales, …), which crashed on scatter and bar charts. Every chart now offers **View All**, the axis options, **Save image…** (twice the screen resolution), **Copy image** and **Save data (CSV)…**, replacing pyqtgraph's Export dialog, which opened squashed and whose SVG and Matplotlib formats failed.
- **The release workflow** reads the version from the code and refuses a tag that does not match. v0.8.0's first build had named its installers 0.7.8.

### Quality
- **A golden replay** of 19 circuit-editor steps is now part of the test suite.
- **Performance tests** set time limits, so speed cannot quietly regress.
- **Automated tests:** 1568 passing, plus 146 opt-in GUI tests. The whole suite runs in about 11 s (was 33 s).

## v0.8.0 — Quantum machine learning, VQLS, and the guide upgraded

### Quantum ML (a fourth area)
- **Datasets:** five built-in datasets, shipped with the app and used offline: Iris, Wine, Breast Cancer Wisconsin (Diagnostic), Digits (8×8) and a 2,000-image MNIST subset (the first 200 of each digit from the MNIST test set, verified against the official checksums). Synthetic moons, circles, XOR and blobs.
  - **Your own data:** **Import CSV or .npz…** (header, label column, text columns, missing values and separators detected).
  - **The checker:** a verdict (ready, usable after preprocessing, cannot be used) and findings with suggested fixes.
  - **Preprocessing,** step by step and adjustable: classes, missing values, text columns, constant features, balanced subsampling, PCA and scaling to [0, π]. The split comes first, and every learned step is fitted on the training data only.
  - **Licences:** `DATASETS.md` lists each dataset's licence (CC BY 4.0; CC BY-SA 3.0 for the MNIST subset) and citation.
- **Quantum Kernel Classifier:** angle encoding or the ZZ feature map (with repetitions), a bandwidth, exact kernels or kernels estimated from shots, an SVM (SMO, checked against SciPy) or kernel ridge, a kernel heatmap, and decision regions for any number of features (in the plane of the two leading principal components), with a boundary line and confidence shading. A hint appears when the kernel concentrates.
- **Variational Classifier:** feature map plus trainable RY/CNOT layers, trained with BFGS (exact parameter-shift gradients) or Adam, with a live training curve, **Stop**, and **Open in circuit simulator**.
- **Classes:** for datasets with more than two classes, the classifiers choose the pair to separate. With data from the Datasets tab, **Qubits (= features)** follows what was prepared.

### VQLS
- **Algorithms → Variational quantum linear solver:** the standard 3-qubit system, a worse-conditioned one, a 1-qubit one, or your own A (a Pauli sum on 1–3 qubits, checked for invertibility) with b = |0…0⟩, |+…+⟩ or |1…1⟩. The cost A†(I − |b⟩⟨b|)A is the observable, so **Optimize**, **Landscape** and **Best of N** apply. The check passes at a fidelity of at least 0.99 with A⁻¹b, and **Show the solution** compares the amplitudes live.

### Lessons
- **Learn → Quantum ML:** five lectures (from data to quantum states; kernel classifiers and the SVM; variational classifiers; generalization, bandwidth and kernel concentration; preparing real data) and three labs. New lab checks (`qml …`) tick steps as the experiments run.
- **A VQLS lecture and lab** in Quantum Circuits, and 14 glossary terms (105 in total).

### The user guide
- **21 pages:** a title page, a table of contents with page numbers, PDF bookmarks, clickable entries, numbered figures with a list of figures, page numbers, and chapters on Quantum ML and VQLS.
- **References:** 41 references, each checked against its publisher, the arXiv or a library record (`docs/references.md`).
- **The builder** (`tools/guide_pdf.py`) repairs blank spots by shrinking figures slightly or letting them float below their text within their section, and checks every page.

### Quality
- Automated tests: 1545 passing, plus 137 opt-in GUI tests. A golden replay of 19 circuit-editor steps is unchanged.

## v0.7.8 — User guide

### The guide
- **`QuantumScope-User-Guide.pdf`:** 13 pages with 11 screenshots, written for anyone who uses QuantumScope. It covers installing and updating, a tour of the window, Hydrogen, Quantum Principles, Quantum Circuits, Learn, Settings, troubleshooting, and a mouse and keyboard reference.
- **Exact names:** every control is named as it appears in the app, taken from a programmatic inventory of the real windows. A test checks that the controls it names still exist in the code.
- **Delivery:** it ships inside QuantumScope (**ⓘ → User guide** opens it in the system's PDF viewer, or the releases page if it is missing), and the release workflow attaches it to each release. The updater only ever picks installer files, so the PDF can never be mistaken for one.

### Rebuilding it (authors)
- **The source** is `docs/user-guide.md`.
- **`python tools/make_user_guide.py`** photographs the real app (`docs/images/`) and lays out the PDF with Qt (`--pdf-only` skips the screenshots).
  - **On a desktop,** the Hydrogen screenshot includes the live 3-D view.
  - **Without a display,** it shows the Explorer's controls, since software 3-D rendering is unreliable there.
- **The self-test** checks that the guide is packaged.

### Quality
- Automated tests: 1434 passing, plus 128 opt-in GUI tests.

## v0.7.7 — Learn → Mathematics

### Mathematics lessons
- **A fourth area in Learn, Mathematics,** with 12 lectures, each with worked examples, quizzes, a **Try it** link into the app, and a summary:
  - complex numbers; vectors and Dirac notation; matrices acting on states;
  - conjugate transpose, Hermitian and unitary; eigenvalues and eigenvectors;
  - probability for quantum experiments; tensor products;
  - outer products, projectors and density matrices; matrix exponentials and rotations;
  - Pauli algebra; the discrete Fourier transform; gradients and optimization.
- **Every formula, worked example and quiz answer was checked numerically** (23 checks), and every Try it link is checked by the link parser.

### "Math you need"
- **A box under the objectives of all 40 physics lectures** links to the math lessons each one builds on.
- **Authors** list them with a new `math:` header field (see LEARN.md).

### Glossary
- **91 terms (+10):** a new **Mathematics** group (complex number, conjugate transpose, inner product, outer product, projector, trace, partial trace, matrix exponential, commutator, gradient). All their links in the lessons were checked in context.
- **Hermitian, Unitary, Eigenvalue, Tensor product, Pauli matrices and Dirac notation** now open the matching math lesson from **Learn more**.

### Quality
- 400 new equation images; no existing image changed.
- Automated tests: 1431 passing, plus 127 opt-in GUI tests.

## v0.7.6 — Teleportation redesigned

### Physics (`physics/teleport_story.py`, the circuit engine)
- **A noisy shared pair:** *v*·(Bell pair) + (1 − *v*)·(completely random pair), computed through the same branch engine as the circuit simulator.
  - **The fidelity is (1 + *v*)/2 for every result,** reaching the classical limit of ⅔ at *v* = ⅓.
- **Skipping Bob's correction:** result 00 stays right, and on average Bob's qubit is random (fidelity ½).
- **New functions:** `expected_fidelity()` and `teleport_once()`. Existing calls behave exactly as before.

### The experiment
- **A mini circuit** with the current step highlighted; skipped corrections are shown as skipped.
- **Three shaded Bloch spheres** (q0 Alice's input, q1 Alice's half, q2 Bob), animated between steps, with flashes when Alice measures and when Bob corrects. Drag q0 at the start to choose the state.
- **A classical channel:** Alice's two bits visibly travel to Bob before his correction.
- **▶ Play,** **Clean pairs,** **"Bob applies the correction",** and **Teleport many** with a fidelity meter (½ random, ⅔ classical limit, 1 perfect, and the expected value).
- **Open in the circuit simulator** works as before.

### Fixes
- **Entanglement:** Bob's delayed measurement uses a timer owned by the dialog, so it can never fire into a closed dialog.
- **GUI tests:** a process that used pyqtgraph charts could crash at the very end, after every test had passed, because a forced deletion of a chart crashes at random. Like the 3-D tests, such processes now exit right after reporting, keeping their result.

### Quality
- Automated tests: 1367 passing, plus 126 opt-in GUI tests.

## v0.7.5 — Entanglement redesigned; turning the spheres

### Turning the spheres
- **Every Bloch sphere has its own turntable camera:** **right-drag** or **Shift + left-drag** turns it, and **double-click** resets it. |0⟩ stays on top, and the tilt is limited to ±80°. Left-drag still sets the state (or, in Entanglement, aims a detector), exactly, however the sphere is turned.

### Entanglement
- **Exact physics** (`physics/bell.py`, no Qt), using density matrices:
  - the four Bell states, a classically correlated mixture, and noise (a visibility *v*);
  - joint probabilities for any two axes;
  - each qubit's own (reduced) state, and Bob's state after Alice's result;
  - correlations, and CHSH with the best angles for each state.
- **Tested:** the textbook formulas, agreement with the existing singlet code, no-signalling, Tsirelson's bound 2√2 (scaling as 2√2·*v*, so it crosses 2 at *v* = 1/√2), and the classical mixture never above 2.
- **Two spheres, Alice's and Bob's,** show each qubit's own state: "random" for an entangled pair. Dragging the amber axis aims each detector.
- **Send one pair:** it flies out; Alice measures and both spheres jump, then Bob measures. The text explains why no signal travels.
- **Send many:** Slow, Fast or Instant, filling a **correlation grid** (with predicted shares) and a **correlation curve** (quantum, the simple classical model, and the measured points).
- **The Bell-test meter:** |S| with its uncertainty, against the classical limit of 2 and the quantum limit of 2√2, with a verdict ("beats", "stays below", "too close to decide").
- **Removed:** the old Entanglement experiment and its unused drawing classes.

### Quality
- Automated tests: 1361 passing, plus 125 opt-in GUI tests.

## v0.7.4 — Quantum Principles redesign, part 1

### Shared building blocks (`gui/principles_visuals.py`)
- **A shaded Bloch sphere:**
  - a lit surface, with the far half of the grid dimmed;
  - labelled poles, and a glowing state arrow with its shadow;
  - an amber measurement axis with its +1 and −1 ends;
  - **smooth animated changes** and a **flash on collapse**.
- **Dragging the arrow** sets the state. Grabbing it keeps its side of the sphere, and dragging past the rim carries it round, so every state can be reached. The viewpoint shows every preset and typical state clearly, never end-on.
- **Live tallies:** outcome bars that grow smoothly as counts arrive, with dashed Born-rule targets.

### Superposition
- **Prepare** by dragging, with the θ/φ sliders (which follow the drag), or with presets (|0⟩ |1⟩ |+⟩ |−⟩ |+i⟩ |−i⟩).
- **Measure once:** the animated collapse onto +1 or −1, then counted.
- **Measure many:** fresh copies streamed into the tally (Slow, Fast or Instant; Stop).
- **Less text:** one short line explains what just happened.
- **Changed:** dragging the sphere used to rotate the view; it now sets the state, as students expect.

### Double-Slit
- **A detector screen:** each particle lands as one glowing dot, and dense places glow brighter, so the fringes emerge from individual detections. Firing runs at Slow, Fast or Instant speed, with Stop.
- **The wavelength sets the colour** of the dots, the drawn waves and the apparatus hits. Ultraviolet and infrared are shown in a labelled false colour.
- **Dragging the slits** changes their separation: the exact inverse of the drawing rule.
- **The physics is unchanged:** the Fraunhofer model, its sampling and the chart are as before.

### Fixes
- **The circuit tab:** a short circuit in a tall window, for example after **Clear** in a maximized window, stretched the heading into a blank band above the tools. Spare height now goes below everything.
- **Clear** (or leaving an example) left the last example's check on screen, for example a VQE energy for an empty circuit. The verification panel now resets. Editing the example keeps its check.

### Testing
- **A CI fix:** a test module that needs Qt's graphics libraries now skips cleanly where they are missing. Before, `importorskip` let a missing system library stop the whole test run.
- Automated tests: 1349 passing, plus 122 opt-in GUI tests.

## v0.7.3 — Glossary and splash

### Glossary
- **81 terms** in nine groups (quantum basics, measurement, linear algebra, gates and circuits, states, noise, measurement in circuits, error correction, algorithms, and hydrogen), each with aliases, a definition, related terms and the lesson that teaches it.
- **Automatic links:** the first occurrence of each term in a lesson is linked, longest terms first ("phase flip" before "phase"). Links appear in body text only, never in headings, quizzes, lab steps, code, equations or existing links. Acronyms match exactly. All 265 automatic links in the lectures were checked in context.
- **Clicking a term** opens a popup with its definition, related terms (themselves links), **Learn more** and **All terms**.
- **A Glossary page** in the Learn contents.
- **PDF handouts** print terms as plain text and end with a **Terms used** box.
- **For authors:** `[[Term]]` or `[[shown text|Term]]` makes an explicit link, and `noglossary: Term, …` in a lesson's header switches terms off there. Teachers' own lessons are linked too.

### Start-up
- **A splash screen:** only the Q, on a transparent background, shown as soon as Qt starts. It covers loading the 3-D libraries, then closes when the window appears.

### Packaging
- **The glossary and the splash logo are always packaged:** `learn/content/*.md` is now part of the package data, and the self-test checks both files.

### Quality
- Automated tests: 1346 passing, plus 119 opt-in GUI tests.

## v0.7.2 — Fixes

- **Learn → Export PDF:** handouts printed their body text at 0.7 pt, because pixel sizes were sent to a 1200-dpi printer. They now use points: 11-pt text, with headings (13.2 pt) and titles (16.5 pt) above it, and box padding and borders in proportion. Equations were already correct.
- **The circuit sidebar:** on tall pages (for example with many parameters), the Classical/Noise row took the spare height and the Noise buttons drifted down. The row now has a fixed height, with both columns at the top.
- **Updating on Ubuntu:**
  - **QuantumScope waits for the installer** after you enter your password, then offers **Restart now**.
  - **A cancelled password prompt or a failed install** is explained, with the manual `sudo apt install` command.
  - **No leftover "defunct" installer process.** Before, the app gave no sign when the install had finished.
- Automated tests: 1338 passing, plus 117 opt-in GUI tests.

## v0.7.1 — Tester suggestions

### Circuit tab layout
- **A fixed 400-px sidebar:** the gates, 6 per row; Classical and Noise side by side; **Measurement shots** (with **Run shots**); and **Circuit Verification & Truth Table** (Input · Output · Expected · Result, long cells wrapped). The results and their check now sit side by side.
- **The canvas height fits the circuit:** one row per qubit plus a spare one, up to ten. It used to be fixed at ten.
- **Removed: the Bloch spheres beside the wires**, with their setting. Every qubit's Bloch sphere stays in the panel under the chart and in the State Inspector.
- **No sideways scrolling:** a long status message no longer widens the page (this was latent in every version), and the Optimize options take two lines. The page's minimum width fell from about 1,420 px to about 1,070 px.

### Parameters
- **Randomize all**, and **🎲** for one parameter: random angles in −π…π, each one undo step.
- **Best of N random starts** (off by default; N = 5) keeps the best of several optimizations.
- **Two columns of parameters** on wide panels, filled across (γ0 β0 / γ1 β1 …), with compact usage counts and ✕.

### Tabs
- **Every tab can close,** including the Hydrogen Explorer and the Gate Circuit Simulator.
  - **Closing only hides a tab,** so reopening it (from **+**, a placeholder, Learn, or the QASM Converter) brings it back as you left it.
  - **An empty area shows a placeholder** with its experiments instead of a blank window.
- **Experiments open in their own area:** the Error-correction explorer used to open in Quantum Principles. Every entry of every **+** menu is now tested.

### Fixes
- **No more highlighted rows on the circuit canvas:** pressing Ctrl+A or Shift+arrows selected cells, which showed up as highlighted rows.
- **GUI tests:** test runs that use the 3-D view sometimes crashed at exit after every test had passed, also in v0.7.0. They now exit cleanly, keeping the result.

### Quality
- Automated tests: 1338 passing, plus 110 opt-in GUI tests (`tools/run_gui_tests.sh`). The 44-step editing replay is unchanged.

## v0.7.0 — Variational algorithms

### Updates
- **ⓘ About → Check for updates…** (also in **Settings → Updates**):
  - **with permission:** it asks first, makes one request to GitHub's release list, and only ever offers full releases (never pre-releases);
  - **verified:** downloads are checked against the release's SHA-256 checksum, and a mismatched file is deleted;
  - **installing:** happens after confirmation (the Windows installer, the macOS DMG, or the Ubuntu package with a password prompt). Source checkouts are shown the `git pull` instructions instead;
  - **errors** have clear messages, including GitHub's rate limit.
- **The release workflow** publishes a `.sha256` file next to each installer.

### Parameterized circuits
- **Parameters:** type a parameter name as a gate angle (RX, RY, RZ, P, CP, U).
  - **Greek letters** are written as in LaTeX (`\theta` → θ); plain names stay as typed.
  - **Factors** share a parameter among gates (`2*\gamma`, `-\beta`). Binding never changes the circuit, and bound gates show their parameter.
- **The Parameters panel** (under the circuit, shown when in use) has sliders, exact values, usage counts and Delete. One drag is one undo step, and the panel keeps its rows readable and scrolls past four.
- **Observables** are Pauli sums (`Z0 Z1 + 0.5 X0`). The panel shows ⟨O⟩, exactly, including under noise and mid-circuit measurement, next to the exact lowest possible value. It explains observables in words, with an Examples menu.
- **Files and QASM:** saved with the circuit as an optional field (older versions open the circuit at its current angles), and written as QASM comments.

### Optimization
- **Methods:**
  - **BFGS** (the default) and **gradient descent**, both with exact **parameter-shift** gradients. Gradient descent uses a backtracking line search, so it never goes uphill;
  - **COBYLA** and **Nelder–Mead**, which need no gradients; only their improving steps are recorded.
- **The live convergence window** shows the exact minimum, the steps and circuit evaluations used, and a Stop button. It gives a clear explanation when the circuit can't reach the exact minimum or no step helps.
- **Parameters are wrapped** back into −π…π where that provably changes nothing.
- **Energy landscapes** show one parameter as a curve or two as a color map, with the optimization path.

### Algorithms
- **VQE:**
  - **problems:** H₂ (two qubits, 0.735 Å; −1.137306 Hartree, checked against the known value) and Ising and Heisenberg chains;
  - **ansatz:** 1–3 entangling layers;
  - **check:** ⟨H⟩ within 0.001 of the exact ground energy.
- **QAOA for MaxCut:**
  - **graphs:** five, from a square to a triangular prism, with 1–3 layers of γ and β;
  - **graph view:** live, with the likeliest cut and the cut-size distribution;
  - **check:** against the brute-force maximum cut. Even rings reach the known ratio 3/4 at one layer.

### Learn
- **Lectures:** *Observables and expectation values* (Quantum Principles); *Parameterized circuits*; *The parameter-shift rule*; *The variational quantum eigensolver*; *Optimizers, landscapes and plateaus*; *QAOA and MaxCut*.
- **Labs:** *Tune a circuit by hand*; *Find H₂'s ground energy*; *Not enough layers*; *Cut a graph with QAOA*.
- **For course authors:** new lab checks `parameters`, `bound`, `observable`, `expectation`, `reaches` and `verified`; Try it links accept `bind=` and `observable=`; **Learn more** now links VQE and QAOA to their lectures.

### Fixes
- **The circuit page** was measured once when built, so a growing panel was squeezed and controls overlapped; it now re-measures itself.
- **The convergence chart** no longer zooms into rounding noise.

### Quality
- Automated tests: 1336 passing (1182 in v0.6.2 + 154 new), plus 101 opt-in GUI tests (run them with `tools/run_gui_tests.sh`, which keeps the 3-D Hydrogen tests in their own process). The 44-step editing replay is unchanged.

## v0.6.2 — Error correction and phase estimation

### Error correction
- **Bit-flip code** and **phase-flip code** examples (5 qubits).
  - **How they work:** data q0–q2 encode q0's state, and ancillas q3 and q4 measure the parities mid-circuit into c0 and c1. Corrections are conditioned on both bits.
  - **Errors to inject:** none, one error on a chosen qubit, two errors (beyond the code), or random errors (noise boxes of strength p).
- **Shor code (9 qubits):** corrects any single-qubit X, Y or Z error, coherently with Toffoli majority votes.
- **Checks** test all six logical inputs on the current circuit.
  - **Two errors fail**, as they should: that's the code's limit.
  - **Removing the Shor code's final majority vote** fails the check.
- **Logical error rate:** one exact sweep with two entry points.
  - **Plot logical error rate** in the verification panel sweeps the noise boxes of the *current* circuit.
  - **Quantum Circuits → + → Error-correction explorer** lets you choose the code and the noise type and drag p.
  - **Exact agreement:** both reproduce 3p² − 2p³ for matched codes and (1 − (1 − 2p)³)/2 for mismatched ones.

### Conditions on several classical bits
- **In the editor:** **Run only if… → Several bits…** (e.g. c0c1 = 10), shown as a badge.
- **Engine and files:** the branch engine, undo and **`.qscope` schema 6** all support them. Single-bit conditions stay schema 5.
- **OpenQASM 2:** bits tested together share one register (`creg r0[2]`) and conditions become `if(r0==value)`. A condition on part of a register expands into one `if` per matching value. Multi-bit `if` is now imported too.

### Quantum phase estimation
- An Algorithms entry with 1–6 counting qubits and exact or inexact phases.
- **The check:** the closest t-bit estimate must win, with probability 1 when φ is exact and at least 4/π² ≈ 0.405 otherwise.

### Example titles and qubit labels
- **A title bar** for circuits built from Examples or Algorithms: the title, its parameters, **Change parameters…**, and **Learn more**, which opens the matching lecture. It shows *(edited)* after changes and clears it when Undo restores the example.
- **Qubit labels for any circuit:**
  - examples fill them in;
  - **click a qubit's label → Label this qubit…** to name your own;
  - they're kept when the number of qubits changes, and cleared by Clear (Undo restores them);
  - they're shown in PDF exports and as QASM comments.
- **Saved with every circuit** as optional fields that older versions ignore, so the format is unchanged.

### Learn
- **Lectures:** *The bit-flip code*, *The phase-flip code*, *Logical error rates and thresholds*, *The Shor code and stabilizers*, *Quantum phase estimation*.
- **Labs:** *Build the bit-flip code*, which includes labeling your own qubits; *Beat the noise*; *Phase estimation precision*.
- **For course authors:** a new lab check `labeled`, links to the Examples (`qs:algorithm/bit_flip_code?…`), and the `qec` view.

### Fixes
- **Qubit roles** stayed after Clear, and a newly added qubit was left unlabeled.
- **A test crash:** an intermittent crash at the end of GUI test runs, after all tests had passed. It was present in v0.6.1's tests too; Qt is now torn down in order.

### Quality
- Automated tests: 1182 passing (1051 in v0.6.1 + 131 new), plus 83 opt-in GUI tests. The 44-step editing replay is unchanged.

## v0.6.1 — Measurement and feed-forward

### Dynamic circuits
- **Mid-circuit measurement (M→c, Classical palette):** measures a qubit at any point and stores the result in a classical bit c0–c9. The terminal **M** gates are unchanged.
- **Classically controlled gates:** right-click → **Run only if… → cₖ = 0 or 1**, shown as a badge. Conditions on whole registers are planned for later.
- **Reset** returns a qubit to |0⟩ mid-circuit.
- **An exact branch engine** follows every measurement outcome. Branches with the same classical record are merged, noise works inside branches, and mid-circuit readout error flips the recorded bit while the qubit collapses to the true outcome.
- **Results:**
  - the status and result line describe the branches;
  - a new **Branches** tab in the State Inspector shows each record's probability, purity and per-qubit Bloch vectors;
  - shots record the classical bits.
- **Tools that need a fixed unitary** (Simplify, Check equivalence and the noisy-success notes) explain why they don't apply to dynamic circuits.

### Examples and experiments
- **Quantum teleportation** (choose the state to send) and **Superdense coding** (choose two bits) examples.
  - **The teleportation check** runs your *current* circuit on ten inputs and requires q2 to equal the input in every branch. Removing a correction, or making one unconditional, fails it.
- **The Quantum Teleportation experiment** in Quantum Principles:
  - **the story:** Alice, Bob and a classical channel, in five steps;
  - **measurement results:** "unknown to Bob" (the average over all four) or a chosen or random result;
  - **the payoff:** it shows that Bob's qubit is random until the two bits arrive and that Alice's original is destroyed;
  - **Open in the circuit simulator** loads the matching circuit. It uses the same engine as the circuit.

### Files and OpenQASM
- **`.qscope` schema version 5** stores mid-circuit measurements, resets and conditions.
- **OpenQASM 2 export** gives each classical bit a one-bit register (`creg m0[1]`), so `if(m1==1) …` expresses single-bit conditions exactly.
- **OpenQASM 2 import** accepts measurements anywhere, `if` on one-bit registers and `reset`, packing every condition after its measurement. Ordinary programs still use the original importer.
- **PDF export** draws M→c boxes, resets and condition badges.

### Learn
- **Lectures:** *Mid-circuit measurement and classical bits*, *Classical control, feed-forward and reset*, *Quantum teleportation*, *Superdense coding*, *The deferred-measurement principle*, and *Measurement, information and no-cloning* (Quantum Principles).
- **Labs:** *Measure in the middle*, *Reset by feed-forward*, *Teleport a qubit*, *Send two bits with one qubit*, *Defer the measurement*.
- **Interactive quizzes:** click an option to get ✓ Correct with the explanation, or ✗ Not quite and try again. Show answer is still available.
- **Lab steps now tick off live in the app.** Previously they only updated after another click.
- **For course authors:**
  - new lab checks `measures`, `conditions`, `branches`, `record`, `teleports` and `settles`;
  - Try it links accept `cols`, `measures`, `resets` and `conditions`, and can open the `teleportation` view.

### Fixes
- **Windows dark mode:** the category tabs and drop-down lists were drawn in the system's light colors. QuantumScope now sets a complete theme palette, and "&" in group titles is shown correctly.
- **Math in table cells:** inline math using a bar inside a table cell fell back to plain text.
- **Ubuntu CI:** a theme test skips cleanly on machines without graphics libraries.

### Quality
- Automated tests: 1051 passing (912 in v0.6.0 + 139 new), plus 75 opt-in GUI tests. The 44-step editing replay is unchanged.

## v0.6.0 — Noise and mixed states

### Noise
- **Density-matrix simulation** (Qt-free, in `physics/noise.py`), used whenever noise is present. Without noise, the exact statevector simulation is unchanged.
- **Channels:** bit flip, phase flip, depolarizing (1- and 2-qubit), amplitude damping (T₁) and phase damping (T₂), plus readout error.
  - Depolarizing and damping use exact closed forms applied in place. 8 qubits simulate in about 0.1 s with every column stored; 10 qubits take a few seconds, final column only.
  - Each closed form is tested against its Kraus form.
- **Global noise (Noise button):**
  - presets Ideal, Gentle, Moderate and Very noisy, which are illustrative teaching levels;
  - separate rates for 1- and 2-qubit gate errors, damping, dephasing and readout;
  - optional **idle noise** on waiting qubits.
- **Noise elements:** channels placed on a wire from the new Noise palette, drawn as orange dashed boxes. They can be edited, moved, removed and undone, and never collide with gates, blocks or measurements.
- **Noise Explorer:** double-click a channel to see its equation, Kraus operators and exact Bloch-sphere map, with a live table of where |0⟩, |1⟩, |+⟩ and |+i⟩ end up, the numeric Kraus matrices, and **Try it**.

### Results under noise
- **Live view:** probability bars from ρ, **shrinking Bloch arrows**, and purity and fidelity with the ideal state at every step.
- **Shots** sample the noisy distribution, including readout error on the measured qubits.
- **State Inspector:** Probabilities and Density matrix tabs, reduced states from the noisy ρ, and noise statistics in the Circuit tab.
- **Algorithm checks:** PASS/FAIL still judges the ideal circuit, and a note reports the noisy success. For example, Grover with 3 qubits drops from 0.945 to 0.577 under Moderate noise.

### Files and exports
- Circuits with noise are saved as `.qscope` **schema version 4**. Older versions refuse these files rather than silently dropping the noise. Circuits without noise keep their schema.
- **Exports:** QASM export writes the ideal circuit with a comment noting that noise was not exported, and PDF export draws noise elements.

### Learn
- New lectures *Density matrices and mixed states* (Quantum Principles) and *Noise and decoherence* (Quantum Circuits), and the lab *Watch a Bell pair decohere*.
- **For course authors:** Try it links accept `noise=` (a preset) and `elements=`; lab checks add `noise`, `fidelity` and `purity`. See [LEARN.md](LEARN.md).

### Interface
- **The gate palette is a compact 3-column grid**, with noise channels in their own grid below it.

### Fixes
- **Dragging from the palettes:** the grid layout had switched the palettes to drop-only, so nothing could be dragged. A test now drives the real drag path.
- **Split objectives:** lesson objectives containing a ket (such as |−⟩) were cut in pieces at the separator. They are reworded, and a test prevents it happening again.

### Quality
- Automated tests: 912 passing (809 in v0.5.2 + 103 new), plus 62 opt-in GUI tests. The 44-step editing replay is unchanged.

## v0.5.2 — Learn & Settings

### Settings
- **A new Settings window**, titled "Settings", with sections for Appearance, Circuits, Graphics and Files. It has only a Close button, with no maximize or minimize, and a fixed size, so it can no longer fill the whole application window.
- **Appearance:**
  - theme: Dark, Light or **Follow system** (tracks the operating system's light/dark switch live);
  - **interface size** 100–175% for projecting in classrooms, applied after a restart.
- **Circuits:** default qubit count, default measurement shots, Bloch spheres beside wires, and **ask before clearing a circuit**.
- **Graphics:**
  - the **graphics device** (Automatic, Integrated or NVIDIA PRIME offloading on Linux) is now a saved setting, applied at start-up by QuantumScope itself, so `run_nvidia.sh` is optional and the packaged app gets the same choice;
  - the 3D volume rendering method and graphics information moved here from the Orbital Explorer panel.
- **Files:**
  - a default folder for saving and exporting, and a **Recent ▾** menu in the circuit tab;
  - **autosave with crash recovery:** if QuantumScope did not close normally, it offers to restore the circuit;
  - the probability report in PDFs can be set to Ask, Always or Never.
- **Restore defaults** resets every setting. **Restart now** appears when a change needs a restart; the restart drops the old session's graphics and size variables, so the new choice really applies.
- **Test isolation:** the test suite uses its own settings file and data folder, so it never reads or changes a user's settings.

### Circuit tab
- **QuantumScope now starts with an empty circuit** sized by Settings → Circuits. The Bell pair stays in Examples….
- **Toolbar cleanup:**
  - removed the leftover **Bell example** button and an orphan "Gate" label left from the old placement controls (along with the hidden, unused controls behind it);
  - Open, Save, Open recent, QASM import/export and PDF export are grouped under a **File** menu.
- **Gate angle units:** degrees or radians, set in Settings.
  - **New-gate angle fields** show the chosen unit.
  - **The gate-edit dialog** reads plain numbers in that unit, while expressions with pi (such as `pi/4`) are always radians.
- **Bit order in labels:** |q0 q1 …⟩ (textbook) or |… q1 q0⟩ (Qiskit). This is display only, applied everywhere basis states are written. Algorithm parameters and CSV data always list q0 first.
- **Amplitudes:** exact forms (1/√2) or decimals, with 2–8 decimal places.
- **Tools → Simplify circuit…:**
  - **What it does:** cancels neighboring inverse pairs (H·H, X·X, CX·CX, S·S†, T·T†, …), merges consecutive rotations about the same axis (including CP), and removes rotations that equal the identity.
  - **Preview:** shows every change before applying.
  - **Safety check:** every result is verified against the full unitary, and global phases are reported honestly. Gates inside blocks are never changed, and Undo restores the original.
- **Tools → Check equivalence with a saved circuit…:** compares two circuits' unitaries up to global phase. A new vectorized unitary calculation handles 10 qubits in under a second.

### Learn
- **A 📖 Learn button** on each area's tab bar opens the Learn window. It has a contents tree, search, Back/Forward, text size, and **Export PDF** for printable handouts.
- **Lectures:**
  - learning objectives, explanations, and crisp equations pre-rendered for both themes (matrices included);
  - **▶ Try it** links that set up the matching circuit, algorithm, example or view;
  - **Check your understanding** questions with reveal-able answers.
- **Labs:** guided steps that turn **✓ Done** automatically as the student's circuit meets each goal, with a progress counter. Once a later step passes, earlier ones stay done.
- **My course:** a folder of a teacher's own Markdown lessons, which can use the same links, questions and lab checks. [LEARN.md](LEARN.md) documents the format.
- **Content: 21 lectures and 6 labs.**
  - **Quantum Circuits:** qubits and bit order; single-qubit gates; multi-qubit gates and tensor products; entanglement in circuits; measurement; reversible logic; phase kickback and oracles; Grover search; the QFT; circuit cost (depth, T-count, Clifford). Labs: Bell pair, GHZ state, phase kickback, Grover by hand, half adder, and the QFT of a basis state.
  - **Quantum Principles:** superposition and the Bloch sphere; measurement and the Born rule; double-slit interference; entanglement and Bell states; global and relative phase.
  - **Hydrogen:** the Schrödinger equation and the reduced mass; quantum numbers and orbitals; probability density and radial probability; energy levels and spectra; superposition and quantum beats; what the model leaves out (spin, fine structure, Lamb shift, hyperfine).
  - **Further reading** is left for the course author to add in the Markdown files.
- **Built-in content is tested:**
  - every equation has an up-to-date image;
  - every Try it link works;
  - every question has exactly one correct answer;
  - every lab has a scripted solution that completes it;
  - every quoted number (hydrogen energies, spectral lines, beat periods, radii, Grover probabilities) is checked against the app's physics.

  The packaged-app self-test also checks that the lessons ship with the app.
- **Fixes:**
  - **QASM Converter tab:** it was always open at start-up, and its close button did nothing. It now opens from **+ → QASM Converter**, closes normally, and keeps its text when reopened.
  - **First experiment tab:** the first experiment opened in an area (for example the Double-Slit Experiment in Quantum Principles) could not be closed. Only the Hydrogen Explorer and Gate Circuit Simulator are permanent now.
  - **tree views** were unthemed (white) in the dark theme;
  - **disabled buttons** in the light theme used the dark theme's colors.

### Quality
- Automated tests: 809 passing (577 existing + 232 new), plus 36 opt-in GUI tests. The 44-step editing replay is unchanged.
- The packaged-app self-test also checks that all 27 lessons and their equation images ship with the app.

## v0.5.1 — Algorithms and examples

- **Blocks:** named groups of real gates that act as one operation.
  - **Collapsed**, a block is a labeled box.
  - **Expanded** (double-click), it shows its gates inside a light dashed outline with a Collapse chip.
  - **Locked:** contents can't be edited, and a block reserves its whole wire span.
  - **Right-click actions:** Expand/Collapse, Edit block… (rebuilds with new parameters), Show contents… (gate list, and the matrix for blocks of up to 3 qubits), Ungroup (make the gates editable) and Remove. All are covered by Undo.
  - **Same physics:** simulation is identical collapsed or expanded, and the State Inspector always counts the real gates inside.
- **Algorithms menu:** Deutsch, Deutsch–Jozsa, Bernstein–Vazirani, Grover search and the quantum Fourier transform (with QFT†).
  - Oracles, diffusion and QFT are blocks.
  - Ancillas start in |−⟩, and Grover uses Toffoli-based multi-controlled Z with work qubits that return to |0⟩.
  - Each algorithm has a **specification check on the current circuit**: constant versus balanced, the hidden string s, Grover's sin²((2k+1)θ) for the oracles actually present, and QFT against the DFT matrix.
- **New reversible examples** with truth-table checks: full adder, 2-bit comparator, controlled increment, Toffoli as AND, and Fredkin multiplexer. Their inputs are set with initial states.
- **New gate CP(λ)** (controlled phase), across the palette, simulator, Gate Explorer, QASM (`cp`, and `cu1` on import), PDF and Clifford classification.
- **Gate Explorer:**
  - a **Worked identity** tab (for example H Z H = X, step by step on every basis state);
  - a **Try it in the circuit** button, which uses starting states that make the gate's effect visible.
- **Files:**
  - circuits with blocks save as `.qscope` **version 3**, which older versions refuse instead of misreading; other circuits keep their format;
  - QASM export writes blocks as their gates, marked by `// block:` comments;
  - PDF export draws blocks.
- **Fixes:**
  - dialogs (Gate Explorer, parameter and custom-state dialogs) were unreadable in the dark theme when the operating system used a light color scheme; they now have a dark style;
  - a multi-qubit gate's angle was lost while its placement was pending, so CP would have become CP(0);
  - the circuit status line now counts the gates inside blocks.
- **New user guide:** [ALGORITHMS.md](ALGORITHMS.md).
- **New Qt-free modules:**
  - `physics/blocks.py`;
  - `physics/algorithms.py` (library, block builders, specifications);
  - `gui/parameter_dialog.py`.
- Automated tests: 577 passing (468 existing + 109 new), plus 27 opt-in GUI tests. The 44-step editing replay from v0.4.3 is unchanged.

## v0.5.0 — See inside the state

- **Initial states:**
  - every qubit can start in |0⟩ (the default), |1⟩, |+⟩, |−⟩, |+i⟩, |−i⟩, or a custom state cos(θ/2)|0⟩ + e^{iφ} sin(θ/2)|1⟩, chosen by clicking the qubit's wire label;
  - the custom dialog accepts expressions like `pi/3` and shows a live Bloch preview;
  - initial states are covered by Undo/Redo, and Clear and the examples reset them.
- **State Inspector window** (State Inspector… button), which follows the step slider, with a Freeze toggle:
  - **Amplitudes:** exact amplitudes, magnitudes, probabilities and phases (as multiples of π), phase color swatches, and filtering and sorting.
  - **Statevector:** Dirac notation, with Copy as text, Copy as LaTeX, Copy as CSV and Save CSV.
  - **Reduced state:** the reduced density matrix of up to 3 qubits (table and heatmap), purity, entanglement entropy in bits, a pure/mixed verdict, and the single-qubit Bloch vector.
  - **Circuit:** gate counts; single-, two- and three-qubit counts; T-count; Clifford and non-Clifford counts; parameterized gates; drawn depth versus minimum depth.
  - An optional "remove global phase" view.
- **Files:**
  - `.qscope` files that use initial states are saved as format version 2, so older versions refuse them instead of silently simulating from |0⟩; all-|0⟩ files stay version 1;
  - OpenQASM export writes exact preparation gates (x, h, s, sdg or u3);
  - PDF export labels each wire with its initial state;
  - the converter reports when it writes preparation gates.
- **Self-test:** the packaged-app self-test now also renders the State Inspector.
- **Hydrogen Dynamics 2D and 3D:**
  - **3D Reset camera fixed.** It did nothing: Qt's `clicked(checked)` argument reached PyVista as `render=False`, and a plain reset also kept the current rotation. It now restores the isometric view, centered and fitted.
  - **New 3D view buttons:** Top (xy), Front (xz) and Side (yz).
  - **Quick-value buttons** (Max, Min and common presets) for probability, phase, grid resolution, cloud visibility and GIF settings.
  - **Fit to states** for the half-width, which contains 99.5% of each state's probability; a hint appears when the view clips the states.
  - **Rebuilds wait** until you finish typing.
  - **Smoother 3D playback,** because the volume is updated in place.
  - **2D:** a Reset view button, axes named after the plane, and a display-only Contrast option (Linear, Enhanced √, Logarithmic).
  - Removed the stale "(v0.2.0)" from the 3D window title.
- **New user guide:** [STATE_INSPECTOR.md](STATE_INSPECTOR.md).
- **New Qt-free modules:**
  - `physics/initial_states.py`;
  - `physics/state_analysis.py` (partial trace, purity, entropy, Dirac/LaTeX/CSV, Clifford test, depth and counts).
- Automated tests: 468 passing (393 existing + 75 new), plus 16 opt-in GUI tests.

## v0.4.3 — Circuit editor model

An internal release with no intended change to how QuantumScope looks or behaves; it prepares the editor for the v0.5 education features.

- **Editor logic moved into a Qt-free `CircuitModel`** (`src/quantumscope/editor/circuit_model.py`). Placement, multi-qubit anchoring, moving, column insertion and deletion, terminal-measurement rules, undo/redo, examples, verification and per-column simulation now live there. The circuit workspace widget only turns input into model calls and draws the result. The widget shrank from 884 to 788 lines.
- **40 new unit tests** cover every editing rule without a display. An opt-in GUI test file checks the widget delegates correctly; run it with `QUANTUMSCOPE_GUI_TESTS=1`.
- **Verified unchanged behavior:**
  - A scripted 44-step editing session gives the same gates, measurements, columns, status messages and verification results as v0.4.2.
  - The rendered workspace is pixel-identical in both themes.
- **Small fixes that fell out of the refactor:**
  - right-clicking any wire of a multi-qubit gate (not only its anchor row) now offers Remove;
  - loading a circuit or undoing now cancels a half-finished multi-qubit placement;
  - empty trailing columns shrink after reducing the qubit count removes gates;
  - removing nothing no longer adds an empty undo step.
- Automated tests: 393 passing (353 existing + 40 new), plus 4 opt-in GUI tests.

## v0.4.2 — Light Mode, Gate Explorer and release checks

- **Light Mode circuit canvas is readable.** Gate symbols, control dots, targets, measurement boxes, Bloch glyphs, probability charts, PASS/FAIL results and step highlights now use theme-aware colors instead of dark-theme colors painted onto the light canvas. Control dots went from 1.08:1 to 12.3:1 contrast. Every color pairing meets WCAG 2.1 AA (4.5:1 for text, 3:1 for graphics), enforced by automated tests. Switching themes recolors the circuit workspace immediately.
- Fixed light-grey empty header areas in the dark circuit table.
- Self-contained visualization panels (Bloch scene, entanglement, double slit, dynamics plots) intentionally keep their dark display background in both themes.
- **Gate Explorer:**
  - full matrices for every gate, including 4×4 and 8×8 matrices for multi-qubit gates, with basis-state labels;
  - readable exact amplitudes (1/√2, i/2, …);
  - a Properties section covering unitary, Hermitian, Clifford, inverse, eigenvalues, the Bloch vector of the gate applied to |0⟩, a useful identity and related gates;
  - angle fields that accept exact expressions such as `pi/2`, plus φ and λ controls for U;
  - fixed the "Overview _matrix" tab label.
  - Every displayed identity and inverse is verified numerically by tests.
- **Packaged-app launch check:** `quantumscope --self-test` starts Qt, the 3D libraries and the circuit workspace without opening a window. The release workflow now runs it on the packaged Linux, Windows and macOS apps before building installers.
- **CI:** the test workflow now also runs on macOS.
- **Shell scripts are executable** in the repository, so `./install_and_run.sh` and `./run.sh` work after a fresh clone without `chmod`.
- Development notes moved from the repository root to `docs/dev-notes/`.
- Automated tests: 353 passing (127 existing + 226 new).

## v0.4.1 — Circuit file integrity and import hardening

- **Circuit layout is preserved on save and load.** `.qscope` files now store each operation's column, the terminal-measurement column and the total column count, so parallel gates, intentional empty columns and spare trailing columns survive a save/reopen. The new fields are optional: v0.4.0 can still open v0.4.1 files (ignoring the layout), and older files open in v0.4.1 with simultaneous gates packed into shared columns.
- **QASM import packs gates into columns** instead of placing one gate per column. Packing only reorders gates that act on disjoint qubits, so the simulated circuit is unchanged.
- **`barrier` statements are no longer dropped silently.** They now separate columns on import, and the editor and converter report that barriers are not saved or exported.
- **Safer QASM angle parsing.** The QASM reader now uses the same safe expression parser as the gate-parameter dialog (no `eval`), with limits on length, nesting and exponent size. Crafted angles such as `9**9**9**9` are rejected instead of freezing the application.
- **Example circuits keep their verification after edits.** Editing the half adder, half subtractor or ripple-carry adder now re-runs the original specification and shows FAIL rows, instead of discarding the check. Undo/redo restores the matching example state.
- Built-in examples moved to `physics/circuit_examples.py` and layout logic to `physics/circuit_layout.py` (Qt-free, unit-tested).
- Removed accidentally tracked `src/quantumscope.egg-info/` build metadata.
- Automated tests: 127 passing (95 existing + 32 new).

## v0.2.0 — Interactive principles update (post-release candidate)

- Added **Quantum Superposition**: pure spin-½ state, Bloch-sphere schematic, selectable measurement basis, Born probabilities, collapse demonstration, and repeated preparations.
- Added **Quantum Entanglement**: animated electron-spin singlet schematic, independent Alice/Bob measurement controls, joint probabilities, simulated correlation statistics, and ideal CHSH reference.
- Added optional ideal which-path marking at the slits in the Double-Slit Experiment. The probability curve and detector samples now switch between coherent fringes and an incoherent single-slit envelope.
- Kept all original Hydrogen Explorer, 2D/3D dynamics, tab workspace, export support, and installer build configuration.
- Distinguish illustrations and ideal-model statistical predictions from real trajectories, real hardware data, and physical signaling.

## v0.2.0 — workspace redesign (stable-release candidate)

- Introduced a cohesive modern dark Qt application theme and a top experiment-launch bar.
- Replaced separate modal experiment windows with closable, state-preserving workspace tabs for Hydrogen Dynamics 2D, Hydrogen Dynamics 3D, and Double-Slit Experiment.
- Kept the Hydrogen Explorer anchored as the primary tab and preserved all physics modules, experiment controls, plots, and exports.
- Refreshed About details and linked directly to https://github.com/Onimee58/QuantumScope.
- Updated documentation to reflect the full v0.2.0 scope rather than the older Hydrogen-only release.
- Physics tests: 40 passing. GUI requires desktop verification with PySide6/VTK.

## 0.2.0 — First stable release candidate

- Double-Slit Experiment: normalized Fraunhofer interference with sampled detection events.
- Added an animated apparatus schematic (source, double-slit barrier, and detector) with detector marks tied to sampled events; optional animation toggle.
- Retained the original probability-density plot, histogram, parameter controls, and CSV export.
- Consistent tag-based artifact filenames and source version 0.2.0.
- Existing hydrogen explorer and 2D/3D dynamics preserved.
- First labeled stable release, subject to packaged GUI verification on Windows and Linux.

## v0.1.7 — 3D Hydrogen Dynamics and layout repair

- Added 3D dynamics experiment with time evolution, density cloud, isosurface, and 3D GIF export.
- Fixed main sidebar startup width (previously hard-coded 330 px); increased minimum width and disabled horizontal overflow.
- Kept v0.1.6 2D dynamics and Windows/Linux workflows.
- Requires real GUI validation on both platforms before tagging.

## v0.1.6 — Hydrogen Dynamics
- New **Experiments → Hydrogen Dynamics** interactive 2D cross-section of exact two-state hydrogen superpositions.
- Physical femtosecond time evolution, play/pause, time scrubber, amplitudes, relative phase, slice controls and export.
- Preserves v0.1.5 comparison, Linux NVIDIA PRIME and Windows/Linux build workflow.

# Changelog

## v0.1.5 — Visualization refinement
- Resizable sidebar and full-height layout.
- Collapsible radial probability plot and scientific information.
- Camera synchronization between comparison viewers, with optional toggle.
- Orbital labels over both viewers.
- Mask numerically undefined phases near nodal points; cyclic phase colormap retained.
- Windows/Linux build workflow preserved; NVIDIA PRIME launcher preserved.

## 0.1.4 — Real orbitals and comparison

- Introduced real tesseral hydrogen orbital basis with unit-normalized cosine/sine combinations.
- Added optional dual 3D orbital viewer and state selectors.
- Added 1–4× PNG screenshot export scale and extended NPZ basis metadata.
- Updated version and portable cross-platform PyInstaller action; avoided broad pyqtgraph collection on headless CI.
- Added numerical checks for real-orbital angular nodes and density identities.

## 0.1.3 — Cross-platform source release
- Added Windows batch installer and launcher using an isolated Python virtual environment.
- Added Windows setup and graphics selection documentation.
- Extended CI physics tests to Windows.
- Kept existing Linux graphics configurations and About dialog unchanged.
- No claim of a compiled Windows executable or Windows GPU validation yet.

## v0.1.1 — About dialog enhancement

- GlassBalance-inspired About panel, local portrait selection, custom logo, maintainer credits and configurable GitHub link.
- Existing hydrogen rendering and scientific computation remain unchanged.

# Changelog

## 0.1.1 — GUI and orbital visualization fixes

- Added Help → About QuantumScope dialog with project details, developer attribution, license, and website.
- Probability-aware camera positioning and reset camera button.
- Density contrast enhancement without changing computed or exported density.
- Scrollable control panel and more legible scientific readouts.
- Automatic radial plot axis framing.
- Selectable VTK smart/GPU/CPU volume mapper, CPU fallback for Auto.
- Optional automatic rerender on controls change.
- More accurate explanations of probability capture and visualization transforms.

## 0.1.0 — Hydrogen Explorer

- Initial hydrogen wavefunction engine and interactive desktop application.

## 0.1.2
- Add phase-colored probability-enclosing isosurfaces (complex wavefunction phase).
- Add standard camera orientations, zoom, optional physical coordinate bounds.
- Add in-application VTK OpenGL capability diagnostics.
- Add NVIDIA PRIME / GLX and system-default launch scripts.
- Preserve About dialog for future revision.

### v0.1.4 UI/graphics hotfix (post-release candidate)
- Sidebar extends to the bottom of the application; radial plot is compact and placed below the viewers only.
- Phase colors on probability-enclosing surfaces now use trilinear interpolation of the complex wavefunction at mesh vertices instead of nearest-voxel cell sampling.
- Clarified VTK volume mapper versus physical GPU choice.
- Added a Linux restart-on-NVIDIA action using the previously verified XCB/GLX PRIME environment; the active GPU is reported by graphics diagnostics.
- Scientific calculations and Windows/Linux packaging workflows retained.

### v0.2.0 — Installer and branding preparation
- Adopted the Modern Q / Wave icon in the main window, About dialog, and native application metadata.
- Added reusable SVG, PNG, and ICO branding resources.
- Added GitHub Actions builds for Ubuntu/Debian `.deb` and Windows Inno Setup `Setup.exe` installers.
- Kept existing tabbed experiment UI and numerical physics modules unchanged.

### v0.2.0 — stable UI polish (pre-release)
- Replaced the legacy Experiments/Help menu bar and three quick-launch buttons with a unified New Experiment dropdown.
- Added the same experiment catalog to the tab-bar + control, organized for future expansion.
- Applied the official QuantumScope Q/Wave icon in the workspace header and Hydrogen Explorer tab.
- Added header Settings and About buttons, including a persistent dark/light interface preference.
- Kept native window decoration, the existing dock/taskbar application icon, and the .deb/Windows installer configurations.

### Quantum principles interaction refinements (v0.2.0 development update)
- Bloch sphere uses a drag-rotatable 3D orthographic projection with three great circles and state vector.
- Superposition state and measurement angles, plus Alice/Bob axes, have synchronized sliders and degree boxes.
- Entanglement electrons are clickable to measure after separation; changing measurement angles no longer restarts their travel animation.
- Previous shot/correlation statistics clear on parameter changes to avoid confusion with the current theoretical prediction.
- After one electron is measured, changing an axis requires preparing a new pair, avoiding mixing incompatible measurement settings.

### Interactive entanglement preparation station (v0.2.0 development update)
- Entanglement demonstration now begins with separately adjustable Alice and Bob spin states (polar angle and phase for each).
- Animated electron symbols move into a schematic H(A) then CNOT(A,B) preparation station and emerge as a joint two-qubit state.
- Displays input product-state amplitudes, output joint-state amplitudes, and pure-state concurrence (0–1).
- Default |up,up> input produces maximally entangled Bell |Phi+>; other inputs can produce partially entangled or separable states.
- After preparation, each electron is clickable for its own local projective spin measurement; sequential measurements condition the same joint state.
- Changing measurement axes does not restart electron motion. Altering initial preparation requires reset and preparation of a new pair.
- Batch statistics use the generated joint state and current measurement axes, not an assumed singlet for every input.

### Quantum Circuit Workspace update (v0.2.0 development)

- Organized the interface into three top-level workspaces: Hydrogen, Quantum Principles, and Quantum Circuits. Experiments retain their individual tabs within each workspace.
- Added an ideal statevector quantum gate simulator with an editor, gate palette, two-qubit controls, Bloch previews of reduced single-qubit states at every step, sample measurement counts, and OpenQASM 2 subset import/export.
- Interactive circuit limit: 10 qubits; explicitly reject unsupported OpenQASM operations.
