# CLAUDE.md

BusProof: a Python test language for the behaviour over time of systems that talk through
messages. This repository is the library only; a test project that uses it, with a demo plant,
has a repository of its own. Principles: [docs/IDEAS.md](docs/IDEAS.md). What is not built yet: [docs/ROADMAP.md](docs/ROADMAP.md).

Rules for every agent, above all about secrets: @AGENTS.md

## Commands

`make check` runs lint, types and tests (as CI does); `make` lists the rest.

## Rules

- **Written from scratch.** Do not copy code or text from other local repositories; ideas are
  welcome, implementations are written fresh here.
- Keep the core small. A new concept or command needs a reason a user would recognise.
- Every piece gets a test; tests of the library run offline.
- Public repo: English in code, docs and commit messages.
