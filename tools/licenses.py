#!/usr/bin/env python3
"""Make QuantumScope license files (v1.0.0). Run on the owner's computer only.

  python tools/licenses.py setup
      Once: makes the private key (kept OUTSIDE the repository, in ~/QuantumScope-license-keys),
      writes the matching public key into src/quantumscope/licensing/license_key.py (commit that
      file), and makes the first licenses in ~/QuantumScope-licenses: one owner license, one beta
      tester license and 40 student licenses for Applied Quantum Computing, Spring 2027 (valid until
      30 June 2027), with a list to note who received which.

  python tools/licenses.py make --kind student --count 5 --start 41 --prefix QS-AQC-S27 \\
         --course "Applied Quantum Computing, Spring 2027" --expires 2027-06-30
  python tools/licenses.py make --kind beta --count 1 --start 2 --prefix QS-BETA
      More licenses, any time, with the same key: no new release needed.

  python tools/licenses.py check FILE.qslicense
      What a license file says, and whether this version of QuantumScope accepts it.

The private key is the only way to make licenses. Keep a copy somewhere safe (a password manager or
an encrypted USB drive): if it is lost, no new license can be made for released versions; if it
leaks, anyone can make licenses (make a new key with `setup --new-key`, and release a new version).
Never put it in the repository, an email or a chat.
"""
import argparse
import csv
import datetime as dt
import os
import re
import stat
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
from quantumscope.licensing import ed25519  # noqa: E402
from quantumscope.licensing.check import KINDS, SUFFIX, LicenseError, make, read_file  # noqa: E402

KEY_FILE = os.path.join(ROOT, 'src', 'quantumscope', 'licensing', 'license_key.py')
KEYS = os.path.expanduser('~/QuantumScope-license-keys')
OUT = os.path.expanduser('~/QuantumScope-licenses')
SECRET = 'quantumscope-license-private.key'
COURSE = 'Applied Quantum Computing, Spring 2027'
COURSE_END = '2027-06-30'


def repo_public_key():
    text = open(KEY_FILE, encoding='utf-8').read()
    return re.search(r"PUBLIC_KEY = '([0-9a-f]{64})'", text).group(1)


def shown(path):
    """A path relative to the repository when it is inside it, else as it is (on Windows, another
    drive has no relative path)."""
    try:
        relative = os.path.relpath(path, ROOT)
    except ValueError:
        return path
    return path if relative.startswith('..') else relative


def load_secret(keys):
    path = os.path.join(keys, SECRET)
    if not os.path.exists(path):
        sys.exit(f'No private key at {path}: run `python tools/licenses.py setup` first '
                 '(or pass --keys with the folder that holds it).')
    secret = bytes.fromhex(open(path, encoding='ascii').read().strip())
    if ed25519.public_key(secret).hex() != repo_public_key():
        sys.exit('This private key does not match the public key in license_key.py: licenses made with it '
                 'would be refused. Check that you are using the right key folder and repository.')
    return secret


def write_license(out, secret, id, kind, **fields):
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, f'QuantumScope-license-{id}{SUFFIX}')
    if os.path.exists(path):
        sys.exit(f'{path} exists already: licenses are never overwritten (choose another --start).')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(make(secret, id, kind, **fields))
    return path


def record(out, rows):
    """Add the new licenses to licenses.csv, with an empty column for whom each was given to."""
    path = os.path.join(out, 'licenses.csv')
    new = not os.path.exists(path)
    with open(path, 'a', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        if new:
            w.writerow(['license', 'kind', 'course', 'valid until', 'issued', 'given to', 'date given'])
        w.writerows(rows)
    return path


def make_batch(out, secret, kind, prefix, count, start, course='', expires='', holder=''):
    rows, paths = [], []
    today = dt.date.today().isoformat()
    for n in range(start, start + count):
        id = f'{prefix}-{n:03d}'
        paths.append(write_license(out, secret, id, kind, holder=holder, course=course, expires=expires))
        rows.append([id, kind, course, expires or 'no end date', today, '', ''])
    record(out, rows)
    return paths


def setup(args):
    path = os.path.join(args.keys, SECRET)
    if os.path.exists(path) and not args.new_key:
        sys.exit(f'A private key exists already at {path}. Use `make` for more licenses; `setup --new-key` '
                 'replaces the key, and every license made with the old one stops working in the next release.')
    secret = os.urandom(32)
    os.makedirs(args.keys, exist_ok=True)
    with open(path, 'w', encoding='ascii') as f:
        f.write(secret.hex() + '\n')
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    public = ed25519.public_key(secret).hex()
    text = open(KEY_FILE, encoding='utf-8').read()
    with open(KEY_FILE, 'w', encoding='utf-8') as f:
        f.write(re.sub(r"PUBLIC_KEY = '[0-9a-f]{64}'", f"PUBLIC_KEY = '{public}'", text))
    print(f'Private key: {path}  (keep it safe and private; back it up now)')
    print(f'Public key written to {shown(KEY_FILE)}: commit this file.')
    owner = make_batch(args.out, secret, 'owner', 'QS-OWNER', 1, 1, holder=args.owner)
    beta = make_batch(args.out, secret, 'beta', 'QS-BETA', args.beta, 1)
    students = make_batch(args.out, secret, 'student', 'QS-AQC-S27', args.students, 1, course=COURSE,
                          expires=COURSE_END)
    print(f'Licenses in {args.out}: {len(owner)} owner, {len(beta)} beta tester, {len(students)} student '
          f'(valid until {COURSE_END}); licenses.csv lists them, to note who received which.')


def make_more(args):
    secret = load_secret(args.keys)
    paths = make_batch(args.out, secret, args.kind, args.prefix, args.count, args.start, course=args.course,
                       expires=args.expires, holder=args.holder)
    print(f'{len(paths)} license(s) in {args.out}, listed in licenses.csv')


def check(args):
    try:
        lic = read_file(args.file)
    except LicenseError as exc:
        sys.exit(f'Not accepted: {exc}')
    print(f'Accepted: {lic.summary()} (issued {lic.issued})')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--keys', default=KEYS, help=f'folder of the private key (default {KEYS})')
    parser.add_argument('--out', default=OUT, help=f'folder for the license files (default {OUT})')
    sub = parser.add_subparsers(dest='command', required=True)
    s = sub.add_parser('setup', help='make the key and the first licenses')
    s.add_argument('--owner', default='Md. Saif Hassan Onim, PhD', help='name on the owner license')
    s.add_argument('--beta', type=int, default=1, help='beta tester licenses (default 1)')
    s.add_argument('--students', type=int, default=40, help='student licenses (default 40)')
    s.add_argument('--new-key', action='store_true', help='replace an existing key (old licenses stop working)')
    s.set_defaults(run=setup)
    m = sub.add_parser('make', help='more licenses with the existing key')
    m.add_argument('--kind', choices=list(KINDS), required=True)
    m.add_argument('--prefix', required=True, help='e.g. QS-AQC-S27 or QS-BETA')
    m.add_argument('--count', type=int, default=1)
    m.add_argument('--start', type=int, default=1, help='first number (licenses are never overwritten)')
    m.add_argument('--course', default='')
    m.add_argument('--expires', default='', help='last valid day, YYYY-MM-DD (empty: no end date)')
    m.add_argument('--holder', default='', help='a name to show in the app (optional)')
    m.set_defaults(run=make_more)
    c = sub.add_parser('check', help='check a license file')
    c.add_argument('file')
    c.set_defaults(run=check)
    args = parser.parse_args(argv)
    args.run(args)


if __name__ == '__main__':
    main()
