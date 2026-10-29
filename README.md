# BusProof

**Make your system bus-proof.** Tests for asynchronous interfaces — events, messages, timing —
from a mocked service to real hardware.

> **Status: M0 of 8 — skeleton.** What it becomes and in which order:
> [docs/CONCEPT.md](docs/CONCEPT.md). The ideas it is built on: [docs/IDEAS.md](docs/IDEAS.md).

```python
from busproof import expect


async def test_the_line_delivers_good_units(line):
    await line.start()
    await expect(line.qc.signal("PassCount")).to_increase(by=3, within_s=30)
```

## Working on it

See [CONTRIBUTING.md](CONTRIBUTING.md): `make install`, then `make check`.

## License

[Apache-2.0](LICENSE)
