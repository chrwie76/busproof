# BusProof

**Make your system bus-proof.** A Python test language for asynchronous industrial interfaces.

> **🚧 Work in progress.** The library works and is tested, but its interface can still change
> and nothing is on PyPI yet.

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

## What works today

- **`expect` that waits:** `to_be`, `rises_by`, `remains`. Silence does not count as stability.
- **Tests that name no topic:** machines are written like page objects, and addresses come from the
  contracts (AsyncAPI 3.0). A name the contract does not have fails at once.
- **MQTT** with TLS and login. Every message is recorded as evidence, also those no contract knows.
- **Plain pytest:** fixtures come with the package, and one setting picks the environment.

## The demo

A small bottling line in Docker — a filler, a capper and an inspector following PackML, a central
unit that coordinates them, and a web page to watch and use it — with a test project that runs on
a real broker and switches real faults on, to show that the tests catch them.

The demo is moving to a repository of its own, laid out the way a test project of yours would be:
clone it, install, start the plant, run the tests. This repository stays the library. The link
will be here when the demo repository is public.

## Working on the library

```bash
make install     # needs Ubuntu, uv and make
make check       # style, types and the tests; they need no broker and no network
```

## Not there yet

REST and OPC UA, the evidence reports, the agent skills, and a release on PyPI. The
playbook — the steps from a contract to a test that catches a fault — moved with the demo.

## License

[Apache-2.0](LICENSE) · Working on it: [CONTRIBUTING.md](CONTRIBUTING.md)
