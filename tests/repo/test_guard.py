"""The guard before every tool call: what it must refuse, and what it must let through.

Both halves matter. A guard that refuses too little leaks a secret; one that refuses too much
gets switched off by the first person it annoys.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from guard import check

GUARD = Path(__file__).parents[2] / "tools" / "guard.py"


@pytest.mark.parametrize(
    ("tool", "args"),
    [
        ("Read", {"file_path": "/home/me/busproof/.env"}),
        ("Read", {"file_path": ".env.local"}),
        ("Edit", {"file_path": "demo/.env.production"}),
        ("Write", {"file_path": "secrets/broker.txt"}),
        ("Read", {"file_path": "certs/server.key"}),
        ("Read", {"file_path": "certs/client.pem"}),
        ("NotebookEdit", {"notebook_path": "/repo/.env"}),
        ("Glob", {"pattern": "**/.env*"}),
        ("Grep", {"pattern": "PASSWORD", "path": ".env"}),
        ("Grep", {"pattern": "PASSWORD", "glob": ".env.*"}),
        ("Bash", {"command": "cat .env"}),
        ("Bash", {"command": "grep MQTT ./.env.local"}),
        ("Bash", {"command": "source .env && pytest"}),
        ("Bash", {"command": "cp .env /tmp/x"}),
        ("Bash", {"command": "ls secrets/"}),
        ("Bash", {"command": "ls secrets"}),
        ("Bash", {"command": "printenv"}),
        ("Bash", {"command": "printenv BUSPROOF_MQTT_PASSWORD"}),
        ("Bash", {"command": "env"}),
        ("Bash", {"command": "make test; env | sort"}),
        ("Bash", {"command": "docker compose config"}),
        ("Bash", {"command": "docker-compose -f demo/compose.yaml config"}),
    ],
)
def test_it_refuses_what_touches_a_secret(tool, args):
    reason = check(tool, args)
    assert reason is not None
    assert "AGENTS.md" in reason


@pytest.mark.parametrize(
    ("tool", "args"),
    [
        ("Read", {"file_path": ".env.example"}),
        ("Edit", {"file_path": "/home/me/busproof/.env.example"}),
        ("Read", {"file_path": "src/busproof/__init__.py"}),
        ("Read", {"file_path": ".envrc.md"}),
        ("Grep", {"pattern": "\\.env", "path": "src"}),
        ("Grep", {"pattern": "secrets"}),
        ("Glob", {"pattern": "**/*.py"}),
        ("Bash", {"command": "make check"}),
        ("Bash", {"command": "git diff .env.example"}),
        ("Bash", {"command": "python -c 'import os; os.environ'"}),
        ("Bash", {"command": "node -e 'console.log(process.env.HOME)'"}),
        ("Bash", {"command": "uv run --env-file=none pytest"}),
        ("Bash", {"command": "git log --oneline"}),
        ("Bash", {"command": "docker compose up -d"}),
        ("Bash", {"command": "grep -rn keyboard docs/"}),
    ],
)
def test_it_lets_ordinary_work_through(tool, args):
    assert check(tool, args) is None


def run_guard(stdin: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(GUARD)], input=stdin, capture_output=True, text=True, check=False
    )


def test_a_refusal_exits_with_2_and_explains_itself_on_stderr():
    call = {"tool_name": "Read", "tool_input": {"file_path": ".env"}}
    result = run_guard(json.dumps(call))
    assert result.returncode == 2
    assert "environment file" in result.stderr


def test_an_allowed_call_exits_with_0():
    call = {"tool_name": "Read", "tool_input": {"file_path": "README.md"}}
    assert run_guard(json.dumps(call)).returncode == 0


def test_input_it_cannot_read_is_refused_not_waved_through():
    result = run_guard("this is not json")
    assert result.returncode == 2
    assert "could not check" in result.stderr
