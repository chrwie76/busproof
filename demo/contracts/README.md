# contracts — what the plant should do

The agreement between the plant and its tests (docs/CONCEPT.md, decisions 13, 22 and 23). The
plant gets this folder mounted and is built to it; the test project points to it in its
`busproof.toml`. Neither owns it.

| File | Answers |
| --- | --- |
| `machines/<machine>.asyncapi.yaml` | How one machine **talks**: its topics, payloads, types, ranges. Standard AsyncAPI 3.0, one per machine — as each machine builder delivers its own interface. |
| `packml.yaml` | How a machine **behaves**: its states, their numbers on the wire, the commands each state accepts, where an acting state goes on its own. |
| `line.yaml` | How the machines make a **line**: which ones, in which order, and where it stands (`acme/plant1/packaging/line1`). *Comes next.* |

A machine contract does not say where the machine stands: its topics start with
`{enterprise}/{site}/{area}/{line}/`, filled in by the line. So one contract serves a test at
the maker's (FAT) and in the plant (SAT).

Not here: how the web page draws a machine (that is the page's business) and the physics of the
simulation (that is `plant/config.json`).
