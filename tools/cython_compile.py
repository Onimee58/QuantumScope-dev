"""Compile QuantumScope's modules to native code with Cython, for the installers (v0.9.7).

PyInstaller normally bundles Python bytecode, which free tools turn back into readable code. Each
module compiled here becomes machine code (.so on Linux and macOS, .pyd on Windows) instead; the
installers then carry the compiled module in place of its bytecode (tools/pyinstaller_compiled.py).

    python tools/cython_compile.py OUT      compile every module into OUT/quantumscope/...
    python tools/cython_compile.py --list   the modules that would be compiled

Package __init__ files and __main__ (PyInstaller's start script) stay Python: they hold no logic
worth hiding. The source tree is never changed; C files and temporary objects go under OUT/.c.
"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC = os.path.join(ROOT, 'src')
KEEP_AS_PYTHON = {'__init__.py', '__main__.py'}

# Cython settings: behave exactly like Python. Annotations stay hints (Cython would otherwise check
# `x: int` strictly), functions keep their names and signatures for Qt and inspect, and the source
# is not embedded in the compiled file.
DIRECTIVES = dict(language_level=3, annotation_typing=False, binding=True, embedsignature=False,
                  always_allow_keywords=True)

# Small and quick to build: Python's own flags ask for debugging data and the slowest optimisation,
# which made the compiled modules 157 MB on Linux. The heavy numbers are NumPy's work anyway.
if sys.platform == 'win32':
    COMPILE, LINK = ['/O1'], []
elif sys.platform == 'darwin':
    COMPILE, LINK = ['-Os', '-g0'], ['-Wl,-S', '-Wl,-x']
else:
    COMPILE, LINK = ['-Os', '-g0'], ['-s']


def modules():
    """(dotted name, path) for each module to compile, sorted."""
    found = []
    for folder, dirs, files in os.walk(os.path.join(SRC, 'quantumscope')):
        dirs[:] = sorted(d for d in dirs if d != '__pycache__')
        for name in sorted(files):
            if name.endswith('.py') and name not in KEEP_AS_PYTHON:
                path = os.path.join(folder, name)
                dotted = os.path.relpath(path, SRC)[:-3].replace(os.sep, '.')
                found.append((dotted, path))
    return found


def compile_all(out):
    from Cython.Build import cythonize
    from setuptools import Extension, setup
    out = os.path.abspath(out)
    extensions = [Extension(dotted, [path], extra_compile_args=COMPILE, extra_link_args=LINK) for dotted, path in modules()]
    jobs = os.cpu_count() or 2
    compiled = cythonize(extensions, compiler_directives=DIRECTIVES, build_dir=os.path.join(out, '.c'),
                         nthreads=jobs, quiet=True)
    setup(name='quantumscope-compiled', ext_modules=compiled, script_args=[
        'build_ext', '--build-lib', out, '--build-temp', os.path.join(out, '.c', 'objects'), '-j', str(jobs)])
    risky = whole_numbers_as_decimals(os.path.join(out, '.c'))
    if risky:
        raise SystemExit('Cython would compute these powers of whole numbers as decimals (2 ** len(x) gives '
                         '8.0, not 8); write them with << or int(...):\n  ' + '\n  '.join(risky))
    missing = [dotted for dotted, _ in modules() if compiled_path(out, dotted) is None]
    if missing:
        raise SystemExit(f'Not compiled: {missing}')
    print(f'Compiled {len(modules())} modules into {out}')


def whole_numbers_as_decimals(c_folder):
    """Source lines where Cython turned a power of whole numbers into a decimal. Python's 2 ** len(x)
    is a whole number; compiled, Cython computes it in C as pow(2.0, (double) n), which breaks
    range(), reshape() and text such as '8×8'. Found in the generated C, as 'file.py:line'."""
    import re
    found = set()
    for folder, _, files in os.walk(c_folder):
        for name in files:
            if not name.endswith('.c'):
                continue
            where = None
            with open(os.path.join(folder, name), encoding='utf-8', errors='replace') as f:
                for line in f:
                    m = re.match(r'\s*/\* "([^"]+\.py)":(\d+)', line)
                    if m:
                        where = f'{m.group(1)}:{m.group(2)}'
                    elif re.search(r'(?<![A-Za-z_])pow\([^;]*\(double\)', line):
                        found.add(where)
    return sorted(found)


def compiled_path(out, dotted):
    """The compiled file for a module under OUT, or None."""
    from importlib.machinery import EXTENSION_SUFFIXES
    base = os.path.join(out, *dotted.split('.'))
    for suffix in EXTENSION_SUFFIXES:
        if os.path.isfile(base + suffix):
            return base + suffix
    return None


if __name__ == '__main__':
    if sys.argv[1:] == ['--list']:
        print('\n'.join(dotted for dotted, _ in modules()))
    elif len(sys.argv) == 2:
        compile_all(sys.argv[1])
    else:
        raise SystemExit(__doc__)
