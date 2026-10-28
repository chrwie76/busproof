# BusProof

**Make your system bus-proof.** Tests for asynchronous interfaces — events, messages, timing —
from a mocked service to real hardware.

> Early days. The ideas this is built on: [docs/IDEAS.md](docs/IDEAS.md).

```python
from busproof import expect

async def test_the_line_delivers_good_units(line):
    await line.start()
    await expect(line.qc.signal("PassCount")).to_increase(by=3, within_s=30)
```

## License

[Apache-2.0](LICENSE)
