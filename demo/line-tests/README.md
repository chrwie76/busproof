# line-tests — the test project for the packaging line

Written the way a customer writes tests with BusProof, and laid out so it could be its own
repository: it depends on `busproof` like any other package and uses only its public interface.

What will be here (milestone M1, filled further in M2):

| File | Purpose | Known from Playwright |
| --- | --- | --- |
| `pyproject.toml` | Depends on `busproof` | `package.json` |
| `busproof.toml` | Environments, timeouts, stance, reporters | `playwright.config.ts` |
| `conftest.py` | Fixtures in layers: `bus` → `line` → `running_line` | fixtures with `test.extend` |
| `machines/` | Machine objects: `filler.py`, `capper.py`, `line.py` | page objects |
| `tests/control/` | States, commands, refused commands | `tests/<app>/ui` … |
| `tests/product/` | What the line makes: good units, rejects, the balance in and out | |
| `tests/timing/` | Latencies, dwell times, ordering | |

The three test folders are the three things to check from docs/IDEAS.md §4: control, product,
timing — a control suite alone can run green on a line that makes nothing.
