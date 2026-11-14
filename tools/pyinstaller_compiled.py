"""Put the Cython-compiled modules into the installers in place of their bytecode (v0.9.7).

PyInstaller still analyses the Python source, so it finds every library QuantumScope needs exactly as
before. This adds one step to the spec file, after that analysis: each QuantumScope module compiled
by tools/cython_compile.py leaves the bytecode archive and goes in as a native extension.

    python tools/pyinstaller_compiled.py QuantumScope.spec OUT    add the step to a spec made by pyi-makespec
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MARK = '# QuantumScope: native modules in place of bytecode (tools/pyinstaller_compiled.py)'


def swap(analysis, out):
    """Move compiled QuantumScope modules from analysis.pure to analysis.binaries. Returns their names."""
    sys.path.insert(0, HERE)
    try:
        from cython_compile import compiled_path, modules
    finally:
        sys.path.pop(0)
    expected = {dotted for dotted, _ in modules()}
    kept, swapped = [], []
    for entry in analysis.pure:
        name = entry[0]
        path = compiled_path(out, name) if name in expected else None
        if path is None:
            kept.append(entry)
            continue
        suffix = os.path.basename(path)[len(name.rsplit('.', 1)[-1]):]          # .cpython-312-….so / .pyd
        analysis.binaries.append((name.replace('.', '/') + suffix, path, 'EXTENSION'))
        swapped.append(name)
    analysis.pure[:] = kept
    readable = [entry[0] for entry in kept if entry[0].startswith('quantumscope.') and entry[0] in expected]
    if readable:      # would ship as bytecode: never silently
        raise SystemExit(f'Not compiled, would ship as bytecode: {readable}')
    unused = sorted(expected - set(swapped))       # not imported by the app: not bundled at all, as before
    print(f'QuantumScope: {len(swapped)} modules bundled as native code'
          + (f'; not used by the app, so not bundled: {", ".join(unused)}' if unused else ''))
    return swapped


def add_to_spec(spec, out):
    text = open(spec, encoding='utf-8').read()
    if MARK in text:
        return
    anchor = '\npyz = PYZ('
    if anchor not in text:
        raise SystemExit(f'{spec}: no "pyz = PYZ(" line to add the step before')
    step = (f'\n{MARK}\nimport sys as _qs_sys\n_qs_sys.path.insert(0, {HERE!r})\n'
            f'import pyinstaller_compiled as _qs_compiled\n_qs_compiled.swap(a, {os.path.abspath(out)!r})\n'
            f'import pyinstaller_trim as _qs_trim\n_qs_trim.trim(a)\n')                 # unused Qt parts (0.9.10)
    open(spec, 'w', encoding='utf-8').write(text.replace(anchor, step + anchor, 1))


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    add_to_spec(sys.argv[1], sys.argv[2])
