# AGENTS.md

Rules for every AI assistant working in this test project: Claude Code, Copilot, Cursor. A person
working here follows them too. The project brings these rules and what enforces them itself, so
they hold when this folder is opened on its own — the way a test project of your own would be.

## Secrets are off limits

- **Never open, write, search, copy, print or quote** a file that holds secrets: `.env` and
  every `.env.*` except the template `.env.example`, anything in a `secrets/` folder, and key
  files (`*.pem`, `*.key`).
- **Never print the environment** — no `printenv`, no bare `env`, no `docker compose config`
  (it shows the Compose file with `.env` filled in).
- **Need a new variable?** Add its name with a comment to `.env.example`, leave a secret's value
  empty, and ask a person to set it in their `.env`.
- **Such a file open or selected in the editor?** Stop at once, quote nothing from it, and ask
  for it to be closed. Continue only when it is.
- **A secret reached you anyway?** Do not use it. Say that you saw one, so a person can replace
  it.

### What enforces this

| Where | What |
| --- | --- |
| `.claude/settings.json` | Permission rules: Claude Code may not read or edit secret files. |
| `.claude/hooks/guard.py` | Runs before every tool call of Claude Code and refuses calls that touch a secret, also through the shell. |

The editor rule cannot be enforced by a tool: a guard does not see what is open in the editor.
It holds because every agent here reads this file.

## The contract is the truth

- **Never invent a topic, payload field, state or command.** What a test may use is what the
  contracts say (`../contracts/` here; your own elsewhere). A guessed topic makes a test that
  checks nothing.
- **Something missing from the contract?** Say so and ask; do not fill the gap. Adding it is a
  decision for a person.
