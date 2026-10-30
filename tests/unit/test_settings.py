"""BUSPROOF_ENV picks a section of busproof.toml, so the same tests run anywhere — and what is
missing is said in one line."""

from pathlib import Path

import pytest

from busproof.settings import SettingsError, broker_url, read_settings

TOML = """
[env.local]
line = "contracts/line.yaml"

[env.offline]
line = "contracts/line.yaml"
bus = "fake"

[env.broken]
bus = "fake"
"""


@pytest.fixture
def project(tmp_path: Path) -> Path:
    (tmp_path / "busproof.toml").write_text(TOML)
    return tmp_path


def test_without_busproof_env_the_local_section_counts(project, monkeypatch):
    monkeypatch.delenv("BUSPROOF_ENV", raising=False)

    settings = read_settings(project)

    assert settings.env == "local"
    assert settings.bus == "mqtt"


def test_busproof_env_picks_the_section(project, monkeypatch):
    monkeypatch.setenv("BUSPROOF_ENV", "offline")

    assert read_settings(project).bus == "fake"


def test_the_line_file_is_relative_to_busproof_toml(project, monkeypatch):
    monkeypatch.setenv("BUSPROOF_ENV", "local")

    assert read_settings(project).line == project / "contracts" / "line.yaml"


def test_the_file_is_found_in_a_folder_above(project, monkeypatch):
    monkeypatch.setenv("BUSPROOF_ENV", "local")
    below = project / "tests" / "control"
    below.mkdir(parents=True)

    assert read_settings(below).env == "local"


def test_an_unknown_environment_lists_the_ones_there_are(project, monkeypatch):
    monkeypatch.setenv("BUSPROOF_ENV", "plant2")

    with pytest.raises(SettingsError, match="no environment 'plant2'; it has: broken, local, off"):
        read_settings(project)


def test_a_section_without_a_line_says_so(project, monkeypatch):
    monkeypatch.setenv("BUSPROOF_ENV", "broken")

    with pytest.raises(SettingsError, match=r"\[env.broken\] does not say which line file"):
        read_settings(project)


def test_no_file_at_all_says_where_it_looked(tmp_path):
    with pytest.raises(SettingsError, match="no busproof.toml in"):
        read_settings(tmp_path)


def test_the_broker_address_comes_from_the_environment(monkeypatch):
    monkeypatch.setenv("BUSPROOF_MQTT_URL", "mqtt://broker.local:1884")

    assert broker_url() == "mqtt://broker.local:1884"


def test_a_missing_broker_address_says_which_variable(monkeypatch):
    monkeypatch.delenv("BUSPROOF_MQTT_URL", raising=False)

    with pytest.raises(SettingsError, match="BUSPROOF_MQTT_URL is not set"):
        broker_url()
