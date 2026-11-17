"""What a test project configures: `busproof.toml`, one section per environment.

    [env.local]
    line = "../contracts/line.yaml"

BUSPROOF_ENV picks the section, so the same tests run on a laptop, in CI and at another site
without a change. The file is in Git and holds no secret; where the broker is and how to log in
come from environment variables, set by `.env` locally and by CI variables in a pipeline.
"""

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

DEFAULT_ENV = "local"


class SettingsError(Exception):
    """A `busproof.toml` that is missing or incomplete, or an environment variable not set."""


@dataclass(frozen=True)
class Settings:
    env: str
    # The line file, resolved against the folder of busproof.toml.
    line: Path


def read_settings(start: Path) -> Settings:
    """Read `busproof.toml` from `start` or the nearest folder above it."""
    path = _find(start)
    environments = tomllib.loads(path.read_text()).get("env", {})
    env = os.environ.get("BUSPROOF_ENV") or DEFAULT_ENV
    if env not in environments:
        known = ", ".join(sorted(environments)) or "none"
        raise SettingsError(f"{path} has no environment {env!r}; it has: {known}")
    section = environments[env]
    if "line" not in section:
        raise SettingsError(f"{path}: [env.{env}] does not say which line file to read")
    return Settings(env, path.parent / section["line"])


def broker_url() -> str:
    url = os.environ.get("BUSPROOF_MQTT_URL")
    if not url:
        raise SettingsError("BUSPROOF_MQTT_URL is not set; see the template of the environment")
    return url


def _find(start: Path) -> Path:
    for folder in [start, *start.parents]:
        if (folder / "busproof.toml").is_file():
            return folder / "busproof.toml"
    raise SettingsError(f"no busproof.toml in {start} or above it")
