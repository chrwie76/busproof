# BusProof

**Make your system bus-proof.** A Python test language for asynchronous industrial interfaces, with
a demo plant to show it.

> **🚧 Work in progress.** It works, and the demo runs, but the interface can still change and
> nothing is on PyPI yet. Where it stands: milestone 2 of 8 ([plan](docs/CONCEPT.md#8--milestones--each-one-shows-something)).

An asynchronous system answers a command now and shows its effect later, somewhere else. So a test
waits for the system, and a failure says what it saw:

```python
await running_line.filler.set(fill_target=80.0)  # the filler fills too little...

await asyncio.gather(
    expect(running_line.inspector.reject_count).rises_by(2, within=20),  # ...seen only at the end
    expect(running_line.filler.state).remains(during=8),  # while the start looks fine
)
```

```
expected inspector.reject_count to rise by 2 within 20s — it rose by 0; seen: 0 (41 messages)
```

## What is where

One repository, four folders — one for each party a test involves:

| Folder | What it is | In real life |
| --- | --- | --- |
| [library/](library/) | BusProof itself, published as the package `busproof` | the tool you install |
| [plant/](plant/) | The system under test: a simulated packaging line, its broker and its web page | the machine builder's product |
| [contracts/](contracts/) | How the plant talks and how it behaves: one AsyncAPI file per unit, `packml.yaml`, `line.yaml` | the interface agreement between the plant's maker and its testers |
| [test-project/](test-project/) | The tests of the plant, written with BusProof | your own test repository |

To write a test, open `test-project/` on its own, as a folder — it is laid out like a test project
of your own, and brings its rules for AI assistants with it. To change the language, open
`library/`. Three rules keep
the folders apart; tests in `tests/repo/` check the second and the third:

1. **The tool knows no plant.** Nothing in `library/` names a machine, a bottle or a topic of this
   line.
2. **The plant knows nothing of BusProof.** A system does not know the tool it is tested with; it
   speaks only its contract.
3. **The test project uses BusProof the way any customer would** — through `from busproof import …`,
   with its own `pyproject.toml` and `busproof.toml`. If it needs something the library does not
   offer, that is a change to the library, not a workaround there.

## What works today

- **`expect` that waits:** `to_be`, `rises_by`, `remains`. Silence does not count as stability.
- **Tests that name no topic:** machines are written like page objects, and addresses come from the
  contracts (AsyncAPI 3.0). A name the contract does not have fails at once.
- **MQTT** with TLS and login. Every message is recorded as evidence, also those no contract knows.
- **Plain pytest:** fixtures come with the package, and one setting picks the environment.

## The demo

A small bottling line in Docker: a filler, a capper and an inspector following PackML, a central
unit that coordinates them, and a web page to watch and use it. Stop a machine or set the filler too
low, and watch what the line does. Its tests run on a real broker and switch real faults on, to show
that they catch them.

```bash
make install     # needs Ubuntu, Docker, uv and make
make demo        # the line, at http://localhost:8088; it says how to log in
make line-tests  # its tests, about five minutes, as bottles take real time
make demo-down
```

## Not there yet

REST and OPC UA, the evidence reports, the agent skills, and a release on PyPI. The
[playbook](docs/PLAYBOOK.md) describes only the steps tried so far.

## License

[Apache-2.0](LICENSE) · Working on it: [CONTRIBUTING.md](CONTRIBUTING.md)
