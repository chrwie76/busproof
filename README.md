# BusProof

**Make your system bus-proof.** Tests for asynchronous interfaces — events, messages, timing —
from a mocked service to real hardware.

> **Status: M2 of 8 — the language and a demo plant.** What it becomes and in which order:
> [docs/CONCEPT.md](docs/CONCEPT.md). The ideas it is built on: [docs/IDEAS.md](docs/IDEAS.md).
> How to use it, step by step, as far as it is tried: [docs/PLAYBOOK.md](docs/PLAYBOOK.md).

An asynchronous system answers a command now and shows its effect later, somewhere else. So a test
waits for the system, and a failure says what it saw:

```python
async def test_a_low_fill_shows_at_the_end_of_the_line_not_where_it_began(running_line):
    await running_line.filler.set(fill_target=80.0)

    await asyncio.gather(
        expect(running_line.inspector.reject_count).rises_by(2, within=20),
        expect(running_line.filler.state).remains(during=8),
        expect(running_line.capper.reject_count).remains(during=8),
    )
```

```
expected inspector.reject_count to rise by 2 within 20s — it rose by 0; seen: 0 (41 messages)
```

No test names a topic. Signals, commands and parameters come from the contracts (AsyncAPI 3.0), and
a name the contract does not have fails at once, listing those it does.

## See it

The demo is a small bottling line, in Docker, speaking MQTT over TLS: a filler, a capper and an
inspector, each a service of its own and following PackML, an SCU that coordinates them, and a web
page to watch and use it. You need Ubuntu, Docker, [uv](https://docs.astral.sh/uv/) and `make`.

```bash
make install
make demo        # the line, at http://localhost:8088; it says how to log in
make line-tests  # its tests on a real broker, about five minutes, as bottles take real time
make demo-down
```

Stop the capper on the page, behind the SCU's back, and watch the line hold. Set the filler too low,
and see the rejects appear seconds later, at the other end of the line.

What the tests in [demo/line-tests](demo/line-tests) show:

| Fault in the plant | What finds it |
| --- | --- |
| The line shows `Execute` and makes nothing | a product test, while every control test stays green |
| A bottle vanishes without a word | the balance: filled = rejected + passed + on the belt + lost |
| The SCU claims `Execute` before its machines are there | comparing the claim with what the machines report |
| A machine jumps past `Starting` | a check against the state machine in the contract |
| A machine keeps its connection and goes silent | silence is not stability: the SCU holds the line |

You can switch these on yourself: [demo/plant/FAULTS.md](demo/plant/FAULTS.md).

## Use it

From its first release on:

```bash
pip install "busproof[mqtt]"
```

A test project writes one class per machine, like page objects, and points `busproof.toml` at its
contracts. [demo/line-tests](demo/line-tests) is such a project, laid out as your own would be.

## Working on it

See [CONTRIBUTING.md](CONTRIBUTING.md): `make install`, then `make check`.

## License

[Apache-2.0](LICENSE)
