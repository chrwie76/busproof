# contracts — what the plant should do

The agreement between the plant and its tests (docs/CONCEPT.md, decisions 13, 22, 23 and 26). The
plant gets this folder mounted and is built to it; the test project points to it in its
`busproof.toml`. Neither owns it.

| File | Answers |
| --- | --- |
| `machines/<machine>.asyncapi.yaml` | How one machine **talks**: its topics, payloads, types, ranges. Standard AsyncAPI 3.0, one per machine — as each machine builder delivers its own interface. |
| `scu.asyncapi.yaml` | How the central unit of the line **talks**: line commands, the line state it claims, why it reacted. |
| `packml.yaml` | How a machine or the SCU **behaves**: its states, their numbers on the wire, the commands each state accepts, where an acting state goes on its own. |
| `line.yaml` | How the machines make a **line**: which ones, in which order, where it stands (`acme/plant1/packaging/line1`), and what the SCU should do: start and stop order, reaction to a fault. |

A machine contract does not say where the machine stands: its topics start with
`{enterprise}/{site}/{area}/{line}/`, filled in by `line.yaml`. So one contract serves a test at
the maker's (FAT) and in the plant (SAT). `line.yaml` is mounted into every machine's service
and read by the tests — one source for the address both sides use (decision 21).

`make check` validates these files: each machine contract against the official AsyncAPI 3.0
schema, and all of them against each other (`tests/repo/test_contracts.py`).

Not here: how the web page draws a machine (that is the page's business) and the physics of the
simulation (that is `plant/config.json`).
