"""Remembering recent results so that repeating them is instant (v0.9.10, no Qt).

A few results are expensive and often asked for again with the same inputs: a hydrogen orbital's
3-D grid (redrawn whenever only the display changes — representation, opacity, camera), and a quantum
kernel matrix (recomputed when only the classifier's C or λ changes, and many times over in Search).
Each cache keeps the most recent results within a memory budget, oldest out first. All caches are
emptied when the computer runs short of memory (gui/resource_monitor.py calls clear_all), so a
cache never causes the shortage it would otherwise have to warn about.
"""
import hashlib
from collections import OrderedDict

import numpy as np

MB = 1024 ** 2
_caches = []


def nbytes(value):
    """Memory held by a result: arrays, and tuples or lists of them."""
    if isinstance(value, np.ndarray):
        return value.nbytes
    if isinstance(value, (tuple, list)):
        return sum(nbytes(v) for v in value)
    return 64


def fingerprint(array):
    """A short key for an array's exact contents, shape and type."""
    array = np.ascontiguousarray(array)
    digest = hashlib.blake2b(array.view(np.uint8), digest_size=16)
    digest.update(repr((array.shape, array.dtype.str)).encode())
    return digest.hexdigest()


def frozen(value):
    """Cached arrays are made read-only, so no caller can change a result another caller will get."""
    if isinstance(value, np.ndarray):
        value.setflags(write=False)
    elif isinstance(value, (tuple, list)):
        for v in value:
            frozen(v)
    return value


class Cache:
    """Least-recently-used results, within `limit` bytes and `entries` results."""

    def __init__(self, name, limit, entries=8):
        self.name, self.limit, self.entries = name, int(limit), int(entries)
        self.items = OrderedDict()
        self.hits = self.misses = 0
        _caches.append(self)

    @property
    def size(self):
        return sum(nbytes(v) for v in self.items.values())

    def get(self, key, compute):
        if key in self.items:
            self.items.move_to_end(key)
            self.hits += 1
            return self.items[key]
        self.misses += 1
        value = frozen(compute())
        if nbytes(value) <= self.limit:
            self.items[key] = value
            while len(self.items) > self.entries or self.size > self.limit:
                self.items.popitem(last=False)
        return value

    def clear(self):
        self.items.clear()


def clear_all():
    """Empty every cache (memory is running short)."""
    for cache in _caches:
        cache.clear()


def caches():
    return list(_caches)
