"""The package installs and knows its version — the smallest proof that the build works."""

import re
import subprocess
import sys
from pathlib import Path

import busproof


def test_the_plant_knows_nothing_of_busproof():
    # A system does not know the tool it is tested with (docs/CONCEPT.md, decision 19).
    plant = Path(__file__).parents[2] / "demo" / "plant"
    sources = [path for path in plant.rglob("*.py") if ".venv" not in path.parts]
    assert sources

    for path in sources:
        assert not re.search(r"^\s*(from|import) busproof\b", path.read_text(), re.M), path


def test_the_test_project_uses_only_the_public_interface():
    # So it could move to a repository of its own unchanged (docs/CONCEPT.md, decision 19).
    project = Path(__file__).parents[2] / "demo" / "line-tests"
    sources = [path for path in project.rglob("*.py") if ".venv" not in path.parts]
    assert sources

    for path in sources:
        assert not re.search(r"^\s*(from|import) busproof\.", path.read_text(), re.M), path


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
