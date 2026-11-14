"""Print PyInstaller arguments that bundle only the VTK modules QuantumScope uses (v0.9.6).

Used by .github/workflows/release.yml:  python -m PyInstaller ... $(python tools/pyinstaller_vtk_args.py)
Each used module is a hidden import; every other VTK Python module installed on the build machine is
excluded, so PyInstaller follows only the libraries the used ones link against.
"""
import os
import pkgutil
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# VTK's helper packages for other toolkits and its "import everything" module, never used here.
OPTIONAL_PACKAGES = {'all', 'web', 'gtk', 'tk', 'wx', 'test', 'generate_pyi'}


def arguments():
    import vtkmodules
    from quantumscope.visualization.vtk_modules import VTK_MODULES
    installed = {m.name for m in pkgutil.iter_modules(vtkmodules.__path__)}
    missing = [m for m in VTK_MODULES if m not in installed]
    if missing:
        raise SystemExit(f'VTK modules QuantumScope needs are not installed: {missing}')
    unused = {m for m in installed - set(VTK_MODULES) if m.startswith('vtk') or m in OPTIONAL_PACKAGES}
    args = [f'--hidden-import=vtkmodules.{m}' for m in VTK_MODULES]
    args += [f'--exclude-module=vtkmodules.{m}' for m in sorted(unused)]
    return args


if __name__ == '__main__':
    print(' '.join(arguments()))
