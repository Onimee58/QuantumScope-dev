"""v1.0.0: signed license files, checked offline (no window)."""
import datetime as dt
import importlib.util
import json
import os
import sys

import pytest

from quantumscope.licensing import check as L
from quantumscope.licensing import ed25519

SECRET = bytes(range(32))
PUBLIC = ed25519.public_key(SECRET).hex()
TODAY = dt.date(2027, 1, 15)


# RFC 8032, section 7.1, tests 1 and 2
@pytest.mark.parametrize('secret, public, message, signature', [
    ('9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60',
     'd75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a', '',
     'e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b'),
    ('4ccd089b28ff96da9db6c346ec114e0f5b8a319f35aba624da8cf6ed4fb8a6fb',
     '3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c', '72',
     '92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da085ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00'),
])
def test_ed25519_matches_rfc_8032(secret, public, message, signature):
    s, m = bytes.fromhex(secret), bytes.fromhex(message)
    assert ed25519.public_key(s).hex() == public
    assert ed25519.sign(s, m).hex() == signature
    assert ed25519.verify(bytes.fromhex(public), m, bytes.fromhex(signature))
    assert not ed25519.verify(bytes.fromhex(public), m + b'!', bytes.fromhex(signature))


def test_a_license_reads_back(monkeypatch):
    text = L.make(SECRET, 'QS-AQC-S27-007', 'student', course='Applied Quantum Computing, Spring 2027',
                  expires='2027-06-30', issued='2026-11-18')
    lic = L.read(text, public=PUBLIC, today=TODAY)
    assert (lic.id, lic.kind, lic.expires) == ('QS-AQC-S27-007', 'student', '2027-06-30')
    assert lic.summary() == ('Student license QS-AQC-S27-007 · Applied Quantum Computing, Spring 2027 · '
                             'valid until 30 June 2027')
    owner = L.read(L.make(SECRET, 'QS-OWNER-001', 'owner', holder='Saif'), public=PUBLIC, today=TODAY)
    assert owner.end() is None and 'no end date' in owner.summary()


@pytest.mark.parametrize('field, value', [('expires', '2099-12-31'), ('kind', 'owner'), ('id', 'QS-AQC-S27-008'),
                                          ('course', 'Another course')])
def test_an_edited_license_is_refused(field, value):
    fields = json.loads(L.make(SECRET, 'QS-AQC-S27-007', 'student', expires='2027-06-30', course='AQC'))
    fields[field] = value
    with pytest.raises(L.LicenseError, match='not valid'):
        L.read(json.dumps(fields), public=PUBLIC, today=TODAY)


def test_other_keys_files_and_ends_are_refused(monkeypatch):
    text = L.make(SECRET, 'QS-1', 'student', expires='2027-06-30')
    other = ed25519.public_key(bytes(32)).hex()
    with pytest.raises(L.LicenseError, match='not valid'):
        L.read(text, public=other, today=TODAY)                       # someone else's key
    with pytest.raises(L.LicenseError, match='not a QuantumScope license'):
        L.read('hello', public=PUBLIC, today=TODAY)
    with pytest.raises(L.LicenseError, match='ended on 30 June 2027'):
        L.read(text, public=PUBLIC, today=dt.date(2027, 7, 1))
    assert L.read(text, public=PUBLIC, today=dt.date(2027, 6, 30))    # the last day still counts
    monkeypatch.setattr(L, 'REVOKED', frozenset({'QS-1'}))
    with pytest.raises(L.LicenseError, match='no longer valid'):
        L.read(text, public=PUBLIC, today=TODAY)
    with pytest.raises(L.LicenseError, match='without its license key'):
        L.read(text, public=L.PLACEHOLDER, today=TODAY)


def test_install_keeps_a_copy(tmp_path, monkeypatch):
    monkeypatch.delenv('QUANTUMSCOPE_LICENSE_FILE', raising=False)
    source = tmp_path / 'QuantumScope-license-QS-1.qslicense'
    source.write_text(L.make(SECRET, 'QS-1', 'beta'))
    folder = tmp_path / 'data'
    assert L.installed(str(folder), public=PUBLIC) == (None, '')
    lic = L.install(str(source), str(folder), public=PUBLIC)
    source.unlink()                                                    # the copy is what counts
    assert L.installed(str(folder), public=PUBLIC)[0] == lic
    bad = tmp_path / 'bad.qslicense'
    bad.write_text('{}')
    with pytest.raises(L.LicenseError):
        L.install(str(bad), str(folder), public=PUBLIC)
    assert L.installed(str(folder), public=PUBLIC)[0] == lic           # a refused file changes nothing


def load_tool():
    path = os.path.join(os.path.dirname(__file__), '..', 'tools', 'licenses.py')
    spec = importlib.util.spec_from_file_location('licenses_tool', path)
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    return tool


def test_the_tool_makes_the_key_and_the_first_licenses(tmp_path, monkeypatch):
    tool = load_tool()
    key_file = tmp_path / 'license_key.py'
    key_file.write_text(f"PUBLIC_KEY = '{L.PLACEHOLDER}'\n")
    monkeypatch.setattr(tool, 'KEY_FILE', str(key_file))
    keys, out = tmp_path / 'keys', tmp_path / 'licenses'
    tool.main(['--keys', str(keys), '--out', str(out), 'setup'])
    public = tool.repo_public_key()
    assert public != L.PLACEHOLDER
    secret = (keys / tool.SECRET).read_text().strip()
    assert ed25519.public_key(bytes.fromhex(secret)).hex() == public
    if sys.platform != 'win32':
        assert oct((keys / tool.SECRET).stat().st_mode & 0o777) == '0o600'
    files = sorted(p.name for p in out.glob('*.qslicense'))
    assert len(files) == 42 and 'QuantumScope-license-QS-OWNER-001.qslicense' in files
    assert 'QuantumScope-license-QS-BETA-001.qslicense' in files and 'QuantumScope-license-QS-AQC-S27-040.qslicense' in files
    student = L.read_file(str(out / 'QuantumScope-license-QS-AQC-S27-040.qslicense'), public=public, today=TODAY)
    assert student.expires == '2027-06-30' and student.course == tool.COURSE
    assert len((out / 'licenses.csv').read_text().splitlines()) == 43
    with pytest.raises(SystemExit):                                     # the key is never replaced by accident
        tool.main(['--keys', str(keys), '--out', str(out), 'setup'])
    tool.main(['--keys', str(keys), '--out', str(out), 'make', '--kind', 'student', '--prefix', 'QS-AQC-S27',
               '--start', '41', '--count', '2', '--expires', '2027-06-30'])
    assert (out / 'QuantumScope-license-QS-AQC-S27-042.qslicense').exists()
    with pytest.raises(SystemExit):                                     # never overwritten
        tool.main(['--keys', str(keys), '--out', str(out), 'make', '--kind', 'beta', '--prefix', 'QS-BETA'])


def test_the_release_has_its_license_key():
    """Fails until `python tools/licenses.py setup` has written the public key (then commit
    src/quantumscope/licensing/license_key.py). A release without it would refuse every license."""
    assert L.key_is_set(), 'Run: python tools/licenses.py setup  (then commit license_key.py)'
    assert len(bytes.fromhex(L.PUBLIC_KEY)) == 32
