# line-tests — the test project for the packaging line

Written the way a customer writes tests with BusProof, and laid out so it could be its own
repository: it depends on `busproof` like any other package and uses only its public interface
(a test checks that).

| File | Purpose | Known from Playwright |
| --- | --- | --- |
| `pyproject.toml` | Depends on `busproof`; the pytest settings | `package.json` |
| `busproof.toml` | One section per environment; `BUSPROOF_ENV` picks one | `playwright.config.ts` |
| `conftest.py` | Fixtures in layers: `bus` (from BusProof) → `line` → `idle_line` → `running_line`; each brings the plant to a known state first | fixtures with `test.extend` |
| `machines/` | Machine objects: `filler.py`, `capper.py`, `inspector.py`, `scu.py`, `line.py`; `state.py` says what the numbers mean | page objects |
| `tests/fat/` | Factory acceptance: one machine alone, without the line | |
| `tests/control/` | States, commands, refused commands; what the SCU does and what it claims | `tests/<app>/ui` … |
| `tests/product/` | What the line makes: good bottles, rejects, a fault that shows only at the end, the balance | |
| `tests/timing/` | Reports that keep coming, how long a bottle travels, a belt that stands still in a hold | |
| `tests/scenarios/` | The plant started from other settings, with `@pytest.mark.scenario(...)` | |
| `tests/faults/` | Each fault of the simulation switched on: the check meant for it has to find it | |
| `checks.py` | Checks over a whole recording: the balance, the state machine, a counter going down | |

The three test folders are the three things to check from docs/IDEAS.md §4: control, product,
timing — a control suite alone can run green on a line that makes nothing.

## Running

```
make line-tests                                  # the whole line, in Docker, on a real broker
make fat                                         # tests/fat: the capper alone
```

Both start the plant, run the tests and clean up; the whole line takes about four minutes, as a
bottle needs real time to travel. To run against a plant already running:

```
cd demo/line-tests && BUSPROOF_MQTT_URL=mqtt://localhost:1884 uv run pytest
```

No test here names a topic: they come from the contracts in `../contracts/`.
