# Working on BusProof

## Setup

Ubuntu (22.04 or newer) with [uv](https://docs.astral.sh/uv/) and `make`. uv installs the right
Python itself — the system Python does not matter.

```bash
make install   # .venv + dependencies + Git hooks
make check     # lint, types, tests — exactly what CI runs
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
| `.editorconfig` | Same whitespace in every editor | — |
| `.gitattributes` | Line endings are LF everywhere | — |
| `.venv/` | The virtual environment, created by uv — never committed | `node_modules/` |

Coming in later milestones: `busproof.toml` (settings of a test project, the counterpart of
`playwright.config.ts`), `.env.example` (addresses and credentials, documented) and
`docker-compose.yml` (the demo plant).

## Rules

- Every piece gets a test; the library's tests run offline.
- Small files, plain functions; a docstring says *why* a module exists.
- The version comes from the Git tag — there is no version number to edit.
