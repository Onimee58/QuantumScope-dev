"""Build QuantumScope's user guide: screenshots of the real app, then the PDF (authors only).

Usage:  python tools/make_user_guide.py            # screenshots + PDF
        python tools/make_user_guide.py --pdf-only # rebuild the PDF from the existing screenshots

Writes docs/images/*.png and src/quantumscope/assets/QuantumScope-User-Guide.pdf from
docs/user-guide.md. On a normal desktop the Hydrogen screenshot includes the live 3-D view; with
QT_QPA_PLATFORM=offscreen (no display) it shows the Explorer's controls and chart instead, since
software 3-D rendering is unreliable there.
"""
import os
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(ROOT, 'src'))
DOCS = os.path.join(ROOT, 'docs')
IMAGES = os.path.join(DOCS, 'images')
PDF = os.path.join(ROOT, 'src', 'quantumscope', 'assets', 'QuantumScope-User-Guide.pdf')
OFFSCREEN = os.environ.get('QT_QPA_PLATFORM') == 'offscreen'


def settle(app, seconds=0.0):
    end = time.time() + seconds
    while True:
        app.processEvents()
        if time.time() >= end:
            break
        time.sleep(0.01)


def save(widget, name, crop=None, scale=1.0):
    from PySide6.QtCore import Qt
    image = widget.grab().toImage()
    if crop is not None:
        image = image.copy(*crop)
    if scale != 1.0:
        image = image.scaledToWidth(int(image.width() * scale), Qt.TransformationMode.SmoothTransformation)
    os.makedirs(IMAGES, exist_ok=True)
    image.save(os.path.join(IMAGES, name))
    print('  ', name, image.width(), 'x', image.height())


def screenshots():
    import pyvista as pv
    from PySide6.QtWidgets import QApplication, QWidget
    os.environ.setdefault('QUANTUMSCOPE_SETTINGS_FILE', os.path.join(DOCS, '.guide-settings.ini'))
    os.environ.setdefault('QUANTUMSCOPE_DATA_DIR', os.path.join(DOCS, '.guide-data'))
    app = QApplication.instance() or QApplication([])
    app.setStyle('Fusion')
    import quantumscope.gui.main_window as M
    if OFFSCREEN:                                    # no display: a stand-in for the 3-D widget
        pv.OFF_SCREEN = True

        class Interactor(QWidget):
            def __init__(self, parent=None, *a, **k):
                super().__init__(parent)
                self.__dict__['_p'] = pv.Plotter(off_screen=True, window_size=(300, 300))

            def __getattr__(self, name):
                return getattr(self.__dict__['_p'], name)

            def render(self, *a, **k):
                return self.__dict__['_p'].render()
        M.QtInteractor = Interactor

        class DecisionInteractor(Interactor):                # the 3-D decision view: larger, picking accepted
            def __init__(self, parent=None, *a, **k):
                QWidget.__init__(self, parent)
                self.__dict__['_p'] = pv.Plotter(off_screen=True, window_size=(960, 640))

            def enable_point_picking(self, *a, **k):
                pass
        import quantumscope.gui.decision3d as D3
        D3.make_plotter = lambda parent: DecisionInteractor(parent)
        from PySide6.QtWidgets import QMessageBox                # no one can click a message box here:

        def stop(title):                                          # fail loudly instead of waiting forever
            def show(*args, **kwargs):
                raise RuntimeError(f'Unexpected {title} while making the guide: {args[2] if len(args) > 2 else args}')
            return staticmethod(show)
        for kind in ('warning', 'information', 'critical'):
            setattr(QMessageBox, kind, stop(kind))
    from quantumscope.gui.theme import apply_theme
    apply_theme('dark')
    w = M.MainWindow()
    w.resize(1480, 920)
    w.show()
    settle(app, 0.5)

    # Main window and Hydrogen
    w.n.setValue(3)
    w.l.setCurrentIndex(w.l.findText('2'))
    settle(app, 0.5)
    w.refresh()
    settle(app, 1.0)
    if OFFSCREEN:
        panel = w.n.parentWidget().parentWidget()
        while panel.parentWidget() is not None and panel.width() < 300:
            panel = panel.parentWidget()
        x = panel.mapTo(w, panel.rect().topLeft()).x()
        save(w, 'hydrogen-controls.png', crop=(0, 0, x + panel.width() + 6, w.height()), scale=0.8)
    else:
        save(w, 'hydrogen-controls.png', scale=0.75)

    # The window tour: the Quantum Principles area with Double-Slit (it renders everywhere)
    w._launch_double_slit()
    double = w._open_experiments['double_slit']
    double.wavelength.setValue(650)
    double.speed.setCurrentIndex(2)
    double.batch.setValue(6000)
    double.add.click()
    settle(app, 0.6)
    save(w, 'main-window.png', scale=0.75)

    # Quantum Principles
    from quantumscope.gui.quantum_principles import SuperpositionDialog
    from quantumscope.gui.double_slit_dialog import DoubleSlitDialog
    from quantumscope.gui.entanglement_experiment import EntanglementDialog
    from quantumscope.gui.teleportation_experiment import TeleportationDialog
    d = SuperpositionDialog()
    d.resize(1300, 760)
    d.show()
    d._preset(60, 30)
    d.axis.setValue(30)
    d.speed.setCurrentIndex(2)
    d.sample.click()
    settle(app, 0.8)
    save(d, 'superposition.png', scale=0.75)
    d = DoubleSlitDialog()
    d.resize(1300, 800)
    d.show()
    d.wavelength.setValue(532)
    d.speed.setCurrentIndex(2)
    d.batch.setValue(8000)
    d.add.click()
    settle(app, 0.5)
    save(d, 'double-slit.png', scale=0.75)
    d = EntanglementDialog()
    d.resize(1400, 860)
    d.show()
    d.speed.setCurrentIndex(2)
    d.count.setValue(2000)
    d.run_bell_test()
    d.bob_axis[1].setValue(30)
    d.send_many()
    settle(app, 0.5)
    save(d, 'entanglement.png', scale=0.7)
    d = TeleportationDialog()
    d.resize(1400, 880)
    d.show()
    d.result.setCurrentIndex(d.result.findData('11'))
    for step in range(1, 5):
        d.go(step, animate=False)
    settle(app, 0.5)
    save(d, 'teleportation.png', scale=0.7)

    # Quantum Circuits
    c = w.circuit_widget
    w._launch_circuits()
    c.load_library('teleportation', {'input': '+'})
    c.verify_circuit()
    settle(app, 0.5)
    save(c, 'circuit-tab.png', scale=0.72)
    c.load_library('qaoa', {'graph': 'ring6', 'layers': 2})
    settle(app, 0.5)
    save(c.param_panel, 'parameters.png', scale=0.8)              # the panel itself (the page may be scrolled)
    c.example()                                         # the Bell pair (as Examples… → Bell pair)
    from quantumscope.gui.state_inspector import StateInspector
    try:
        inspector = StateInspector(c)
        inspector.resize(1000, 640)
        inspector.show()
        inspector.refresh()
        settle(app, 0.5)
        save(inspector, 'state-inspector.png', scale=0.8)
    except Exception as exc:                                     # noqa: BLE001
        print('   (state inspector skipped:', exc, ')')

    # Quantum ML (v0.8.0): Datasets, the two classifiers, and the VQLS solution view
    w._launch_qml_datasets()
    datasets = w._open_experiments['qml_datasets']
    datasets.source.setCurrentIndex(datasets.source.findData('mnist'))
    settle(app, 0.4)
    save(w, 'qml-datasets.png', scale=0.75)
    w._launch_qml_kernel()
    kernel = w._open_experiments['qml_kernel']
    kernel.data.source.setCurrentIndex(kernel.data.source.findData('mnist'))
    kernel.data.qubits.setValue(4)
    kernel.data.class_a.setCurrentIndex(kernel.data.class_a.findText('3'))
    kernel.data.class_b.setCurrentIndex(kernel.data.class_b.findText('8'))
    kernel.feature_map.setCurrentIndex(kernel.feature_map.findData('angle'))
    kernel.bandwidth.setValue(0.5)
    kernel.train().wait()
    settle(app, 0.4)
    save(w, 'qml-kernel.png', scale=0.75)
    kernel.views.setCurrentIndex(1)                          # the kernel map, with a mistake selected
    mistakes = [item for item in kernel.kernel_map.getPlotItem().items
                if hasattr(item, 'points') and len(item.points()) and item.points()[0].data()
                and item.opts.get('symbol') == 'x']
    if mistakes:
        kernel._show_points([mistakes[0].points()[0]])
    settle(app, 0.4)
    save(w, 'qml-kernel-map.png', scale=0.75)
    kernel.top_tabs.setCurrentIndex(1)                       # the 3-D view: separating axes, margins
    settle(app, 0.2)
    kernel.view3d.axes_box.setCurrentIndex(kernel.view3d.axes_box.findData('separating'))
    kernel.view3d.run.wait()
    kernel.view3d.show_margins.setChecked(True)
    settle(app, 0.3)
    from PySide6.QtGui import QImage
    from PySide6.QtCore import Qt as _Qt
    shot = kernel.view3d.save_image(os.path.join(IMAGES, 'qml-3d.png'))
    QImage(shot).scaledToWidth(960, _Qt.TransformationMode.SmoothTransformation).save(shot)
    print('   qml-3d.png', QImage(shot).width(), 'x', QImage(shot).height())
    kernel.top_tabs.setCurrentIndex(0)
    kernel.views.setCurrentWidget(kernel.evaluation)          # v0.8.3: Evaluation, with cross-validation
    cv = kernel.evaluation.run_cross_validation()
    while cv.running():
        app.processEvents()
    settle(app, 0.4)
    save(w, 'qml-evaluation.png', scale=0.75)
    kernel.views.setCurrentWidget(kernel.search_panel)        # and a search, ranked
    kernel.search_panel.bandwidths.setText('0.25, 0.5, 1')
    kernel.search_panel.strengths.setText('1, 10')
    search = kernel.search_panel.search()
    while search.running():
        app.processEvents()
    settle(app, 0.4)
    save(w, 'qml-search.png', scale=0.75)
    kernel.views.setCurrentWidget(kernel.heatmap)
    calculator = w._launch_calculator()                       # v0.9.0: the Math tab
    run = calculator.set_expression('CNOT (H ⊗ I)|00⟩', evaluate=True)
    while run.running():
        app.processEvents()
    settle(app, 0.4)
    save(w, 'math-calculator.png', scale=0.75)
    w._select_category('qml')
    import numpy as _np
    from quantumscope.ml import datasets as _D
    digits = _D.load('mnist')                                 # predict on new images with the saved model
    import tempfile
    scratch = tempfile.mkdtemp(prefix='quantumscope-guide-')    # outside the repository
    model_path = kernel.model_panel.save(os.path.join(scratch, 'digits-3-vs-8.npz'))
    sample_path = os.path.join(scratch, 'new-digits.npz')
    _np.savez(sample_path, images=digits.X[1000:1300].reshape(-1, 28, 28), y=digits.y[1000:1300])
    kernel.model_panel.load(model_path)
    kernel.model_panel.predict_file(sample_path).wait()
    settle(app, 0.4)
    dialog = kernel.model_panel.dialog
    dialog.resize(640, 460)
    settle(app, 0.2)
    save(dialog, 'qml-predictions.png', scale=0.9)
    dialog.close()
    w._launch_qml_variational()
    variational = w._open_experiments['qml_variational']
    variational.data.source.setCurrentIndex(variational.data.source.findData('breast_cancer'))
    variational.data.qubits.setValue(4)
    variational.steps.setValue(60)
    variational.train().wait()
    settle(app, 0.4)
    save(w, 'qml-variational.png', scale=0.75)
    w._launch_circuits()
    w.circuit_widget.load_library('vqls', {'problem': 'harder', 'layers': 2})
    w.circuit_widget.optimize_parameters().waited()
    solution = w.circuit_widget.show_vqls_solution()
    solution.resize(760, 460)
    settle(app, 0.4)
    save(solution, 'vqls-solution.png', scale=0.9)
    solution.close()
    w._launch_annealing()                                       # Quantum annealing: a hexagon, partly adiabatic
    annealing = w._open_experiments['annealing']
    annealing.problem_box.setCurrentIndex(annealing.problem_box.findData('maxcut:ring6'))
    annealing.T.setValue(10)
    annealing.compute().wait()
    annealing.tabs.setCurrentIndex(1)
    annealing.s_slider.setValue(28)
    settle(app, 0.4)
    save(w, 'annealing.png', scale=0.75)

    # Learn, Settings, About
    from PySide6.QtCore import QUrl
    from quantumscope.gui.learn_window import LearnWindow
    learn = LearnWindow()
    learn.resize(1250, 820)
    learn.move(0, 0)
    learn.show()
    learn.open_lesson('principles/08-observables')
    settle(app, 0.4)
    learn._link(QUrl('glossary:Hermitian'))
    settle(app, 0.3)
    from PySide6.QtGui import QPainter
    image = learn.grab().toImage()
    painter = QPainter(image)
    popup = learn._term_popup
    painter.drawImage(learn.mapFromGlobal(popup.pos()) if not OFFSCREEN else learn.reader.mapTo(learn, learn.reader.rect().center()),
                      popup.grab().toImage())
    painter.end()
    from PySide6.QtCore import Qt
    image.scaledToWidth(int(image.width() * 0.75), Qt.TransformationMode.SmoothTransformation).save(
        os.path.join(IMAGES, 'learn.png'))
    print('   learn.png')
    popup.hide()
    from quantumscope.gui.settings_dialog import SettingsDialog
    settings = SettingsDialog(w)
    settings.resize(820, 560)
    settings.show()
    settle(app, 0.3)
    save(settings, 'settings.png', scale=0.85)


def build_pdf():
    """docs/user-guide.md (+ docs/references.md) → the PDF: see tools/guide_pdf.py."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import guide_pdf
    report = guide_pdf.build(PDF)
    print('PDF:', PDF, os.path.getsize(PDF) // 1024, 'KB |', report['pages'], 'pages,', report['headings'], 'headings,',
          report['figures'], 'figures')
    print('   figures shrunk to fill gaps:', {k + 1: round(v, 2) for k, v in report['shrunk'].items()} or 'none')
    print('   headings moved to the next page:', len(report['moved']))
    print('   figures floated below their text:', {k + 1: v for k, v in report['floated'].items()} or 'none')
    print('   blank spots left:', [(p, f'{g:.0%}') for p, g in report['gaps']] or 'none')
    return report


if __name__ == '__main__':
    if '--pdf-only' not in sys.argv:
        screenshots()
    build_pdf()
    os._exit(0)                                       # skip Qt/VTK teardown (see tests/conftest.py)
