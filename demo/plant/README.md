# plant — the system under test

A small simulation of a packaging line (filler → capper → inspector) that publishes over MQTT in
a Unified Namespace, follows the PackML state model, and has a web page to watch it and to switch
faults on. It is the *system*: it knows nothing of BusProof and speaks only its contract.

Each machine runs as a **service of its own** — one image, started as `filler`, `capper` or
`inspector` — with `../contracts/` mounted: `line.yaml` tells it where it stands, its AsyncAPI
file what it publishes, `packml.yaml` how it behaves. So one machine can be started and tested
alone, or stopped while the others run.

## Running one machine

```
make fat                                  # the capper alone, on a real broker, with its tests
docker compose -f demo/compose.yaml up    # the broker and the machines there are so far
```

The broker listens on port 1884 of this computer, so the demo can run next to another broker on
1883; `BUSPROOF_MQTT_PORT` changes it.

## What is here

| File | Purpose |
| --- | --- |
| `pyproject.toml`, `Dockerfile` | The plant as a package and as one image for all machines |
| `src/plant/machine.py` | What every machine does: follow the state machine, take parameters, report. No MQTT in it |
| `src/plant/capper.py` | What only the capper does, in a few lines |
| `src/plant/contracts.py` | Reads the mounted contracts. There is no fallback copy: a missing file stops the service |
| `src/plant/link.py` | The one place that touches a bus, so another protocol replaces this file only |
| `config.json` | The state the plant starts in, and its pace |
| `tests/` | The plant's own tests: does the simulation compute right? Tests *of* the plant are in `../line-tests` |

A machine reports its whole state after a command, on every change and as a heartbeat. Its MQTT
last will says when it is gone.

Still to come in M2: the filler, the inspector and the SCU, bottles that travel, faults to switch
on, and the web page (`web/index.html`).
