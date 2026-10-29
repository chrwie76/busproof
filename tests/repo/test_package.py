"""The package installs and knows its version — the smallest proof that the build works."""

import busproof


def test_the_package_has_a_version_from_git():
    assert busproof.__version__
    assert busproof.__version__ != "0.0.0"
