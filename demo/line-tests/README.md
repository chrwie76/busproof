# line-tests — the test project for the packaging line

Written the way a customer writes tests with BusProof, and laid out so it could be its own
repository: it depends on `busproof` like any other package and uses only its public interface
(a test checks that).

| File | Purpose | Known from Playwright |
| --- | --- | --- |
| `pyproject.toml` | Depends on `busproof`; the pytest settings | `package.json` |
| `busproof.toml` | One section per environment; `BUSPROOF_ENV` picks one | `playwright.config.ts` |
| `conftest.py` | Fixtures in layers: `bus` (from BusProof) → `line` → `idle_line` → `running_line` | fixtures with `test.extend` |
| `machines/` | Machine objects: `filler.py`, `capper.py`, `inspector.py`, `line.py`; `state.py` says what the numbers mean | page objects |
| `tests/fat/` | Factory acceptance: one machine alone, without the line | |
| `tests/control/` | States, commands, refused commands | `tests/<app>/ui` … |
| `tests/product/` | What the line makes: good units, rejects | |
| `tests/timing/` | Reports that keep coming; later latencies, dwell times, ordering | |
| `stand_in.py` | Plays the machines over a fake bus until the real plant exists (M2) | a mocked backend |

The three test folders are the three things to check from docs/IDEAS.md §4: control, product,
timing — a control suite alone can run green on a line that makes nothing.

## Running

```
make line-tests                                  # offline, against the stand-in
make fat                                         # tests/fat on a real broker, in Docker
cd demo/line-tests && BUSPROOF_ENV=ci uv run pytest   # against a real broker and plant (M2)
```

No test here names a topic: they come from the contracts in `../contracts/`. The stand-in reads
the same contracts, but it is no simulation — a green run against it proves the wiring of this
project, not a plant.
