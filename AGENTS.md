# AGENTS.md

Rules for every AI assistant working in this repository: Claude Code, Copilot, Cursor and the
agents that the playbook and its skills start. A person working here follows them too.

## Two sets of rules

This repository holds the tool and a test project that uses it. The test project brings its own
rules, so they hold when someone opens only that folder — as a user of BusProof would.

- **[test-project/AGENTS.md](test-project/AGENTS.md) applies in the whole repository:** secrets
  are off limits, and the contract is the truth. Read it first. It is the one place these rules
  are written down.
- **This file adds what only building BusProof needs.**

## What enforces the rules on secrets here

| Where | What |
| --- | --- |
| `.claude/settings.json` | Permission rules: Claude Code may not read or edit secret files. Its hook is the test project's guard. |
| `test-project/.claude/hooks/guard.py` | Runs before every tool call of Claude Code and refuses calls that touch a secret, also through the shell. Tested in `tests/repo/test_guard.py`. |
| `.pre-commit-config.yaml` | gitleaks scans every commit for secrets — for people and agents alike. |

Claude Code reads its settings from the folder it is started in. Started at the root, these
settings apply; started in `test-project/`, that folder's own do.

## The contract, when building the plant

What the test project's rule says of a test holds for the plant too: it may use only what the
contracts in `contracts/` say. Adding something to a contract is a decision for a person
(docs/PLAYBOOK.md, step 1).

## Working here

- `make check` must be green before work is handed over.
- Commit on a branch; a person pushes. Never rewrite history that may already be pushed.
