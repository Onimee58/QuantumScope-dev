"""Console entry point: python -m quantumscope or quantumscope."""
import sys


def _self_test():
    """Start the packaged application's core without showing a window.

    Used by CI after packaging: it checks that Qt (including its platform
    plugin), the 3D (OpenGL) libraries and the circuit workspace load
    and simulate inside the frozen bundle. The OpenGL main window itself is
    not created, because CI machines have no GPU. Returns 0 on success.
    A report is written to $QUANTUMSCOPE_SELF_TEST_REPORT when set, since
    windowed builds on Windows have no console output.
    """
    import os
    import traceback
    lines = []
    try:
        from quantumscope import __version__
        lines.append(f"QuantumScope {__version__} self-test")
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv[:1])
        lines.append(f"Qt platform: {app.platformName()}")
        from quantumscope.licensing.check import key_is_set   # v1.0.0: a release must be able to check licenses
        if not key_is_set():
            raise RuntimeError("Built without the license key: run tools/licenses.py setup and commit license_key.py")
        lines.append("License key: present")
        from quantumscope.visualization.glplatform import opengl_environment
        opengl_environment(app)                       # before OpenGL is imported (v0.9.11 fix)
        if sys.platform.startswith("linux"):          # both Linux interfaces must be bundled
            import importlib
            for name in ("OpenGL.platform.glx", "OpenGL.platform.egl"):
                importlib.import_module(name)
            lines.append(f"OpenGL interfaces bundled: GLX and EGL; using {os.environ.get('PYOPENGL_PLATFORM', 'default')}")
        # The 3-D views (v0.9.11: OpenGL through pyqtgraph). PyOpenGL loads its platform support
        # on import; a contour, a lit mesh and a volume must build (drawing needs a GPU, which CI lacks).
        import numpy as np
        import pyqtgraph.opengl  # noqa: F401
        from OpenGL import GL  # noqa: F401
        from quantumscope.visualization import gl3d
        x = np.linspace(-1, 1, 12)
        field = x[:, None, None] ** 2 + x[None, :, None] ** 2 + x[None, None, :] ** 2
        verts, faces = gl3d.contour(field, 0.5, -1.0, float(x[1] - x[0]))
        if len(faces) == 0:
            raise RuntimeError("3-D contour produced nothing")
        gl3d.Mesh(vertexes=verts, faces=faces).vertexNormals()
        gl3d.lut("phase"), gl3d.lut("viridis")                        # colour maps ship with pyqtgraph
        pyqtgraph.opengl.GLVolumeItem(np.zeros((4, 4, 4, 4), np.uint8))
        lines.append(f"3-D: OpenGL module loads; contour ({len(faces)} triangles), mesh and volume build")
        import quantumscope.gui.main_window  # noqa: F401  (imports every workspace module)
        from quantumscope.gui.circuit_workspace import CircuitWorkspace
        from quantumscope.physics.circuit_examples import EXAMPLE_NAMES
        workspace = CircuitWorkspace()
        workspace.load_example(1 + EXAMPLE_NAMES.index("Half adder (a=1,b=1)"))
        verdicts = [workspace.verify_table.item(r, 3).text() for r in range(workspace.verify_table.rowCount())]
        if not verdicts or not all("PASS" in v for v in verdicts):
            raise RuntimeError(f"Example verification failed: {verdicts}")
        lines.append(f"Circuit workspace: half adder {len(verdicts)}/{len(verdicts)} PASS")
        from quantumscope.gui.state_inspector import StateInspector
        inspector = StateInspector(workspace)
        inspector.refresh()
        if "column" not in inspector.where.text() or inspector.amp_table.rowCount() == 0:
            raise RuntimeError("State Inspector did not render the state")
        lines.append(f"State Inspector: {inspector.amp_table.rowCount()} amplitude row(s) rendered")
        workspace.load_library("grover", {"n": 3, "marked": "101", "iterations": -1})
        rows, _ = workspace.model.verification()
        if not rows or rows[0].passed is not True or len(workspace.model.blocks) != 4:
            raise RuntimeError("Algorithm library did not build Grover correctly")
        lines.append(f"Algorithm library: Grover {rows[0].output_label} (PASS)")
        # Lessons and their equation images must be inside the installed package.
        import os
        from quantumscope.learn.lessons import builtin_lessons, content_folder
        from quantumscope.learn.equations import equations_in, image_name
        lessons = builtin_lessons()
        missing = [name for lesson in lessons for tex, kind in equations_in(lesson.body)
                   for name in [image_name(tex, kind, "dark")]
                   if not os.path.exists(os.path.join(content_folder(), "eq", name))]
        if not lessons or missing:
            raise RuntimeError(f"Learn content incomplete: {len(lessons)} lessons, {len(missing)} missing equations")
        lines.append(f"Learn: {len(lessons)} lessons, all equation images present")
        # The glossary and the splash's logo must ship too (a missing glossary only hides links).
        from quantumscope.learn import glossary
        from importlib.resources import files
        terms = glossary.builtin().terms
        if len(terms) < 50 or not files("quantumscope").joinpath("assets/quantumscope-mark.svg").is_file():
            raise RuntimeError(f"Glossary or splash logo missing ({len(terms)} terms)")
        lines.append(f"Glossary: {len(terms)} terms; splash logo present")
        guide = files("quantumscope").joinpath("assets/QuantumScope-User-Guide.pdf")
        if not guide.is_file() or guide.read_bytes()[:5] != b"%PDF-":
            raise RuntimeError("User guide (assets/QuantumScope-User-Guide.pdf) missing")
        lines.append("User guide: present")
        from quantumscope.ml import datasets
        sizes = {name: len(datasets.load(name).y) for name in datasets.BUILTIN}
        if sizes != {'iris': 150, 'wine': 178, 'breast_cancer': 569, 'digits': 1797, 'mnist': 2000,
                     'fashion_mnist': 2000, 'penguins': 344, 'seeds': 210, 'glass': 214}:      # v0.9.3: + 4
            raise RuntimeError(f"Bundled datasets incomplete: {sizes}")
        lines.append(f"Datasets: {len(sizes)} bundled ({sum(sizes.values())} samples)")
        from quantumscope import resources
        if resources.snapshot().total <= 0:                      # psutil bundled (the memory meter needs it)
            raise RuntimeError("Memory reading failed")
        # v0.9.7: installers carry QuantumScope's modules as native code, not readable bytecode
        from importlib.machinery import EXTENSION_SUFFIXES
        ours = [m for name, m in sorted(sys.modules.items()) if name.startswith("quantumscope.")
                and getattr(m, "__file__", None) and not m.__file__.endswith(("__init__.py", "__init__.pyc"))]
        python = [m.__name__ for m in ours if not m.__file__.endswith(tuple(EXTENSION_SUFFIXES))]
        if python and os.environ.get("QUANTUMSCOPE_EXPECT_NATIVE") == "1":
            raise RuntimeError(f"Not compiled to native code: {python}")
        lines.append(f"Code: {len(ours) - len(python)} of {len(ours)} loaded modules native")
        lines.append("RESULT: PASS")
        status = 0
    except Exception:
        lines.append(traceback.format_exc())
        lines.append("RESULT: FAIL")
        status = 1
    report = "\n".join(lines)
    print(report)
    path = os.environ.get("QUANTUMSCOPE_SELF_TEST_REPORT")
    if path:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(report + "\n")
    return status


def main():
    if "--version" in sys.argv:
        from quantumscope import __version__
        print(f"QuantumScope {__version__}")
        return 0
    if "--self-test" in sys.argv:
        return _self_test()
    # Graphics device and interface size must be set before Qt or OpenGL start.
    from quantumscope.gui.preferences import apply_startup_environment
    apply_startup_environment()
    from PySide6.QtCore import QCoreApplication, Qt
    from PySide6.QtWidgets import QApplication
    # Every 3-D view, in any window, shares OpenGL resources: pyqtgraph compiles each shader once (v0.9.11).
    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)

    app = QApplication.instance() or QApplication(sys.argv)
    # PyOpenGL must use the same windowing interface as Qt (GLX or EGL), before anything imports it.
    from quantumscope.visualization.glplatform import opengl_environment
    opengl_environment(app)
    # The splash appears before the slow imports below (the 3-D libraries), so it covers the wait.
    from quantumscope.gui.splash import show_splash
    splash = show_splash(app)
    from quantumscope.gui.main_window import MainWindow
    from PySide6.QtGui import QIcon
    from importlib.resources import files
    app.setApplicationName("QuantumScope")
    app.setOrganizationName("QuantumScope")
    app.setWindowIcon(QIcon(str(files("quantumscope").joinpath("assets/quantumscope.png"))))
    app.setStyle("Fusion")
    from quantumscope.gui import preferences as prefs
    from quantumscope.gui.theme import apply_theme
    apply_theme(prefs.get("appearance/theme"))
    from quantumscope.gui.report_dialog import enable_crash_log
    enable_crash_log()                                   # v1.1.1: a crash in compiled code leaves a trace
    from quantumscope.gui.license_dialog import open_main_window
    window = open_main_window(app, splash, MainWindow)   # v1.0.0: only with a valid license
    if window is None:
        return 0
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
