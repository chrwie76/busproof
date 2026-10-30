"""The package installs and knows its version — the smallest proof that the build works."""

import subprocess
import sys

import busproof


def test_the_package_has_a_version_from_git():
    assert busproof.__version__
    assert busproof.__version__ != "0.0.0"


def test_the_core_does_not_load_mqtt_so_the_extra_stays_optional():
    # A fresh interpreter: in this one, another test may already have imported busproof.mqtt.
    loaded = subprocess.run(
        [sys.executable, "-c", "import sys, busproof; print('aiomqtt' in sys.modules)"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert loaded.stdout.strip() == "False"
