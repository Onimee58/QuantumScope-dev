"""QuantumScope Hydrogen Explorer Qt desktop UI."""
from pathlib import Path
from importlib.resources import files
import traceback
import os
import subprocess
import sys

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt, QModelIndex, QSettings, QUrl, QStandardPaths, QTimer
from PySide6.QtGui import QDesktopServices, QPixmap, QPainter, QPen, QColor, QIcon
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel,
    QMainWindow, QMessageBox, QPushButton, QScrollArea, QSpinBox, QDoubleSpinBox,
    QSplitter, QVBoxLayout, QWidget, QFileDialog, QDialog, QDialogButtonBox, QFrame, QInputDialog, QTabWidget, QSizePolicy, QToolButton, QMenu, QApplication,
    QStyle, QTabBar,
)
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from quantumscope import __version__
from quantumscope.physics import HydrogenAtom, density_grid
from quantumscope.physics.hydrogen import A_MU_METERS, captured_probability, RealHydrogenState
from quantumscope.visualization.orbitals import draw_orbital, set_camera_view, probability_radius
from quantumscope.visualization.gl3d import View3D
from quantumscope.gui.plots import tidy
from quantumscope import caching

HYDROGEN_GRIDS = caching.Cache('hydrogen grids', 512 * caching.MB, entries=4)   # 0.9.10



USER_GUIDE_URL = 'https://github.com/Onimee58/QuantumScope/releases/latest'


def user_guide_path():
    """The user guide shipped with QuantumScope (assets/QuantumScope-User-Guide.pdf)."""
    return Path(str(files('quantumscope').joinpath('assets/QuantumScope-User-Guide.pdf')))


def open_user_guide():
    """Open the user guide in the system's PDF viewer (or, if it is missing, the releases page)."""
    path = user_guide_path()
    if path.is_file():
        return QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
    return QDesktopServices.openUrl(QUrl(USER_GUIDE_URL))

class AboutDialog(QDialog):
    """Branded, accessible project credits; GitHub avatar is cached offline."""
    AVATAR_URL = 'https://avatars.githubusercontent.com/u/50075168?s=256&v=4'

    def __init__(self,parent=None):
        super().__init__(parent)
        self.setWindowTitle('About QuantumScope')
        self.resize(510,580)
        self.setMinimumWidth(440)
        layout=QVBoxLayout(self);layout.setContentsMargins(28,20,28,20);layout.setSpacing(10)
        logo=QLabel();logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setPixmap(QPixmap(str(files('quantumscope').joinpath('assets/quantumscope-128.png'))).scaled(76,76,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
        layout.addWidget(logo)
        title=QLabel('QuantumScope');title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet('font-size:25px;font-weight:800;');layout.addWidget(title)
        subtitle=QLabel(f'Quantum Visualization Studio  •  v{__version__}')
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter);subtitle.setObjectName('muted');layout.addWidget(subtitle)
        # Check for updates, beside the version (asks permission before any connection).
        self.update_button=QPushButton('Check for updates…')
        self.update_button.setToolTip('Asks first, then looks on github.com for a newer full release')
        self.update_button.clicked.connect(self._check_for_updates)
        self.guide_button=QPushButton('User guide')
        self.guide_button.setToolTip('Open the QuantumScope User Guide (PDF)')
        self.guide_button.clicked.connect(open_user_guide)
        self.report_button=QPushButton('Report a problem…')
        self.report_button.setToolTip('Fills in an email or a GitHub issue for you to check and send')
        self.report_button.clicked.connect(lambda: parent.report_problem() if hasattr(parent,'report_problem') else None)
        update_row=QHBoxLayout();update_row.addStretch();update_row.addWidget(self.update_button)
        update_row.addWidget(self.guide_button);update_row.addWidget(self.report_button);update_row.addStretch()
        layout.addLayout(update_row)
        tagline=QLabel('Explore  •  Visualize  •  Simulate');tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tagline.setStyleSheet('color:#5ad1e9;font-size:12px;');layout.addWidget(tagline)
        divider=QFrame();divider.setObjectName('divider');layout.addWidget(divider)
        dev=QHBoxLayout();dev.setSpacing(17);layout.addLayout(dev)
        self.photo=QLabel('GitHub avatar');self.photo.setFixedSize(90,90)
        self.photo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.photo.setStyleSheet('background:#1d3852;border-radius:12px;color:#aac3d8;')
        dev.addWidget(self.photo)
        identity=QVBoxLayout();identity.setSpacing(4);dev.addLayout(identity,1)
        name=QLabel('Md. Saif Hassan Onim, PhD');name.setStyleSheet('font-size:15px;font-weight:700;');identity.addWidget(name)
        for line in ('Developer & maintainer','Postdoctoral Fellow','Southern Methodist University, Dallas'):
            label=QLabel(line);label.setObjectName('muted');label.setWordWrap(True);identity.addWidget(label)
        self._load_avatar()
        desc=QLabel('Scientific software for teaching hydrogen orbitals, quantum principles, quantum circuits and quantum machine learning.')
        desc.setWordWrap(True);desc.setAlignment(Qt.AlignmentFlag.AlignCenter);layout.addWidget(desc)
        features=QLabel('Hydrogen Explorer & Dynamics  •  Double Slit  •  Superposition & Entanglement  •  Circuit Simulator  •  QASM Converter')
        features.setObjectName('muted');features.setWordWrap(True)
        features.setAlignment(Qt.AlignmentFlag.AlignCenter);layout.addWidget(features)
        links=QHBoxLayout();layout.addLayout(links)
        for text,url in (('GitHub repository','https://github.com/Onimee58/QuantumScope'),('Developer profile','https://github.com/Onimee58'),('SMU page','https://people.smu.edu/monim')):
            btn=QPushButton(text+' ↗');btn.clicked.connect(lambda checked=False,u=url:QDesktopServices.openUrl(QUrl(u)))
            links.addWidget(btn)
        footer=QLabel('MIT licensed  •  Python / PySide6 / NumPy / OpenGL  •  Idealized educational simulations')
        footer.setObjectName('muted');footer.setWordWrap(True);footer.setAlignment(Qt.AlignmentFlag.AlignCenter);layout.addWidget(footer)
        layout.addStretch()
        close=QPushButton('Close');close.clicked.connect(self.accept);layout.addWidget(close)

    def _load_avatar(self):
        directory=Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.CacheLocation)) / 'QuantumScope'
        directory.mkdir(parents=True,exist_ok=True)
        self._avatar_path=directory/'github-avatar.png'
        if self._avatar_path.exists():
            self._display_avatar(self._avatar_path.read_bytes())
        self._network=QNetworkAccessManager(self)
        request=QNetworkRequest(QUrl(self.AVATAR_URL))
        self._reply=self._network.get(request)
        self._reply.finished.connect(self._avatar_received)

    def _display_avatar(self,data):
        pix=QPixmap()
        if pix.loadFromData(data):
            self.photo.setText('')
            self.photo.setPixmap(pix.scaled(90,90,Qt.AspectRatioMode.KeepAspectRatioByExpanding,Qt.TransformationMode.SmoothTransformation))
            return True
        return False

    def _avatar_received(self):
        if self._reply.error()==self._reply.NetworkError.NoError:
            data=bytes(self._reply.readAll())
            if self._display_avatar(data):
                try:self._avatar_path.write_bytes(data)
                except OSError:pass
        self._reply.deleteLater()

    def _check_for_updates(self):
        from quantumscope.gui.update_dialog import check_for_updates
        check_for_updates(self)

def fitted_size(width, height, screen=None):
    """The size to open a window at: as asked, but within the screen's free area (without the taskbar
    or Dock), leaving room for the title bar (v0.9.17)."""
    from PySide6.QtGui import QGuiApplication
    screen = screen or QGuiApplication.primaryScreen()
    if screen is None:
        return width, height
    free = screen.availableGeometry()
    return min(width, free.width() - 16), min(height, free.height() - 48)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"QuantumScope {__version__} — Quantum Visualization Studio")
        self.setWindowIcon(QIcon(str(files("quantumscope").joinpath("assets/quantumscope.png"))))
        self.resize(*fitted_size(1420, 920))          # v0.9.17: never taller or wider than the screen
        self.atom = HydrogenAtom()
        self.axis = self.density = self.psi = self.state = None
        self.compare_axis = self.compare_density = self.compare_psi = self.compare_state = None
        # Signals from dependent quantum-number controls may fire during UI construction.
        # Do not render until all widgets and plotters have been initialized.
        self._ui_ready = False
        self._syncing_camera = False
        self._rendering = False
        self._build_ui()
        self._ui_ready = True
        self._build_workspace()
        self.refresh()

    def _experiment_menu(self, parent, category=None):
        """Single extensible experiment catalog shared by header and tab bar."""
        menu = QMenu(parent)
        menu.setObjectName("experimentMenu")
        if category in (None,"hydrogen"):
            menu.addSection("ATOMIC PHYSICS")
            menu.addAction("Hydrogen Explorer", self._show_hydrogen)
            menu.addAction("Hydrogen Dynamics 2D", self.show_dynamics)
            menu.addAction("Hydrogen Dynamics 3D", self.show_dynamics_3d)
        if category in (None,"principles"):
            menu.addSection("QUANTUM PRINCIPLES")
            menu.addAction("Double-Slit Experiment", self._launch_double_slit)
            menu.addAction("Quantum Superposition (spin-½)", self._launch_superposition)
            menu.addAction("Quantum Entanglement (electron spins)", self._launch_entanglement)
            menu.addAction("Quantum Teleportation", self._launch_teleportation)
        if category in (None,"circuits"):
            menu.addSection("QUANTUM CIRCUITS")
            menu.addAction("Gate Circuit Simulator", self._launch_circuits)
            menu.addAction("QASM Converter", self._launch_converter)
            menu.addAction("Error-correction explorer", self._launch_qec_explorer)
            menu.addAction("Quantum annealing", self._launch_annealing)
        if category in (None,"qml"):
            menu.addSection("QUANTUM ML")
            menu.addAction("Datasets", self._launch_qml_datasets)
            menu.addAction("Quantum Kernel Classifier", self._launch_qml_kernel)
            menu.addAction("Variational Classifier", self._launch_qml_variational)
        if category in (None,"math"):
            menu.addSection("MATH")
            menu.addAction("Quantum Calculator", self._launch_calculator)
        return menu

    def _show_settings(self):
        from quantumscope.gui.settings_dialog import SettingsDialog
        SettingsDialog(self).exec()

    # ---- hooks used by the Settings window ---------------------------------------------
    def apply_theme(self, choice):
        from quantumscope.gui.theme import apply_theme
        apply_theme(choice)
        if hasattr(self, "circuit_widget"):
            self.circuit_widget.apply_theme()
        if getattr(self, "_learn", None) is not None:
            self._learn.apply_theme()

    # ---- Learn ------------------------------------------------------------------------
    def open_learn(self, area="circuits"):
        from quantumscope.gui.learn_window import LearnWindow
        if getattr(self, "_learn", None) is None:
            self._learn = LearnWindow(host=self, parent=self)
        self._learn.show_area(area)
        self._learn.show()
        self._learn.raise_()
        self._learn.activateWindow()

    def launch_view(self, view):
        """Open a view by name (used by lesson "Try it" links)."""
        {"circuits": self._launch_circuits, "converter": self._launch_converter,
         "orbital": self._show_hydrogen, "dynamics2d": self.show_dynamics, "dynamics3d": self.show_dynamics_3d,
         "doubleslit": self._launch_double_slit, "superposition": self._launch_superposition,
         "entanglement": self._launch_entanglement, "teleportation": self._launch_teleportation,
         "qec": self._launch_qec_explorer, "annealing": self._launch_annealing, "qml_datasets": self._launch_qml_datasets,
         "qml_kernel": self._launch_qml_kernel, "qml_variational": self._launch_qml_variational,
         "calculator": self._launch_calculator}[view]()

    def apply_preferences(self):
        if hasattr(self, "circuit_widget"):
            self.circuit_widget.apply_preferences()
        if hasattr(self, "news_bar"):                     # the news choice may have changed
            self.news_bar.start()
        if hasattr(self, "resource_monitor"):
            self.resource_monitor.apply_preferences()

    def graphics_information(self):
        """Renderer, vendor and OpenGL version of the 3D view's actual context."""
        self._update_gpu_diagnostics()
        return self.gpu_diagnostics.text()

    def restart_application(self):
        """Relaunch QuantumScope so start-up settings (graphics device, size) take effect."""
        from quantumscope.gui import preferences as prefs
        answer = QMessageBox.question(
            self, "Restart QuantumScope",
            "QuantumScope will close and start again with the new settings. Save your work first.\nRestart now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes:
            return
        command = [sys.executable] if getattr(sys, "frozen", False) else [sys.executable, "-m", "quantumscope"]
        try:
            subprocess.Popen(command, env=prefs.restart_environment(), start_new_session=True,
                             cwd=str(Path.home()), close_fds=True)
        except OSError as exc:
            QMessageBox.warning(self, "Restart failed", str(exc))
            return
        self.close()

    def check_for_updates(self):
        """Only on request: asks permission, then one request to GitHub (see gui/update_dialog.py)."""
        from quantumscope.gui.update_dialog import check_for_updates
        check_for_updates(self)

    def _follow_system_theme(self, *_):
        from quantumscope.gui import preferences as prefs
        if prefs.get("appearance/theme") == "system":
            self.apply_theme("system")

    def report_problem(self, error=None):
        """Help → Report a problem: shows the whole report, then fills in an email or a GitHub issue."""
        from quantumscope.gui.report_dialog import ReportDialog
        dialog = ReportDialog(self, error)
        self._report_dialog = dialog
        dialog.exec()
        return dialog

    def start_news(self):
        """After the window appears: ask once about the news, or read it if a week has passed."""
        return self.news_bar.start()

    def _header_button(self, label, tooltip, action):
        button = QToolButton(self)
        button.setObjectName("headerTool")
        button.setText(label)
        button.setToolTip(tooltip)
        button.setAccessibleName(tooltip)
        button.clicked.connect(action)
        return button

    def _build_workspace(self):
        """Host every experiment in the same extensible, closable tab workspace."""
        explorer = self.takeCentralWidget()
        shell = QWidget(self)
        shell.setObjectName("workspaceShell")
        outer = QVBoxLayout(shell)
        outer.setContentsMargins(15, 12, 15, 12)
        outer.setSpacing(10)
        self.menuBar().hide()  # Native menu retained internally but not shown.
        header = QWidget()
        header.setObjectName("workspaceHeader")
        row = QHBoxLayout(header)
        row.setContentsMargins(15, 10, 15, 10)
        mark = QLabel()
        mark.setObjectName("brandMark")
        mark.setPixmap(QPixmap(str(files("quantumscope").joinpath("assets/quantumscope.png"))).scaled(
            44, 44, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        mark.setFixedSize(50, 50)
        row.addWidget(mark)
        titles = QVBoxLayout()
        titles.setSpacing(1)
        name = QLabel("QuantumScope")
        name.setObjectName("brandTitle")
        titles.addWidget(name)
        caption = QLabel(f"QUANTUM VISUALIZATION STUDIO  /  v{__version__}")
        caption.setObjectName("brandCaption")
        titles.addWidget(caption)
        row.addLayout(titles)
        row.addStretch()
        row.addWidget(self._search_box())                   # v0.9.18: find an experiment by name or topic
        new_button = QToolButton(self)
        new_button.setObjectName("newExperiment")
        new_button.setText("+ New Experiment  ▾")
        new_button.setToolTip("Open or switch to an experiment")
        new_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        new_button.setMenu(self._experiment_menu(new_button))
        row.addWidget(new_button)
        row.addWidget(self._header_button("⚑", "Report a problem", self.report_problem))
        row.addWidget(self._header_button("⚙", "Settings", self._show_settings))
        row.addWidget(self._header_button("ⓘ", "About QuantumScope (and check for updates)", self.show_about))
        outer.addWidget(header)
        from quantumscope.gui.news_bar import NewsBar          # announcements, after the user allows them (v0.9.5)
        self.news_bar = NewsBar(self)
        outer.addWidget(self.news_bar)
        self.categories = QTabWidget()
        self.categories.setObjectName("categoryWorkspace")
        self.categories.setDocumentMode(True)
        self.workspaces = {}
        for category, title in (("hydrogen", "⚛  Hydrogen"),
                                ("principles", "◈  Quantum Principles"),
                                ("circuits", "▦  Quantum Circuits"),
                                ("qml", "◇  Quantum ML"),
                                ("math", "∑  Math")):
            tabs = QTabWidget()
            tabs.setObjectName("experimentWorkspace")
            tabs.setTabsClosable(True)
            tabs.setDocumentMode(True)
            tabs.tabCloseRequested.connect(lambda idx, cat=category: self._close_workspace_tab(cat, idx))
            plus = QToolButton(tabs)
            plus.setObjectName("tabAddButton")
            plus.setText("+")
            plus.setToolTip("New experiment")
            plus.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
            plus.setMenu(self._experiment_menu(plus,category))
            # Each area has a Learn button next to "+": lectures and labs for that area.
            corner = QWidget(tabs)
            corner_row = QHBoxLayout(corner)
            corner_row.setContentsMargins(0, 0, 0, 0)
            corner_row.setSpacing(4)
            learn = QToolButton(corner)
            learn.setObjectName("tabAddButton")
            learn.setText("📖 Learn")
            learn.setToolTip("Lectures and labs for this area")
            learn.clicked.connect(lambda _=False, cat=category: self.open_learn(cat))
            corner_row.addWidget(learn)
            detach = QToolButton(corner)                         # v0.9.15: any tab in its own window
            detach.setObjectName("tabAddButton")
            detach.setText("⧉")
            detach.setToolTip("Open this tab in its own window (closing the window puts it back)")
            detach.clicked.connect(lambda _=False, cat=category: self._detach_tab(cat, self.workspaces[cat].currentIndex()))
            corner_row.addWidget(detach)
            corner_row.addWidget(plus)
            tabs.tabBar().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            tabs.tabBar().customContextMenuRequested.connect(lambda pos, cat=category: self._tab_menu(cat, pos))
            tabs.setCornerWidget(corner, Qt.Corner.TopRightCorner)
            self.categories.addTab(tabs, title)
            self.workspaces[category] = tabs
        self.workspace = self.workspaces["hydrogen"]
        self.workspace.addTab(explorer, QIcon(str(files("quantumscope").joinpath("assets/quantumscope-24.png"))), "Hydrogen Explorer")
        self._hydrogen_explorer = explorer          # closing hides it; + → Hydrogen Explorer brings it back
        from quantumscope.gui.circuit_workspace import CircuitWorkspace
        self.circuit_widget = CircuitWorkspace(self.workspaces["circuits"])
        self.workspaces["circuits"].addTab(self.circuit_widget, "Gate Circuit Simulator")
        from quantumscope.gui.qasm_converter import QasmConverter
        # The converter opens as a tab only when chosen (+ → QASM Converter) and can be closed;
        # the widget is kept, so reopening it keeps what you were converting.
        self.converter_widget = QasmConverter(self._load_converted_circuit, self.workspaces["circuits"])
        self.converter_widget.hide()
        # v0.9.17: the areas scroll when the window is shorter (or narrower) than an experiment needs,
        # instead of the window growing past the bottom of a small screen.
        self.workspace_scroll = QScrollArea()
        self.workspace_scroll.setObjectName("workspaceScroll")
        self.workspace_scroll.setWidgetResizable(True)
        self.workspace_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.workspace_scroll.setWidget(self.categories)
        outer.addWidget(self.workspace_scroll, 1)
        self.categories.currentChanged.connect(self._fit_pages)
        for tabs in self.workspaces.values():
            tabs.currentChanged.connect(self._fit_pages)
        self.categories.currentChanged.connect(self._seen)                  # v0.9.18: dots go once seen
        for tabs in self.workspaces.values():
            tabs.currentChanged.connect(self._seen)
        self.setCentralWidget(shell)
        self._open_experiments = {}
        self._detached = {}                              # widget → its own window (v0.9.15)
        self._experiment_labels, self._experiment_icons, self._placeholders = {}, {}, {}
        self._launch_double_slit()
        self._show_placeholder("qml")                    # Quantum ML opens on its Start page
        self._show_placeholder("math")                   # so does Math (v0.9.0)
        self._select_category("hydrogen")
        self.statusBar().showMessage("Ready  ·  Choose an experiment or explore hydrogen orbitals")
        from quantumscope.gui.resource_monitor import ResourceMonitor    # memory and processor (v0.9.6)
        self.resource_monitor = ResourceMonitor(self)

    # ---- dots on tabs, and search (v0.9.18) ----------------------------------------------------
    SEARCH_WORDS = {
        "Hydrogen Explorer": "atom orbital orbitals wavefunction quantum numbers n l m electron cloud radial",
        "Hydrogen Dynamics 2D": "time evolution wave packet superposition of states",
        "Hydrogen Dynamics 3D": "time evolution wave packet superposition of states",
        "Double-Slit Experiment": "interference wave particle diffraction which path photon electron",
        "Quantum Superposition (spin-½)": "spin stern gerlach bloch sphere measurement probability",
        "Quantum Entanglement (electron spins)": "bell test chsh epr correlation nonlocality",
        "Quantum Teleportation": "protocol bell pair classical bits",
        "Gate Circuit Simulator": "gates circuit h cnot cx bell ghz grover qft measurement noise qasm pdf "
                                  "ibm hardware qiskit statevector",
        "QASM Converter": "openqasm qiskit import export",
        "Error-correction explorer": "qec bit flip phase flip shor steane surface code syndrome",
        "Quantum annealing": "qubo ising max-cut maxcut number partitioning feature selection d-wave adiabatic",
        "Datasets": "csv upload data pca features mnist iris wine breast cancer split test",
        "Quantum Kernel Classifier": "qsvm svm support vector machine kernel ridge grid search roc cross-validation",
        "Variational Classifier": "vqc neural network training gradient descent adam bfgs loss",
        "Quantum Calculator": "dirac notation bra ket matrix eigenvalue trace partial trace tensor product",
    }

    def _search_entries(self):
        """(shown text, words to match, action) for everything the search box can open."""
        menu = self._experiment_menu(self)
        entries, area = [], ""
        for action in menu.actions():
            if action.isSeparator():
                area = action.text().title().replace(" Ml", " ML")
                continue
            name = action.text()
            entries.append((f"{name}  ·  {area}", f"{name} {area} {self.SEARCH_WORDS.get(name, '')}", action.trigger))
        for category, title in (("hydrogen", "Hydrogen"), ("principles", "Quantum Principles"),
                                ("circuits", "Quantum Circuits"), ("qml", "Quantum ML"), ("math", "Math")):
            entries.append((f"Learn: {title}", f"learn lessons lectures labs course {title}",
                            lambda c=category: self.open_learn(c)))
        entries += [("Settings", "settings preferences theme dark light font size graphics updates", self._show_settings),
                    ("Report a problem", "report problem bug feedback", self.report_problem),
                    ("About QuantumScope", "about version check for updates", self.show_about)]
        self._search_menu = menu                                # the actions must outlive this call
        return entries

    def _search_box(self):
        from PySide6.QtGui import QStandardItem, QStandardItemModel
        from PySide6.QtWidgets import QCompleter, QLineEdit
        box = QLineEdit(self)
        box.setObjectName("searchBox")
        box.setPlaceholderText("Search…")
        box.setClearButtonEnabled(True)
        box.setToolTip("Find an experiment, a Learn area or a setting by name or topic (e.g. SVM, Bell, QUBO)")
        box.setFixedWidth(220)
        model = QStandardItemModel(box)
        self._search_actions = []
        for shown, words, action in self._search_entries():
            item = QStandardItem(shown)
            item.setData(f"{shown} {words}".lower(), Qt.ItemDataRole.UserRole)
            item.setData(len(self._search_actions), Qt.ItemDataRole.UserRole + 1)
            self._search_actions.append(action)
            model.appendRow(item)
        completer = QCompleter(model, box)
        completer.setCompletionRole(Qt.ItemDataRole.UserRole)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setMaxVisibleItems(12)
        completer.popup().setMinimumWidth(360)                 # room for the names
        completer.setWidget(box)                               # not setCompleter: the box keeps what was typed

        def typed(text):
            text = text.strip().lower()
            if text:
                completer.setCompletionPrefix(text)
                completer.complete()
            else:
                completer.popup().hide()

        def chosen(index):
            self._search_actions[index.data(Qt.ItemDataRole.UserRole + 1)]()
            box.clear()
            completer.popup().hide()

        def enter():
            index = completer.completionModel().index(0, 0)
            if box.text().strip() and index.isValid():
                chosen(index)
        box.textEdited.connect(typed)
        completer.activated[QModelIndex].connect(chosen)
        box.returnPressed.connect(enter)
        self.search_box, self.search = box, completer
        return box

    def _tab_dot_side(self, bar):
        if not bar.tabsClosable():
            return QTabBar.ButtonPosition.RightSide
        closes = bar.style().styleHint(QStyle.StyleHint.SH_TabBar_CloseButtonPosition, None, bar)
        return QTabBar.ButtonPosition.RightSide if closes == 0 else QTabBar.ButtonPosition.LeftSide

    def _put_dot(self, bar, index, reason):
        side = self._tab_dot_side(bar)
        dot = bar.tabButton(index, side)
        if dot is None or dot.objectName() != "tabDot":
            dot = QLabel("●")
            dot.setObjectName("tabDot")
            bar.setTabButton(index, side, dot)
        dot.setToolTip(reason)

    def _take_dot(self, bar, index):
        if index < 0:
            return
        side = self._tab_dot_side(bar)
        dot = bar.tabButton(index, side)
        if dot is not None and dot.objectName() == "tabDot":
            bar.setTabButton(index, side, None)
            dot.deleteLater()

    def has_dot(self, widget):
        """Whether the tab of the experiment holding `widget` has a dot (for tests)."""
        for tabs in self.workspaces.values():
            for i in range(tabs.count()):
                page = tabs.widget(i)
                if page is widget or page.isAncestorOf(widget):
                    dot = tabs.tabBar().tabButton(i, self._tab_dot_side(tabs.tabBar()))
                    return dot is not None and dot.objectName() == "tabDot"
        return False

    def flag(self, widget, reason):
        """A dot on the tab of the experiment holding `widget` (and on its area's tab), until that tab
        is looked at: for something ready or changed while you were elsewhere. Returns True if put."""
        for tabs in self.workspaces.values():
            for i in range(tabs.count()):
                page = tabs.widget(i)
                if not (page is widget or page.isAncestorOf(widget)):
                    continue
                area = self.categories.indexOf(tabs)
                if self.categories.currentIndex() == area and tabs.currentIndex() == i:
                    return False                               # in view already
                self._put_dot(tabs.tabBar(), i, reason)
                if self.categories.currentIndex() != area:
                    self._put_dot(self.categories.tabBar(), area, f"{tabs.tabText(i).strip()}: {reason}")
                return True
        return False

    def _seen(self, *_):
        tabs = self.categories.currentWidget()
        self._take_dot(self.categories.tabBar(), self.categories.currentIndex())
        if tabs is not None and tabs in self.workspaces.values():
            self._take_dot(tabs.tabBar(), tabs.currentIndex())

    def _data_changed(self, experiment):
        data = getattr(experiment, "data", None)
        if data is not None and data.source.currentData() == "store":
            self.flag(experiment, "The Datasets tab prepared new data: train again to use it")

    def _fit_pages(self, *_):
        """Only the tab in view sets how small the window may be (v0.9.17). A tab widget otherwise
        needs the room of its largest tab, open or not, so one tall experiment made every area scroll."""
        if not hasattr(self, "categories"):
            return
        for tabs in (self.categories, *self.workspaces.values()):
            current = tabs.currentWidget()
            for i in range(tabs.count()):
                page = tabs.widget(i)
                if page.property("ownPolicy") is None:
                    page.setProperty("ownPolicy", (page.sizePolicy().horizontalPolicy(), page.sizePolicy().verticalPolicy()))
                if page is current:
                    page.setSizePolicy(*page.property("ownPolicy"))
                else:
                    page.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
            tabs.updateGeometry()

    @staticmethod
    def _own_policy(widget):
        own = widget.property("ownPolicy")
        if own is not None:
            widget.setSizePolicy(*own)

    def _select_category(self, category):
        tabs=self.workspaces[category]
        self.categories.setCurrentWidget(tabs)
        return tabs

    # The area each experiment belongs to (the + menu it is listed in).
    EXPERIMENT_AREAS={"dynamics_2d":"hydrogen","dynamics_3d":"hydrogen","qec_explorer":"circuits","annealing":"circuits",
                      "double_slit":"principles","superposition":"principles","entanglement":"principles",
                      "teleportation":"principles","qml_datasets":"qml","qml_kernel":"qml",
                      "qml_variational":"qml","calculator":"math"}

    def _open_experiment(self, key, label, constructor):
        """One persistent experiment tab in its own area. A closed tab was only hidden, so it
        comes back exactly as it was left."""
        category = self.EXPERIMENT_AREAS[key]
        if key in self._open_experiments and self._open_experiments[key] in getattr(self, "_detached", {}):
            self._raise_detached(self._open_experiments[key])     # it is in its own window: show that
            return
        tabs=self._select_category(category)
        if key in self._open_experiments:
            widget=self._open_experiments[key]
            index=tabs.indexOf(widget)
            if index<0:
                index=self._add_area_tab(category,widget,self._experiment_labels.get(key,label),self._experiment_icons.get(key))
            tabs.setCurrentIndex(index)
            return
        widget=constructor(tabs)
        widget.setWindowFlags(Qt.WindowType.Widget)
        widget.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Expanding)
        icon_name={"double_slit":"◫","dynamics_2d":"∿","dynamics_3d":"⬡"}.get(key,"◈")
        self._experiment_labels[key]=f"{icon_name}  {label.strip()}"
        index=self._add_area_tab(category,widget,self._experiment_labels[key])
        self._open_experiments[key]=widget
        if key in ("qml_kernel", "qml_variational"):          # v0.9.18: new data in the Datasets tab
            from quantumscope.gui.qml_experiments import STORE
            STORE.changed.connect(lambda w=widget: self._data_changed(w))
        tabs.setCurrentIndex(index)
        self.statusBar().showMessage(f"Opened {label.strip()}",3500)

    def _add_area_tab(self,category,widget,label,icon=None,index=None):
        """Add (or re-add) a tab to an area, replacing its "nothing open" placeholder. A widget in
        its own window stays there (its window comes to the front): returns -1."""
        if widget in getattr(self, "_detached", {}):
            self._raise_detached(widget)
            return -1
        tabs=self.workspaces[category]
        placeholder=self._placeholders.get(category)
        if placeholder is not None and tabs.indexOf(placeholder)>=0:
            tabs.removeTab(tabs.indexOf(placeholder))
        widget.show()
        if index is None:
            index=tabs.addTab(widget,icon,label) if icon is not None else tabs.addTab(widget,label)
        else:
            index=tabs.insertTab(index,widget,icon,label) if icon is not None else tabs.insertTab(index,widget,label)
        getattr(self, "_fit_pages", lambda: None)()
        return index

    def _close_workspace_tab(self,category,index):
        """Every tab can close. Closing only hides its widget, so + brings it back exactly as it
        was (a circuit, an experiment's settings); an empty area shows a placeholder."""
        tabs=self.workspaces[category]
        widget=tabs.widget(index)
        if widget is None or widget is self._placeholders.get(category):
            return
        tabs.removeTab(index)
        widget.hide()
        from quantumscope.gui import pop_out                       # its graphs' windows close with it
        for window in pop_out.windows_for(widget):
            window.close()
        if tabs.count()==0:
            self._show_placeholder(category)

    # ---- tabs in their own windows (v0.9.15) ------------------------------------------------------
    def _tab_menu(self, category, pos):
        tabs = self.workspaces[category]
        index = tabs.tabBar().tabAt(pos)
        if index < 0 or tabs.widget(index) is self._placeholders.get(category):
            return
        menu = QMenu(self)
        menu.addAction("Open in its own window", lambda: self._detach_tab(category, index))
        menu.addAction("Close", lambda: self._close_workspace_tab(category, index))
        menu.exec(tabs.tabBar().mapToGlobal(pos))

    def _detach_tab(self, category, index):
        """Move a tab into its own resizable window; closing that window (or Dock back) returns it."""
        tabs = self.workspaces[category]
        widget = tabs.widget(index)
        if widget is None or widget is self._placeholders.get(category):
            return None
        label, icon, size = tabs.tabText(index), tabs.tabIcon(index), widget.size()
        tabs.removeTab(index)
        self._own_policy(widget)                          # its own size again, in its own window
        window = DetachedWindow(self, widget, label, icon, lambda: self._dock_back(widget))
        self._detached[widget] = (window, category, label, icon)
        if tabs.count() == 0:
            self._show_placeholder(category)
        window.resize(max(size.width(), 640), max(size.height() + 40, 480))
        window.show()
        window.raise_()
        self.statusBar().showMessage(f"{label.strip()} is in its own window: close it to put it back", 5000)
        return window

    def _dock_back(self, widget):
        entry = self._detached.pop(widget, None)
        if entry is None:
            return
        window, category, label, icon = entry
        window.release()
        index = self._add_area_tab(category, widget, label, icon if not icon.isNull() else None)
        self._select_category(category).setCurrentIndex(index)

    def _raise_detached(self, widget):
        window = self._detached[widget][0]
        window.showNormal()
        window.raise_()
        window.activateWindow()

    def _show_placeholder(self,category):
        tabs=self.workspaces[category]
        placeholder=self._placeholders.get(category)
        if placeholder is None:
            placeholder=self._placeholders[category]=self._make_placeholder(category)
        if tabs.indexOf(placeholder)<0:
            index=tabs.addTab(placeholder,"Start")
            tabs.tabBar().setTabButton(index,tabs.tabBar().ButtonPosition.RightSide,None)
        tabs.setCurrentWidget(placeholder)
        getattr(self, "_fit_pages", lambda: None)()

    def _make_placeholder(self,category):
        """'No experiment open', with one button per experiment of this area (from its + menu)."""
        page=QWidget();page.setObjectName("areaPlaceholder")
        outer=QVBoxLayout(page);outer.addStretch()
        title=QLabel("No experiment open");title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: 700;");outer.addWidget(title)
        hint=QLabel("Open one here, or with + above.");hint.setAlignment(Qt.AlignmentFlag.AlignCenter);hint.setObjectName("muted")
        outer.addWidget(hint)
        row=QHBoxLayout();row.addStretch()
        for action in self._experiment_menu(page,category).actions():
            if action.isSeparator() or not action.text():
                continue
            button=QPushButton(action.text());button.clicked.connect(action.trigger);row.addWidget(button)
        row.addStretch();outer.addLayout(row);outer.addStretch()
        page._buttons=[b for b in page.findChildren(QPushButton)]
        return page

    def _launch_circuits(self):
        tabs=self._select_category("circuits")
        if tabs.indexOf(self.circuit_widget)<0:                 # closed: bring it back, first
            self._add_area_tab("circuits",self.circuit_widget,"Gate Circuit Simulator",index=0)
        tabs.setCurrentWidget(self.circuit_widget)

    def _launch_converter(self):
        tabs=self._select_category("circuits")
        index=tabs.indexOf(self.converter_widget)
        if index<0:
            index=self._add_area_tab("circuits",self.converter_widget,"QASM Converter")
        tabs.setCurrentIndex(index)

    def _load_converted_circuit(self,n,gates,measured=(),layout=None):
        layout=layout or {}
        self.circuit_widget.set_circuit(n,gates,layout.get('columns'),measured,
            layout.get('measurement_column'),layout.get('total_columns'),layout.get('initial_states'),layout.get('blocks') or (),
            layout.get('noise') or (),layout.get('noise_model'),layout.get('classical') or (),layout.get('conditions') or ())
        self._launch_circuits()

    def _show_hydrogen(self):
        tabs=self._select_category("hydrogen")
        explorer=self._hydrogen_explorer
        if tabs.indexOf(explorer)<0:                            # closed: bring it back, first
            self._add_area_tab("hydrogen",explorer,"Hydrogen Explorer",
                               QIcon(str(files("quantumscope").joinpath("assets/quantumscope-24.png"))),index=0)
        tabs.setCurrentWidget(explorer)

    def _launch_double_slit(self):
        from quantumscope.gui.double_slit_dialog import DoubleSlitDialog
        self._open_experiment("double_slit", "  Double-Slit Experiment  ", DoubleSlitDialog)

    def _launch_superposition(self):
        from quantumscope.gui.quantum_principles import SuperpositionDialog
        self._open_experiment("superposition", "Quantum Superposition", SuperpositionDialog)

    def _launch_qml_datasets(self):
        from quantumscope.gui.qml_experiments import DatasetsExperiment
        self._open_experiment("qml_datasets", "Datasets",
                              lambda parent: DatasetsExperiment(parent, choose_features=self._anneal_features))

    def _launch_qml_kernel(self):
        from quantumscope.gui.qml_experiments import KernelExperiment
        self._open_experiment("qml_kernel", "Quantum Kernel Classifier", KernelExperiment)

    def _launch_qml_variational(self):
        from quantumscope.gui.qml_experiments import VariationalExperiment
        self._open_experiment("qml_variational", "Variational Classifier", VariationalExperiment)

    def _launch_calculator(self):
        from quantumscope.gui.calculator import CalculatorView
        self._open_experiment("calculator", "Quantum Calculator",
                              lambda parent: CalculatorView(parent, send_state=self.send_state_to_circuit))
        return self._open_experiments["calculator"]

    def open_calculator(self, expression=None, mode=None):
        """Open the calculator, optionally with an expression evaluated (lesson "Try it" links);
        mode ('exact' or 'digits') switches first, for expressions that need one."""
        view = self._launch_calculator()
        if mode in ('exact', 'digits') and view.calculator.mode != mode:
            (view.exact_button if mode == 'exact' else view.digits_button).setChecked(True)
            view.calculator.set_mode(mode)
        if expression:
            return view.set_expression(expression, evaluate=True)
        return None

    def send_state_to_circuit(self, vector):
        """Start the circuit simulator from a calculator state. A product state becomes per-qubit
        starting states (undoable); an entangled one cannot, which the returned message explains."""
        from quantumscope.calc.bridge import product_angles
        from quantumscope.physics.initial_states import InitialState
        try:
            angles = product_angles(vector)
        except ValueError as exc:
            return str(exc)
        if angles is None:
            return ('This state is entangled, so it cannot be written as one starting state per qubit. '
                    'Build it in the circuit with gates instead (a Bell state: H, then CNOT).')
        workspace = self.circuit_widget
        model = workspace.model
        if model.n != len(angles):                     # as if the qubit count were changed by hand: the
            workspace.qubits.setValue(len(angles))      # workspace asks only if gates would be removed
            if model.n != len(angles):
                return 'Not sent: the circuit is unchanged.'
        for qubit, (theta, phi) in enumerate(angles):
            workspace.set_initial_state(qubit, InitialState(theta, phi))
        workspace._changed()
        self._launch_circuits()
        return f'Sent: the circuit now starts in this state ({len(angles)} qubit{"s" if len(angles) != 1 else ""}).'

    def _launch_qec_explorer(self):
        from quantumscope.gui.qec_chart import ErrorCorrectionExplorer
        self._open_experiment("qec_explorer", "Error-correction explorer", ErrorCorrectionExplorer)

    def _launch_annealing(self):
        from quantumscope.gui.annealing_view import AnnealingExperiment
        self._open_experiment("annealing", "Quantum annealing",
                              lambda parent: AnnealingExperiment(parent, open_circuit=self._load_annealing_circuit,
                                                                 use_features=self._use_annealed_features))

    def _anneal_features(self, task):
        """Datasets → Quantum annealing: anneal a feature selection for the data being prepared (v0.9.13)."""
        self._launch_annealing()
        self._open_experiments["annealing"].load_task(task)

    def _use_annealed_features(self, task, names):
        """Quantum annealing → Datasets: prepare the data with the features the anneal chose (v0.9.13)."""
        self._launch_qml_datasets()
        self._open_experiments["qml_datasets"].use_features(task, names)

    def _load_annealing_circuit(self, n, gates, observable, note):
        """The anneal as gates, in the simulator, with its problem energy as the observable."""
        self.circuit_widget.show_generated_circuit(n, gates, observable, note)
        self._launch_circuits()

    def _launch_teleportation(self):
        from quantumscope.gui.teleportation_experiment import TeleportationDialog
        self._open_experiment("teleportation", "Quantum Teleportation", TeleportationDialog)

    def _launch_entanglement(self):
        from quantumscope.gui.entanglement_experiment import EntanglementDialog
        self._open_experiment("entanglement", "Quantum Entanglement", EntanglementDialog)

    def show_dynamics(self):
        from quantumscope.gui.dynamics_dialog import HydrogenDynamicsDialog
        self._open_experiment("dynamics_2d", "  Hydrogen Dynamics 2D  ", HydrogenDynamicsDialog)

    def show_dynamics_3d(self):
        from quantumscope.gui.dynamics_3d_dialog import HydrogenDynamics3DDialog
        self._open_experiment("dynamics_3d", "  Hydrogen Dynamics 3D  ", HydrogenDynamics3DDialog)

    def show_about(self):
        AboutDialog(self).exec()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter, stretch=4)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(300)                    # narrower windows scroll sideways (v0.9.15)
        scroll.setMaximumWidth(820)
        options = QWidget()
        controls = QVBoxLayout(options)
        controls.setAlignment(Qt.AlignmentFlag.AlignTop)
        controls.setSpacing(10)

        state_box = QGroupBox("Hydrogen quantum state")
        state_form = QFormLayout(state_box)
        state_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        self.n = QSpinBox()
        self.n.setRange(1, 4)
        self.l = QComboBox()
        self.m = QComboBox()
        self.n.valueChanged.connect(self._update_l)
        self.l.currentIndexChanged.connect(self._update_m)
        state_form.addRow("Principal n", self.n)
        state_form.addRow("Angular l", self.l)
        state_form.addRow("Magnetic m", self.m)
        self.basis = QComboBox()
        self.basis.addItems(["Complex Y(l,m)", "Real cosine", "Real sine"])
        state_form.addRow("Orbital basis", self.basis)
        controls.addWidget(state_box)

        compare_box = QGroupBox("Side-by-side comparison")
        compare_form = QFormLayout(compare_box)
        compare_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        self.compare_enable = QCheckBox("Enable second 3D viewer")
        self.compare_n = QSpinBox()
        self.compare_n.setRange(1, 4)
        self.compare_n.setValue(2)
        self.compare_l = QComboBox()
        self.compare_m = QComboBox()
        self.compare_basis = QComboBox()
        self.compare_basis.addItems(["Complex Y(l,m)", "Real cosine", "Real sine"])
        self.compare_n.valueChanged.connect(lambda: self._update_compare_l())
        self.compare_l.currentIndexChanged.connect(lambda: self._update_compare_m())
        compare_form.addRow(self.compare_enable)
        compare_form.addRow("Compare n", self.compare_n)
        compare_form.addRow("Compare l", self.compare_l)
        compare_form.addRow("Compare m", self.compare_m)
        compare_form.addRow("Compare basis", self.compare_basis)
        controls.addWidget(compare_box)
        self._update_compare_l()

        view_box = QGroupBox("Visualization")
        vf = QFormLayout(view_box)
        vf.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        self.mode = QComboBox()
        self.mode.addItems(["Density cloud", "Probability enclosure", "Real(psi)", "Imag(psi)"])
        self.resolution = QSpinBox()
        self.resolution.setRange(32, 160)
        self.resolution.setSingleStep(8)
        self.resolution.setValue(96)
        self.enclosed = QSpinBox()
        self.enclosed.setRange(50, 99)
        self.enclosed.setValue(90)
        self.enclosed.setSuffix("%")
        self.opacity = QDoubleSpinBox()
        self.opacity.setRange(0.2, 4.0)
        self.opacity.setSingleStep(0.2)
        self.opacity.setValue(1.4)
        vf.addRow("Representation", self.mode)
        vf.addRow("Grid points/axis", self.resolution)
        vf.addRow("Enclosed probability", self.enclosed)
        vf.addRow("Cloud visibility", self.opacity)
        controls.addWidget(view_box)

        camera_box = QGroupBox("Camera && scientific display")
        cf = QFormLayout(camera_box)
        cf.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        self.camera_view = QComboBox()
        self.camera_view.addItems(["Perspective", "+X", "+Y", "+Z"])
        self.zoom_factor = QDoubleSpinBox()
        self.zoom_factor.setRange(0.5, 5.0)
        self.zoom_factor.setSingleStep(0.25)
        self.zoom_factor.setValue(1.3)
        self.phase_color = QCheckBox("Color enclosure by wavefunction phase")
        self.show_grid = QCheckBox("Show axes and coordinates (a_mu)")
        self.sync_cameras = QCheckBox("Synchronize comparison cameras")
        self.sync_cameras.setChecked(True)
        cf.addRow("View", self.camera_view)
        cf.addRow("Magnification", self.zoom_factor)
        cf.addRow(self.phase_color)
        cf.addRow(self.show_grid)
        cf.addRow(self.sync_cameras)
        controls.addWidget(camera_box)
        self.camera_view.currentIndexChanged.connect(self._change_camera)
        self.zoom_factor.valueChanged.connect(self._change_camera)

        # Graphics information is shown in Settings → Graphics.
        self.gpu_diagnostics = QLabel("OpenGL context information pending", self)
        self.gpu_diagnostics.hide()

        self.export_scale = QSpinBox()
        self.export_scale.setRange(1, 4)
        self.export_scale.setValue(2)
        controls.addWidget(QLabel("PNG export scale (1–4×)"))
        controls.addWidget(self.export_scale)
        self.auto_render = QCheckBox("Update when changing state/mode")
        controls.addWidget(self.auto_render)
        render_btn = QPushButton("Render state")
        render_btn.clicked.connect(self.refresh)
        controls.addWidget(render_btn)
        reset_btn = QPushButton("Reset camera")
        reset_btn.clicked.connect(self._reset_camera)
        controls.addWidget(reset_btn)
        screenshot_btn = QPushButton("Export PNG")
        screenshot_btn.clicked.connect(self.export_png)
        controls.addWidget(screenshot_btn)
        data_btn = QPushButton("Export grid (.npz)")
        data_btn.clicked.connect(self.export_grid)
        controls.addWidget(data_btn)

        details_box = QGroupBox("Scientific information")
        details_box.setCheckable(True)
        details_box.setChecked(True)
        detail_layout = QVBoxLayout(details_box)
        self.details = QLabel()
        self.details.setWordWrap(True)
        self.details.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        detail_layout.addWidget(self.details)
        controls.addWidget(details_box)
        controls.addStretch()
        # Allow long setting labels to wrap instead of creating horizontal scrolling.
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        options.setMinimumWidth(398)
        scroll.setWidget(options)
        splitter.addWidget(scroll)

        self.viewer_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.plotter = View3D(central)
        self.compare_plotter = View3D(central)
        self.primary_panel = QWidget()
        primary_layout = QVBoxLayout(self.primary_panel)
        primary_layout.setContentsMargins(0, 0, 0, 0)
        primary_layout.setSpacing(2)
        self.primary_label = QLabel("Primary orbital")
        primary_layout.addWidget(self.primary_label)
        primary_layout.addWidget(self.plotter, stretch=1)
        self.viewer_splitter.addWidget(self.primary_panel)
        self.compare_panel = QWidget()
        compare_layout = QVBoxLayout(self.compare_panel)
        compare_layout.setContentsMargins(0, 0, 0, 0)
        compare_layout.setSpacing(2)
        self.compare_label = QLabel("Comparison orbital")
        compare_layout.addWidget(self.compare_label)
        compare_layout.addWidget(self.compare_plotter, stretch=1)
        self.viewer_splitter.addWidget(self.compare_panel)
        self.compare_panel.hide()
        self.plotter.cameraChanged.connect(lambda: self._mirror_camera(self.plotter, self.compare_plotter))
        self.compare_plotter.cameraChanged.connect(lambda: self._mirror_camera(self.compare_plotter, self.plotter))
        # Make the left sidebar span the full content height.
        # The compact radial plot belongs below the 3D viewers on the RIGHT only.
        viewer_column = QWidget()
        viewer_layout = QVBoxLayout(viewer_column)
        viewer_layout.setContentsMargins(0, 0, 0, 0)
        viewer_layout.setSpacing(6)
        viewer_layout.addWidget(self.viewer_splitter, stretch=1)
        splitter.addWidget(viewer_column)
        splitter.setSizes([455, 965])
        from quantumscope.gui.side_panel import wrap_in_splitter
        self.hydrogen_panel = wrap_in_splitter(splitter, 0, 'Hydrogen controls', 'hydrogen')
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        bottom = QGroupBox("Radial probability  P(r) = r² |Rₙₗ(r)|²")
        bottom.setCheckable(True)
        bottom.setChecked(True)
        self.radial_group = bottom
        blayout = QVBoxLayout(bottom)
        self.radial_plot = tidy(pg.PlotWidget())
        self.radial_plot.setBackground("#101820")
        self.radial_plot.setLabel("bottom", "r", units="a_mu")
        self.radial_plot.setLabel("left", "P(r)", units="a_mu^-1")
        self.radial_plot.showGrid(x=True, y=True, alpha=0.2)
        self.radial_plot.setMinimumHeight(95)
        blayout.addWidget(self.radial_plot)
        bottom.setMinimumHeight(125)
        bottom.setMaximumHeight(170)
        bottom.toggled.connect(self._toggle_radial_plot)
        viewer_layout.addWidget(bottom, stretch=0)
        self.statusBar().showMessage("Nonrelativistic isolated hydrogen • reduced-mass Coulomb model")
        self._update_l()
        for ctrl in (self.basis, self.compare_enable, self.compare_n, self.compare_l,
                     self.compare_m, self.compare_basis):
            signal = (ctrl.stateChanged if isinstance(ctrl, QCheckBox) else
                      ctrl.valueChanged if isinstance(ctrl, QSpinBox) else ctrl.currentIndexChanged)
            signal.connect(self._auto_refresh)
        for ctrl, signal in ((self.n, self.n.valueChanged),
                             (self.l, self.l.currentIndexChanged),
                             (self.m, self.m.currentIndexChanged),
                             (self.mode, self.mode.currentIndexChanged),
                             (self.resolution, self.resolution.valueChanged),
                             (self.enclosed, self.enclosed.valueChanged),
                             (self.opacity, self.opacity.valueChanged),
                             (self.phase_color, self.phase_color.stateChanged),
                             (self.show_grid, self.show_grid.stateChanged)):
            signal.connect(self._auto_refresh)

    def _toggle_radial_plot(self, shown):
        self.radial_plot.setVisible(shown)
        self.radial_group.setMaximumHeight(170 if shown else 35)

    def _mirror_camera(self, source, destination):
        """Keep both cameras in matching world coordinates without recursive updates."""
        if (not self._ui_ready or self._syncing_camera or self._rendering or
                not self.compare_enable.isChecked() or not self.sync_cameras.isChecked()):
            return
        self._syncing_camera = True
        try:
            destination.set_camera(source.camera())
        finally:
            self._syncing_camera = False

    def _update_compare_l(self):
        old = self.compare_l.currentData()
        self.compare_l.blockSignals(True)
        self.compare_l.clear()
        for l in range(self.compare_n.value()):
            self.compare_l.addItem(str(l), l)
        self.compare_l.setCurrentIndex(min(old if old is not None else 0,
                                           self.compare_n.value()-1))
        self.compare_l.blockSignals(False)
        self._update_compare_m()

    def _update_compare_m(self):
        l = self.compare_l.currentData()
        if l is None:
            return
        old = self.compare_m.currentData()
        self.compare_m.blockSignals(True)
        self.compare_m.clear()
        for m in range(-l, l + 1):
            self.compare_m.addItem(str(m), m)
        self.compare_m.setCurrentIndex((old if old is not None and abs(old) <= l else 0)+l)
        self.compare_m.blockSignals(False)
        self._auto_refresh()

    def _grid(self, state, n, l, m, basis):
        """The state's 3-D grid, remembered (0.9.10): changing only the display — representation,
        opacity, camera, enclosed probability — redraws at once instead of recomputing ψ."""
        resolution = self.resolution.value()
        return HYDROGEN_GRIDS.get((n, l, m, basis, resolution), lambda: density_grid(state, resolution=resolution))

    def _make_state(self, n, l, m, basis):
        if basis == "Complex Y(l,m)":
            return self.atom.state(n, l, m)
        order = abs(m)
        kind = "sin" if basis == "Real sine" and order else "cos"
        return RealHydrogenState(n, l, order, kind)

    def _auto_refresh(self, *_):
        if not self._ui_ready:
            return
        if self.auto_render.isChecked():
            self.refresh()

    def _update_l(self):
        prev = self.l.currentData()
        self.l.blockSignals(True)
        self.l.clear()
        for l in range(self.n.value()):
            self.l.addItem(str(l), l)
        self.l.setCurrentIndex(min(prev if prev is not None else 0, self.n.value() - 1))
        self.l.blockSignals(False)
        self._update_m()

    def _update_m(self):
        l = self.l.currentData()
        if l is None:
            return
        old = self.m.currentData()
        self.m.blockSignals(True)
        self.m.clear()
        for m in range(-l, l + 1):
            self.m.addItem(str(m), m)
        self.m.setCurrentIndex((old if old is not None and abs(old) <= l else 0) + l)
        self.m.blockSignals(False)
        self._auto_refresh()

    def _change_camera(self, *_):
        if self.density is None:
            return
        set_camera_view(self.plotter, probability_radius(self.axis, self.density),
                        self.camera_view.currentText(), self.zoom_factor.value())
        if self.compare_enable.isChecked() and self.compare_density is not None:
            set_camera_view(self.compare_plotter,
                            probability_radius(self.compare_axis, self.compare_density),
                            self.camera_view.currentText(), self.zoom_factor.value())

    def _update_gpu_diagnostics(self):
        """Query the 3-D view's *current* OpenGL context; environment hints aren't proof."""
        try:
            self.gpu_diagnostics.setText(self.plotter.gl_information())
        except Exception as exc:
            self.gpu_diagnostics.setText(f"Renderer query unavailable: {exc}")

    def _reset_camera(self):
        if self.density is not None:
            self.camera_view.setCurrentText("Perspective")
            self.zoom_factor.setValue(1.3)
            self._change_camera()

    def _memory_allows(self):
        """A fine grid, twice with the comparison viewer, can need a lot of memory: ask first if the
        computer may not have it (once per grid size and viewer count)."""
        from quantumscope import resources as R
        from quantumscope.gui.resource_monitor import confirm_memory
        viewers = 2 if self.compare_enable.isChecked() else 1
        key = (self.resolution.value(), viewers)
        if key in getattr(self, "_memory_accepted", set()):
            return True
        needed = R.hydrogen_grid(self.resolution.value(), viewers)
        if not confirm_memory(self, needed, f"A {self.resolution.value()}³ grid"
                              + (" in both viewers" if viewers == 2 else "")):
            return False
        self._memory_accepted = getattr(self, "_memory_accepted", set()) | {key}
        return True

    def refresh(self):
        if not self._memory_allows():
            self.statusBar().showMessage("Not drawn: lower the grid points or turn off the comparison viewer", 6000)
            return
        self._rendering = True
        try:
            self.statusBar().showMessage("Rendering…")
            self.state = self._make_state(self.n.value(), self.l.currentData(),
                                          self.m.currentData(), self.basis.currentText())
            self.axis, self.density, self.psi = self._grid(
                self.state, self.n.value(), self.l.currentData(), self.m.currentData(), self.basis.currentText())
            self.primary_label.setText("Primary: " + getattr(self.state, "label", f"n={self.state.n}, l={self.state.l}, m={self.state.m}"))
            backend, radius = draw_orbital(
                self.plotter, self.axis, self.density, self.psi,
                self.mode.currentText(), self.enclosed.value(),
                self.opacity.value(),
                self.phase_color.isChecked(), self.show_grid.isChecked(),
                self.camera_view.currentText(), self.zoom_factor.value())
            self.compare_panel.setVisible(self.compare_enable.isChecked())
            if self.compare_enable.isChecked():
                self.compare_state = self._make_state(
                    self.compare_n.value(), self.compare_l.currentData(),
                    self.compare_m.currentData(), self.compare_basis.currentText())
                self.compare_label.setText("Comparison: " + getattr(self.compare_state, "label", f"n={self.compare_state.n}, l={self.compare_state.l}, m={self.compare_state.m}"))
                self.compare_axis, self.compare_density, self.compare_psi = self._grid(
                    self.compare_state, self.compare_n.value(), self.compare_l.currentData(),
                    self.compare_m.currentData(), self.compare_basis.currentText())
                draw_orbital(self.compare_plotter, self.compare_axis,
                             self.compare_density, self.compare_psi,
                             self.mode.currentText(), self.enclosed.value(),
                             self.opacity.value(),
                             self.phase_color.isChecked(), self.show_grid.isChecked(),
                             self.camera_view.currentText(), self.zoom_factor.value())
            else:
                self.compare_axis = self.compare_density = self.compare_psi = self.compare_state = None
            self._rendering = False
            if self.compare_enable.isChecked() and self.sync_cameras.isChecked():
                # Ensure both begin with the same orientation after a refresh.
                self._mirror_camera(self.plotter, self.compare_plotter)
            r = np.linspace(0, max(30, 10*self.state.n*self.state.n), 1000)
            probability = self.state.radial_probability(r)
            self.radial_plot.clear()
            self.radial_plot.plot(r, probability, pen=pg.mkPen("#64c9f2", width=2.5))
            integral = np.cumsum(probability) * float(r[1] - r[0])
            cutoff = int(np.searchsorted(integral, 0.999 * integral[-1]))
            self.radial_plot.setXRange(0, float(r[min(len(r)-1, cutoff)]) * 1.05,
                                       padding=0)
            self.radial_plot.setYRange(0, float(max(probability)) * 1.12, padding=0)
            captured = captured_probability(self.axis, self.density)
            from quantumscope.learn import progress                     # for labs (0.9.9)
            progress.record('orbital', n=self.state.n, l=self.state.l, m=self.state.m,
                            basis={'Real cosine': 'cosine', 'Real sine': 'sine'}.get(self.basis.currentText(), 'complex'),
                            view={'Probability enclosure': 'enclosure', 'Real(psi)': 'real',
                                  'Imag(psi)': 'imag'}.get(self.mode.currentText(), 'cloud'),
                            enclosed=self.enclosed.value(), compare=int(self.compare_enable.isChecked()))
            orbital = "spdf"[self.state.l]
            state_name = getattr(self.state, "label", f"{self.state.n}{orbital} (m={self.state.m})")
            self.details.setText(
                f"<b>Orbital:</b> {state_name}<br>"
                f"<b>Energy:</b> {self.state.energy_ev:.6f} eV<br>"
                f"<b>Basis:</b> {self.basis.currentText()}<br>"
                f"<b>Comparison:</b> {getattr(self.compare_state, 'label', 'active' if self.compare_state else 'off')}<br>"
                f"<b>Bohr radius (reduced mass):</b> {A_MU_METERS * 1e12:.4f} pm<br>"
                f"<b>Grid:</b> ±{self.axis[-1]:g} a_mu per axis<br>"
                f"<b>Grid probability:</b> {captured:.6f} (numerical estimate)<br>"
                f"<b>Camera framing:</b> {radius:.1f} a_mu radius (99.5% of grid mass)<br>"
                f"<b>Drawn with:</b> {backend}<br><br>"
                "Cloud displays a transformed intensity of |ψ|² to reveal dim regions, "
                "not electron trajectories. Grid data export contains unmodified |ψ|². "
                "Nucleus marker is symbolic (not to scale). "
                "Enclosures refer to probability captured on the finite grid.")
            self.statusBar().showMessage(f"Render complete • {backend}")
            self._update_gpu_diagnostics()
        except Exception as exc:
            self._rendering = False
            self.statusBar().showMessage("Render failed")
            QMessageBox.critical(self, "Rendering error", f"{exc}\n\n{traceback.format_exc()}")

    def export_png(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export 3D image", "orbital.png", "PNG (*.png)")
        if path:
            try:
                self.plotter.save(Path(path).with_suffix(".png"), scale=self.export_scale.value())
            except Exception as exc:
                QMessageBox.critical(self, "Export error", str(exc))

    def export_grid(self):
        if self.axis is None:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export scientific data", "orbital.npz", "NumPy (*.npz)")
        if path:
            try:
                np.savez_compressed(str(Path(path).with_suffix(".npz")),
                                    axis_a_mu=self.axis, density_a_mu_minus3=self.density,
                                    psi_a_mu_minus3_over2=self.psi,
                                    n=self.state.n, l=self.state.l, m=self.state.m,
                                    energy_ev=self.state.energy_ev,
                                    orbital_basis=self.basis.currentText(),
                                    reduced_bohr_radius_m=A_MU_METERS)
            except Exception as exc:
                QMessageBox.critical(self, "Export error", str(exc))

    # ---- crash recovery ---------------------------------------------------------------
    def _session_marker(self):
        from quantumscope.gui import preferences as prefs
        return os.path.join(prefs.data_folder(), "session.running")

    def offer_recovery(self):
        """If the last session ended without a clean exit, offer its autosaved circuit.

        A marker file exists while QuantumScope runs and is removed on a normal
        exit, so a leftover marker means the previous session crashed or was killed.
        """
        from quantumscope.gui import preferences as prefs
        workspace = getattr(self, "circuit_widget", None)
        if workspace is None:
            return
        marker = self._session_marker()
        autosave = workspace.autosave_path()
        crashed = os.path.exists(marker)
        if crashed and prefs.get("files/autosave") and os.path.exists(autosave):
            answer = QMessageBox.question(
                self, "Recover circuit",
                "QuantumScope did not close normally last time.\n"
                "Recover the circuit you were working on?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.Yes)
            if answer == QMessageBox.StandardButton.Yes:
                try:
                    with open(autosave, encoding="utf-8") as handle:
                        workspace.load_text(handle.read())
                    self._launch_circuits()
                    workspace.status.setText("Recovered the circuit from your last session")
                except (OSError, ValueError) as exc:
                    QMessageBox.warning(self, "Recovery failed", str(exc))
        try:
            with open(marker, "w", encoding="utf-8") as handle:
                handle.write(str(os.getpid()))
        except OSError:
            pass
        workspace.enable_autosave(True)

    def closeEvent(self, event):
        from quantumscope.gui import pop_out                       # graphs in their own windows (v0.9.18)
        pop_out.close_all()
        for entry in list(getattr(self, "_detached", {}).values()):   # tabs in their own windows go too
            entry[0].close()
        workspace = getattr(self, "circuit_widget", None)
        if workspace is not None:
            workspace.enable_autosave(False)
            for path in (workspace.autosave_path(), self._session_marker()):
                try:
                    os.remove(path)          # a clean exit leaves nothing to recover
                except OSError:
                    pass
        self.plotter.close()
        self.compare_plotter.close()
        super().closeEvent(event)


class DetachedWindow(QWidget):
    """A tab in its own window (v0.9.15): any size and shape, on any screen. Closing it, or Dock
    back, returns the tab to its area."""

    def __init__(self, main, widget, label, icon, dock):
        super().__init__(main, Qt.WindowType.Window)
        self.widget, self._dock = widget, dock
        self.setWindowTitle(f"{label.strip()} · QuantumScope")
        if not icon.isNull():
            self.setWindowIcon(icon)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        bar = QHBoxLayout()
        bar.addWidget(QLabel(label.strip()))
        bar.addStretch()
        back = QPushButton("Dock back")
        back.setToolTip("Put this back as a tab in the main window")
        back.clicked.connect(self.close)
        bar.addWidget(back)
        layout.addLayout(bar)
        widget.setParent(self)
        layout.addWidget(widget, 1)
        widget.show()

    def release(self):
        """Hand the widget back (it is re-added as a tab by the main window)."""
        self.layout().removeWidget(self.widget)
        self.widget.setParent(None)

    def closeEvent(self, event):
        from quantumscope.gui import pop_out                       # its graphs come home first
        for window in pop_out.windows_for(self.widget):
            window.close()
        dock, self._dock = self._dock, None
        super().closeEvent(event)
        if dock is not None:
            dock()
        self.deleteLater()
