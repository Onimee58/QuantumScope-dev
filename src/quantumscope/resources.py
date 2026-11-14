"""Memory and processor use (v0.9.6, no Qt): what the computer has, what a task will need, and when to warn.

QuantumScope watches two things while it runs (gui/resource_monitor.py): how much memory is still
free on the computer, and whether the processor has been fully busy for a while. Before the few
tasks that can need a lot of memory (a fine 3-D orbital grid, a large kernel matrix) it estimates
the need and asks first if the computer would run short.
"""
from dataclasses import dataclass

GB = 1024 ** 3
MB = 1024 ** 2

# Thresholds on the memory still available to programs (the larger of a share and an amount).
HIGH = (0.15, 800 * MB)              # getting full: the status bar turns amber
CRITICAL = (0.08, 400 * MB)          # nearly full: QuantumScope warns once
BUSY_PERCENT = 95                    # the whole processor this busy …
BUSY_SECONDS = 30                    # … for this long: the status bar says so
ASK_SHARE = 0.7                      # ask before a task that would use more than this share of free memory


@dataclass(frozen=True)
class Snapshot:
    process: int                     # bytes QuantumScope itself uses (resident memory)
    total: int                       # bytes of memory in the computer
    available: int                   # bytes still available to programs
    cpu: float                       # percent of the whole processor busy (all programs)
    cores: int

    @property
    def used_share(self):
        return 1 - self.available / self.total if self.total else 0.0


def snapshot(process=None):
    """The current use. psutil measures it the same way on Windows, macOS and Linux."""
    import os
    import psutil
    process = process or psutil.Process(os.getpid())
    memory = psutil.virtual_memory()
    return Snapshot(process.memory_info().rss, memory.total, memory.available,
                    psutil.cpu_percent(interval=None), psutil.cpu_count() or 1)


def memory_level(snap):
    """'ok', 'high' or 'critical' for the memory still available."""
    def below(limits):
        share, amount = limits
        return snap.available < max(share * snap.total, amount)
    if below(CRITICAL):
        return 'critical'
    return 'high' if below(HIGH) else 'ok'


def size(nbytes):
    """Bytes in words: '850 MB', '1.4 GB'."""
    return f'{nbytes / GB:.1f} GB' if nbytes >= GB else f'{max(1, round(nbytes / MB))} MB'


# ---- estimates for the tasks that can need a lot of memory ---------------------------------------------
def hydrogen_grid(resolution, viewers=1):
    """A 3-D orbital: the density (float64) and wavefunction (complex128) on resolution³ points, the
    coordinate arrays, and the cloud's colours or the surface. Measured: about 80 bytes a point with
    VTK, about 72 with the OpenGL view (v0.9.11); the estimate keeps the margin."""
    return int(80 * resolution ** 3 * viewers)


def kernel_matrix(n_train, n_test, qubits):
    """Feature-map states (complex128, 2^qubits each) for every sample, the training and test kernels,
    and the decision-region grid's kernel (about 8,100 points against the training set)."""
    states = (n_train + n_test) * 16 * 2 ** qubits
    kernels = 8 * (n_train * n_train + n_test * n_train + 8100 * n_train)
    return int(1.5 * (states + kernels))      # temporary copies while computing


def check(needed, snap):
    """(fine?, message): whether a task needing `needed` bytes fits comfortably in free memory."""
    if needed <= ASK_SHARE * snap.available:
        return True, ''
    return False, (f'This needs about {size(needed)} of memory, and about {size(snap.available)} is free. '
                   f'The computer may slow down a lot, or QuantumScope may close. Close other programs or '
                   f'choose a smaller setting first.')


# ---- system requirements (stated in the guide, the README and the releases page) ----------------------
REQUIREMENTS = {
    'Minimum': dict(cpu='64-bit, 2 cores', memory='4 GB', graphics='OpenGL 3.2 (most integrated graphics since 2015)',
                    disk='1.5 GB free', screen='1280 × 720',
                    note='3-D orbitals up to 96 points per axis; circuits up to 10 qubits; Quantum ML up to a few hundred samples'),
    'Recommended': dict(cpu='4 cores', memory='8 GB', graphics='Recent integrated graphics (Intel Iris Xe, AMD Radeon, Apple M1)',
                        disk='2 GB free', screen='1920 × 1080',
                        note='Everything, including the comparison 3-D view and larger datasets'),
    'Best': dict(cpu='6 or more cores', memory='16 GB', graphics='A dedicated graphics card (NVIDIA or AMD)',
                 disk='2 GB free (SSD)', screen='1920 × 1080 or larger',
                 note='The finest 3-D grids (160 points per axis) with both viewers, and the largest models, smoothly'),
}
# Set by what the installers are built with: Qt 6.12 (macOS 14.4+; Windows 10 1809+ or 11) and Ubuntu 24.04
# (whose system library the Linux build needs: Ubuntu 24.04, Debian 13 or newer).
SYSTEMS = ('Windows 10 (version 1809 or later) or Windows 11, 64-bit; macOS 14.4 or later on Apple Silicon; '
           'Ubuntu 24.04 or Debian 13 or later, 64-bit')
