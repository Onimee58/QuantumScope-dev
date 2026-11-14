#!/usr/bin/env bash
# Runs the optional GUI tests reliably.
#
# Tests that build the whole window (each *_mainwindow_gui.py file) and the Hydrogen tests run in
# their own processes: when they share one with the many Qt widgets the other GUI tests create, the
# process can crash at random (seen since v0.6.2), while each group passes on its own.
#
# The 3-D views draw with OpenGL (v0.9.11), which Qt's offscreen platform does not have. With no
# display, the tests run on a virtual one (xvfb-run) when it is installed; otherwise offscreen, where
# the 3-D tests are skipped.
#
# Usage: tools/run_gui_tests.sh   (uses .venv/bin/python when present)
set -u
cd "$(dirname "$0")/.."
PY=.venv/bin/python
[ -x "$PY" ] || PY=python3
export QUANTUMSCOPE_GUI_TESTS=1
RUN=()
if [ -z "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]; then
    if command -v xvfb-run >/dev/null; then
        RUN=(xvfb-run -a -s "-screen 0 1920x1200x24")
    else
        echo "No display and no xvfb-run: the 3-D tests will be skipped (sudo apt install xvfb)"
        export QT_QPA_PLATFORM=offscreen
    fi
fi
status=0
${RUN[@]+"${RUN[@]}"} "$PY" -m pytest -q tests/test_v050_hydrogen_gui.py || status=1
for file in tests/test_*_mainwindow_gui.py; do              # each whole-window file on its own
    ${RUN[@]+"${RUN[@]}"} "$PY" -m pytest -q "$file" || status=1
done
others=$(ls tests/test_*_gui.py | grep -v -e test_v050_hydrogen_gui.py -e _mainwindow_gui.py)
${RUN[@]+"${RUN[@]}"} "$PY" -m pytest -q $others || status=1
exit $status
