"""Ed25519 signatures (RFC 8032), in plain Python: no extra package in the installers.

QuantumScope only verifies; signing is used by tools/licenses.py on the owner's computer, where the
private key lives. This follows the reference code of RFC 8032, section 6, and is checked against
its test vectors (tests/test_v100_licensing.py). It is not constant-time: fine for verifying
license files and for signing them offline, not for a server facing attackers.
"""
import hashlib

P = 2 ** 255 - 19
Q = 2 ** 252 + 27742317777372353535851937790883648493


def _sha512(data):
    return hashlib.sha512(data).digest()


def _inverse(x):
    return pow(x, P - 2, P)


D = -121665 * _inverse(121666) % P
SQRT_M1 = pow(2, (P - 1) // 4, P)


def _hash_mod_q(data):
    return int.from_bytes(_sha512(data), 'little') % Q


def _add(a, b):
    A = (a[1] - a[0]) * (b[1] - b[0]) % P
    B = (a[1] + a[0]) * (b[1] + b[0]) % P
    C = 2 * a[3] * b[3] * D % P
    Dd = 2 * a[2] * b[2] % P
    E, F, G, H = B - A, Dd - C, Dd + C, B + A
    return (E * F, G * H, F * G, E * H)


def _multiply(s, point):
    result = (0, 1, 1, 0)
    while s > 0:
        if s & 1:
            result = _add(result, point)
        point = _add(point, point)
        s >>= 1
    return result


def _equal(a, b):
    return (a[0] * b[2] - b[0] * a[2]) % P == 0 and (a[1] * b[2] - b[1] * a[2]) % P == 0


def _recover_x(y, sign):
    if y >= P:
        return None
    x2 = (y * y - 1) * _inverse(D * y * y + 1)
    if x2 == 0:
        return None if sign else 0
    x = pow(x2, (P + 3) // 8, P)
    if (x * x - x2) % P:
        x = x * SQRT_M1 % P
    if (x * x - x2) % P:
        return None
    if (x & 1) != sign:
        x = P - x
    return x


_GY = 4 * _inverse(5) % P
_GX = _recover_x(_GY, 0)
BASE = (_GX, _GY, 1, _GX * _GY % P)


def _compress(point):
    z = _inverse(point[2])
    x, y = point[0] * z % P, point[1] * z % P
    return int.to_bytes(y | ((x & 1) << 255), 32, 'little')


def _decompress(data):
    if len(data) != 32:
        return None
    y = int.from_bytes(data, 'little')
    sign = y >> 255
    y &= (1 << 255) - 1
    x = _recover_x(y, sign)
    return None if x is None else (x, y, 1, x * y % P)


def _expand(secret):
    if len(secret) != 32:
        raise ValueError('An Ed25519 private key is 32 bytes')
    h = _sha512(secret)
    a = int.from_bytes(h[:32], 'little')
    a &= (1 << 254) - 8
    a |= 1 << 254
    return a, h[32:]


def public_key(secret):
    """The 32-byte public key of a 32-byte private key."""
    a, _ = _expand(secret)
    return _compress(_multiply(a, BASE))


def sign(secret, message):
    """The 64-byte signature of `message` (bytes)."""
    a, prefix = _expand(secret)
    public = _compress(_multiply(a, BASE))
    r = _hash_mod_q(prefix + message)
    R = _compress(_multiply(r, BASE))
    s = (r + _hash_mod_q(R + public + message) * a) % Q
    return R + int.to_bytes(s, 32, 'little')


def verify(public, message, signature):
    """True when `signature` was made for `message` by the owner of `public`."""
    if len(public) != 32 or len(signature) != 64:
        return False
    A = _decompress(public)
    R = _decompress(signature[:32])
    if A is None or R is None:
        return False
    s = int.from_bytes(signature[32:], 'little')
    if s >= Q:
        return False
    h = _hash_mod_q(signature[:32] + public + message)
    return _equal(_multiply(s, BASE), _add(R, _multiply(h, A)))
