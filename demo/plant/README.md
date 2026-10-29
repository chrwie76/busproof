# plant — the system under test

A small simulation of a packaging line (filler → capper → inspector) that publishes over MQTT in
a Unified Namespace, follows the PackML state model, and has a web page to watch it and to switch
faults on. It is the *system*: it knows nothing of BusProof and speaks only its contract.

What will be here (milestone M2):

| File | Purpose |
| --- | --- |
| `pyproject.toml`, `Dockerfile` | The plant as a package and as an image |
| `src/plant/` | The simulation |
| `config.json` | The state the plant starts in: levels, counters, speed, active faults, random seed, physics — one file per scenario |
| `web/index.html` | The page: live states and counters over MQTT WebSockets, buttons for the faults |
| `tests/` | The plant's own tests — does the simulation compute right? Not tests *of* the plant; those are in `../line-tests` |
