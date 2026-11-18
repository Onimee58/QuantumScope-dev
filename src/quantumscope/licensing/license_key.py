"""The public key that checks license files (hex). Written by `python tools/licenses.py setup`,
which keeps the matching private key outside the repository. The zeros are a placeholder: a build
with them refuses every license (and its --self-test fails)."""
PUBLIC_KEY = '0000000000000000000000000000000000000000000000000000000000000000'
