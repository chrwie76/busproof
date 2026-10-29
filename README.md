# BusProof

**Make your system bus-proof.** Tests for asynchronous interfaces — events, messages, timing —
from a mocked service to real hardware.

> **Status: M1 of 8 — the language, in progress.** What it becomes and in which order:
> [docs/CONCEPT.md](docs/CONCEPT.md). The ideas it is built on: [docs/IDEAS.md](docs/IDEAS.md).
> How to use it, step by step, as far as it is tried: [docs/PLAYBOOK.md](docs/PLAYBOOK.md).

```python
import asyncio

from busproof import expect


async def test_the_line_makes_good_units_and_no_rejects(line):
    await line.start()
    await expect(line.state).to_be("Execute", within=10)
    await asyncio.gather(
        expect(line.capper.good_count).rises_by(5, within=30),
        expect(line.inspector.reject_count).remains(during=30),
    )
```

Every matcher waits until the system agrees or the time is up — and a failure says what it saw:

```
expected capper.good_count to rise by 5 within 30s — it rose by 2; seen: 120 → 121 → 122 (2 messages)
```

## Working on it

See [CONTRIBUTING.md](CONTRIBUTING.md): `make install`, then `make check`.

## License

[Apache-2.0](LICENSE)
