# plant — the system under test

A small simulation of a packaging line (filler → capper → inspector) that publishes over MQTT in
a Unified Namespace, follows the PackML state model, and has a web page to watch it and to switch
faults on. It is the *system*: it knows nothing of BusProof and speaks only its contract.

Each machine runs as a **service of its own** — one image, started as `filler`, `capper` or
`inspector` — with `../contracts/` mounted: `line.yaml` tells it where it stands, its AsyncAPI
file what it publishes, `packml.yaml` how it behaves. So one machine can be started and tested
alone, or stopped while the others run.

## Running it

```
make line-tests                           # the whole plant, with its tests
make fat                                  # the capper alone, with its tests
docker compose -f demo/compose.yaml up    # the whole plant, to look at
```

The broker listens on port 1884 of this computer, so the demo can run next to another broker on
1883; `BUSPROOF_MQTT_PORT` changes it.

## What is here

| File | Purpose |
| --- | --- |
| `pyproject.toml`, `Dockerfile` | The plant as a package and as one image for all machines |
| `src/plant/machine.py` | What every machine does: follow the state machine, take parameters, report. No MQTT in it |
| `src/plant/filler.py`, `capper.py`, `inspector.py` | What only that machine does, in a few lines |
| `src/plant/scu.py` | The central unit: passes commands on in order, reports the line state it claims, reacts to a machine that fails or is gone |
| `src/plant/contracts.py` | Reads the mounted contracts. There is no fallback copy: a missing file stops the service |
| `src/plant/link.py` | The one place that touches a bus, so another protocol replaces this file only |
| `config.json` | The state the plant starts in, and its pace |
| `tests/` | The plant's own tests: does the simulation compute right? Tests *of* the plant are in `../line-tests` |

A unit reports its whole state after a command, on every change and as a heartbeat. Its MQTT
last will says when it is gone.

Still to come in M2: bottles that travel (the inspector judges none yet), faults to switch on, and
the web page (`web/index.html`).
