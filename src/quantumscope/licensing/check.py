"""License files (v1.0.0): QuantumScope opens only with a valid license.

A license file (.qslicense) is a small JSON text signed with the owner's private key, which never
leaves the owner's computer (tools/licenses.py makes the key and the licenses). QuantumScope holds
only the public key (license_key.py): it can tell a real license from an edited or invented one, but
cannot make one. Everything is checked offline.

Kinds: 'owner' and 'beta' (no end date, unless one is given) and 'student' (for a course, with an
end date). A license that leaked can be listed in REVOKED, so the next release refuses it.

This deters casual sharing; it cannot stop a determined programmer, as no offline check can.
"""
import base64
import datetime as dt
import json
import os
from dataclasses import dataclass

from quantumscope.licensing import ed25519
from quantumscope.licensing.license_key import PUBLIC_KEY

PRODUCT = 'QuantumScope'
FORMAT = 1
KINDS = {'owner': 'Owner license', 'beta': 'Beta tester license', 'student': 'Student license'}
SUFFIX = '.qslicense'
REVOKED = frozenset()                     # license numbers no longer accepted (add a leaked one here)
PLACEHOLDER = '0' * 64                    # license_key.py before tools/licenses.py setup


class LicenseError(ValueError):
    """Why a license file is not accepted, in words for the person holding it."""


@dataclass(frozen=True)
class License:
    id: str
    kind: str
    holder: str
    course: str
    issued: str
    expires: str                          # 'YYYY-MM-DD', the last valid day, or '' for no end
    raw: str = ''                         # the file's text, as it is stored

    @property
    def title(self):
        return KINDS.get(self.kind, 'License')

    def end(self):
        return dt.date.fromisoformat(self.expires) if self.expires else None

    def summary(self):
        """'Student license QS-… · Applied Quantum Computing · valid until 30 June 2027'"""
        parts = [f'{self.title} {self.id}']
        if self.holder:
            parts.append(f'licensed to {self.holder}')
        if self.course:
            parts.append(self.course)
        end = self.end()
        parts.append(f'valid until {end.day} {end:%B %Y}' if end else 'no end date')
        return ' · '.join(parts)


def key_is_set(public=None):
    return (public or PUBLIC_KEY) != PLACEHOLDER


def signed_part(fields):
    """The exact bytes that are signed: every field but the signature, in a fixed order."""
    content = {k: v for k, v in fields.items() if k != 'signature'}
    return json.dumps(content, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')


def make(secret, id, kind, *, holder='', course='', expires='', issued=None):
    """The text of a new license file, signed with the 32-byte private key `secret` (for tools)."""
    if kind not in KINDS:
        raise ValueError(f'kind must be one of {", ".join(KINDS)}')
    if expires:
        dt.date.fromisoformat(expires)
    fields = {'product': PRODUCT, 'format': FORMAT, 'id': id, 'kind': kind, 'holder': holder,
              'course': course, 'issued': issued or dt.date.today().isoformat(), 'expires': expires}
    fields['signature'] = base64.b64encode(ed25519.sign(secret, signed_part(fields))).decode('ascii')
    return json.dumps(fields, indent=2, ensure_ascii=False) + '\n'


def read(text, *, public=None, today=None):
    """The License in `text`, if it is genuine, not revoked and not expired; else LicenseError."""
    public = public or PUBLIC_KEY
    if not key_is_set(public):
        raise LicenseError('This copy of QuantumScope was built without its license key, so it cannot '
                           'check licenses. Please report it to the developer.')
    try:
        fields = json.loads(text)
        signature = base64.b64decode(fields['signature'], validate=True)
    except (ValueError, KeyError, TypeError):
        raise LicenseError('This is not a QuantumScope license file.') from None
    if not isinstance(fields, dict) or fields.get('product') != PRODUCT:
        raise LicenseError('This is not a QuantumScope license file.')
    if not ed25519.verify(bytes.fromhex(public), signed_part(fields), signature):
        raise LicenseError('This license file is not valid: it was changed, or it was not issued for '
                           'QuantumScope.')
    if fields.get('format') != FORMAT or fields.get('kind') not in KINDS:
        raise LicenseError('This license is for a different version of QuantumScope: please update.')
    lic = License(str(fields['id']), fields['kind'], fields.get('holder', ''), fields.get('course', ''),
                  fields.get('issued', ''), fields.get('expires', ''), text)
    if lic.id in REVOKED:
        raise LicenseError(f'License {lic.id} is no longer valid. Please ask your instructor for a new one.')
    end = lic.end()
    if end is not None and (today or dt.date.today()) > end:
        raise LicenseError(f'License {lic.id} ended on {end.day} {end:%B %Y}. Please ask your instructor '
                           'for a new one.')
    return lic


def read_file(path, **kwargs):
    try:
        with open(path, encoding='utf-8') as f:
            text = f.read(64 * 1024)
    except (OSError, UnicodeDecodeError):
        raise LicenseError('This file could not be read.') from None
    return read(text, **kwargs)


def store_path(folder):
    """Where the license in use is kept: QUANTUMSCOPE_LICENSE_FILE, or license.qslicense in `folder`
    (the app's data folder)."""
    return os.environ.get('QUANTUMSCOPE_LICENSE_FILE') or os.path.join(folder, 'license' + SUFFIX)


def installed(folder, **kwargs):
    """(License, None) for the license in use, or (None, why not) when there is none that works."""
    path = store_path(folder)
    if not os.path.exists(path):
        return None, ''
    try:
        return read_file(path, **kwargs), None
    except LicenseError as exc:
        return None, str(exc)


def install(source, folder, **kwargs):
    """Check the license file at `source` and keep a copy as the license in use; returns it."""
    lic = read_file(source, **kwargs)
    path = store_path(folder)
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(lic.raw)
    return lic
