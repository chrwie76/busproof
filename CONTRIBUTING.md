# Working on BusProof

## Setup

Ubuntu (22.04 or newer) with [uv](https://docs.astral.sh/uv/) and `make`. uv installs the right
Python itself — the system Python does not matter.

```bash
make install   # .venv + dependencies + Git hooks
make check     # lint, types, tests, all offline — as CI runs them
make           # list all commands
```

## What each file in the root is for

If you know a Node/Playwright project, the right-hand column is the file you already know.

| File | What it does | Known from |
| --- | --- | --- |
| `pyproject.toml` | Name, dependencies, settings of pytest, ruff and pyright | `package.json`, `tsconfig.json` |
| `uv.lock` | Exact versions of every dependency — commit it, never edit it | `package-lock.json` |
| `.python-version` | The Python we develop on (3.13); `requires-python` says the oldest supported (3.12) | `.nvmrc`, `engines` |
| `Makefile` | The command menu | `scripts` in `package.json` |
| `.pre-commit-config.yaml` | Git hooks: lint before a commit, all checks before a push | husky + lint-staged |
| `.github/workflows/ci.yml` | CI: `make check` on Python 3.12 and 3.13 | `.gitlab-ci.yml`, `Jenkinsfile` |
| `.github/workflows/release.yml` | A tag like `v0.2.0` publishes to TestPyPI, then PyPI, with no password stored | a publish pipeline |
| `.github/pull_request_template.md` | Prefills every pull request: what and why, provenance, evidence, acceptance | GitLab merge request templates |
| `.github/dependabot.yml` | A monthly pull request when an action or dependency is outdated | Renovate |
| `AGENTS.md` | Rules for every AI assistant, above all: secrets are off limits | — |
| `.claude/settings.json` | Permission rules and the guard hook for Claude Code | — |
| `.claude/hooks/guard.py` | Refuses a tool call that touches a secret; runs before every call | a husky hook script |
| `.editorconfig` | Same whitespace in every editor | — |
| `.gitattributes` | Line endings are LF everywhere | — |
| `.venv/` | The virtual environment, created by uv — never committed | `node_modules/` |

## Where things live

| Folder | What | Its tests |
| --- | --- | --- |
| `src/busproof/` | the library | `tests/` — one file per module, same name: `expect.py` ↔ `test_expect.py` |
| repository files | the guard, packaging | `tests/test_guard.py`, `tests/test_package.py` |
| `docs/` | IDEAS (why), CONCEPT (what, and in which order) | — |

Shared fixtures of the tests (`bus`, `clock`, `deliver_later`) are in `tests/conftest.py`. A plant
and a test project that uses the library have a repository of their own.

## Rules

- Every piece gets a test; the library's tests run offline.
- Small files, plain functions; a docstring says *why* a module exists.
- The version comes from the Git tag — there is no version number to edit.
