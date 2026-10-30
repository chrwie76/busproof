# schemas — the official rules a contract is checked against

`asyncapi-3.0.0.json` is the JSON Schema of AsyncAPI 3.0.0, published by the AsyncAPI
Initiative under the Apache License 2.0. Taken unchanged, so a test can check every machine
contract offline (`tests/repo/test_contracts.py`):

- Source: https://github.com/asyncapi/spec-json-schemas, `schemas/3.0.0-without-$id.json`
- Commit: `eee8d2217d23b22c475090c0e12f20801f531f11`, fetched 2026-10-29
- SHA-256: `acefdddecb7909e2e6335f49b5acf222cf6170e303e51ab7824123981d7adfa0`

The schema checks how a contract is *built* — required fields, allowed keys, types. What only
the JavaScript parser of AsyncAPI checks, such as a parameter appearing in its address, our own
tests check next to it.
