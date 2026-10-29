# demo — a customer's world, built to show BusProof

Everything outside this folder is the tool. Everything inside is what a team that *uses* the tool
would have: a system, the agreement on how it talks, and a test project for it.

| Folder | What it is | In real life |
| --- | --- | --- |
| [contracts/](contracts/) | How the plant talks and how it behaves: `asyncapi.yaml`, `line.yaml` | the interface agreement between the plant's maker and its testers |
| [plant/](plant/) | The system under test: a simulated packaging line and its web page | the machine builder's product |
| [line-tests/](line-tests/) | The test project, written with BusProof | the customer's test repository |

## Three rules keep the parts apart

1. **The tool knows no plant.** Nothing under `src/busproof` names a machine, a bottle or a topic
   of this line.
2. **The plant knows nothing of BusProof.** A system does not know the tool it is tested with; it
   speaks only its contract.
3. **The test project uses BusProof the way any customer would** — through `from busproof import …`,
   with its own `pyproject.toml` and `busproof.toml`. If it needs something the library does not
   offer, that is a change to the library, not a workaround here.

Because of these rules, each part could move to a repository of its own unchanged: the plant as a
Docker image with its contracts, the test project as a template others start from.

Status: the folders are placed; they are filled in milestones M1 (line-tests) and M2 (plant,
contracts, `compose.yaml`).
