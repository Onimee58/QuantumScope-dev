"""The VTK modules QuantumScope uses (v0.9.6), so installers bundle only these.

VTK ships about 150 Python modules and 200 libraries (about 580 MB); QuantumScope's 3-D views use
the ones below and the libraries they need. The release build passes them to PyInstaller and
excludes the rest (tools/pyinstaller_vtk_args.py), which makes the installed app about 20% smaller.
The list was taken from every module loaded by the whole GUI test suite and the user-guide build;
tests/test_v096_resources.py checks that nothing the app loads is missing, and the packaged
self-test imports every one, so a missing module fails the build instead of a student's session.
"""
VTK_MODULES = (
    'numpy_interface', 'util', 'vtkChartsCore', 'vtkCommonColor', 'vtkCommonCore', 'vtkCommonDataModel',
    'vtkCommonExecutionModel', 'vtkCommonMath', 'vtkCommonMisc', 'vtkCommonSystem', 'vtkCommonTransforms',
    'vtkFiltersCore', 'vtkFiltersGeneral', 'vtkFiltersPython', 'vtkFiltersSources', 'vtkIOCore',
    'vtkIOImage', 'vtkImagingCore', 'vtkImagingMath', 'vtkImagingSources', 'vtkInteractionStyle',
    'vtkInteractionWidgets', 'vtkParallelCore', 'vtkPythonContext2D', 'vtkRenderingAnnotation',
    'vtkRenderingContext2D', 'vtkRenderingContextOpenGL2', 'vtkRenderingCore', 'vtkRenderingFreeType',
    'vtkRenderingHyperTreeGrid', 'vtkRenderingLabel', 'vtkRenderingMatplotlib', 'vtkRenderingOpenGL2',
    'vtkRenderingUI', 'vtkRenderingVolume', 'vtkRenderingVolumeOpenGL2', 'vtkViewsContext2D', 'vtkViewsCore',
)


def import_all():
    """Import every listed module (the packaged self-test); returns how many loaded."""
    import importlib
    for name in VTK_MODULES:
        importlib.import_module(f'vtkmodules.{name}')
    return len(VTK_MODULES)
