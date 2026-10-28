# CLAUDE.md

BusProof: a Python test language for asynchronous interfaces (REST, MQTT, OPC UA), with a demo
plant to show it. Principles: [docs/IDEAS.md](docs/IDEAS.md).

## Commands

`make check` runs lint, types and tests (as CI does); `make` lists the rest.

## Rules

- **Written from scratch.** Do not copy code or text from other local repositories; ideas are
  welcome, implementations are written fresh here.
- Keep the core small. A new concept or command needs a reason a user would recognise.
- Every piece gets a test; tests of the library run offline.
- Public repo: English in code, docs and commit messages.
