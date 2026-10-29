# contracts — what the plant should do

Two files, each answering one question (docs/CONCEPT.md, decisions 13 and 14):

- `asyncapi.yaml` — how the plant **talks**: topics, payloads, types, ranges. Standard AsyncAPI 3.0.
- `line.yaml` — how the plant **behaves**: machines and their signals, PackML states, commands
  and the states they are allowed in, setpoints, alarms, the flow of units. It refers to the
  AsyncAPI channels by name.

The plant gets this folder mounted and is built to it; the test project points to it in its
`busproof.toml`. Neither owns it — it is the agreement between them.

Not here: how the web page draws a machine (that is the page's business) and the physics of the
simulation (that is `plant/config.json`).
