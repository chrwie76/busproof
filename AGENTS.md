# AGENTS.md

Rules for every AI assistant working in this repository: Claude Code, Copilot, Cursor and the
agents that the playbook and its skills start. A person working here follows them too.

## Secrets are off limits

This repository needs no secret: the library's tests run offline. The rules hold all the same.

- **Never open, write, search, copy, print or quote** a file that holds secrets: `.env` and
  every `.env.*` except a template `.env.example`, anything in a `secrets/` folder, and key
  files (`*.pem`, `*.key`).
- **Never print the environment** — no `printenv`, no bare `env`, no `docker compose config`
  (it shows the Compose file with `.env` filled in).
- **Such a file open or selected in the editor?** Stop at once, quote nothing from it, and ask
  for it to be closed. Continue only when it is.
- **A secret reached you anyway?** Do not use it. Say that you saw one, so a person can replace
  it.

### What enforces this

| Where | What |
| --- | --- |
| `.claude/settings.json` | Permission rules: Claude Code may not read or edit secret files. |
| `.claude/hooks/guard.py` | Runs before every tool call of Claude Code and refuses calls that touch a secret, also through the shell. Tested in `tests/test_guard.py`. |
| `.pre-commit-config.yaml` | gitleaks scans every commit for secrets — for people and agents alike. |

The editor rule cannot be enforced by a tool: a guard does not see what is open in the editor.
It holds because every agent here reads this file.

## The contract is the truth

- **Never invent a topic, payload field, state or command.** What a test may use is what the
  contracts of the system under test say. A guessed topic makes a test that checks nothing.
- **The library names no plant.** Nothing in `src/busproof` knows a machine, a bottle or a topic
  of any particular line.

## Working here

- `make check` must be green before work is handed over.
- Commit on a branch; a person pushes. Never rewrite history that may already be pushed.
