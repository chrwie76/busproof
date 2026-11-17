# busproof — the library

A Python test language for the behaviour over time of systems that talk through messages. This
folder is the package `busproof`; nothing else in the repository is published.

An asynchronous system answers a command now and shows its effect later, somewhere else. So a test
waits for the system, and a failure says what it saw:

```python
await asyncio.gather(
    expect(line.inspector.reject_count).rises_by(2, within=20),
    expect(line.filler.state).remains(during=8),
)
```

```
expected inspector.reject_count to rise by 2 within 20s — it rose by 0; seen: 0 (41 messages)
```

> **Work in progress.** The interface can still change, and nothing is on PyPI yet.

| Folder | What is in it |
| --- | --- |
| `src/busproof/` | The library. Each module starts with a docstring that says why it exists; `__init__.py` lists what a test project may use. |
| `tests/` | The library's own tests, one file per module: `expect.py` ↔ `test_expect.py`. They run offline. |

MQTT is an optional extra: `busproof[mqtt]`. The core runs without it.

A test project that uses the library, and a plant to try it on, are in the
[repository](https://github.com/chrwie76/busproof).
