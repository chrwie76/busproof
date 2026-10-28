# Concept — what BusProof becomes, and in which order

> Draft v1, 2026-10-28. Written to be argued with. [IDEAS.md](IDEAS.md) holds the *why*; this
> document holds the *what* and the *order*. When a decision here is made, it moves out of §9.

## 1 · In one sentence

**BusProof is a Python test language for asynchronous industrial interfaces (IIoT) — with the
knowledge, demos and agent skills to use it — so a team can point it at an MQTT-, REST- or
OPC UA-connected system described by AsyncAPI or OpenAPI and end up with a pytest suite that
catches real faults.**

## 2 · Who it is for, and what they see first

| Reader | What they need to see in five minutes |
| --- | --- |
| A test engineer with an IIoT system (MQTT, OPC UA, MES) | A test that reads like the requirement, and a failure that explains itself. |
| A developer of one service | The same tests in their CI against a mocked neighbour. |
| A reviewer of this repository (CV) | `make demo` → a plant runs, a test turns red on a real fault, a report says why. Clean, small, tested code. |

The third reader is not a side effect. Every milestone below ends in something that reader can
run or look at.

## 3 · Where it sits — what others already do

| Tool | What it does well | What it does not do |
| --- | --- | --- |
| **Microcks** (CNCF, Java) | Mocks and conformance tests from OpenAPI/AsyncAPI | Behaviour over time: states, timing, product |
| **Specmatic** (Docker) | Contract tests and mocks across many brokers | A language you write your own scenarios in |
| **Schemathesis** (Python) | Property-based fuzzing of REST APIs | Asynchronous events |
| **Pact** | Consumer-driven contracts, also for messages | Testing a running system end to end |
| **Playwright** | A test language that waits, for browsers | Buses |

**The gap BusProof fills:** a Python-native *language* for asserting the **behaviour** of an
asynchronous system — "after `start`, good units come out and no rejects are added within 30 s"
— not only whether one message matches its schema. Schema conformance is a solved problem; we
use it (e.g. via `jsonschema`), we do not rebuild it.

## 4 · Four layers

```
┌──────────────────────────────────────────────────────────────┐
│ 4  Agent layer   skills + playbooks (Markdown), later MCP    │  optional
├──────────────────────────────────────────────────────────────┤
│ 3  Demos         demo plant (REST + MQTT), example suites    │  in the repo
├──────────────────────────────────────────────────────────────┤
│ 2  Knowledge     contract import (AsyncAPI, OpenAPI),        │
│                  templates, test ideas, types                │
├──────────────────────────────────────────────────────────────┤
│ 1  Core          things · signals · expect · bus adapters    │  small, no AI
└──────────────────────────────────────────────────────────────┘
```

Each layer uses only the layers below it. The core never imports an AI library, and the agent
layer is mostly text, not code.

### 4.1 Core — the part that must stay small

- `Thing`, `Signal`, `Command` — the vocabulary of a test ([IDEAS §1](IDEAS.md#1--a-test-language-not-a-test-factory)).
- `expect(...)` — matchers that wait and say what they saw.
- `Bus` — one small interface (`read`, `watch`, `send`), one adapter per protocol. MQTT first,
  REST second, OPC UA third.
- A pytest plugin that provides the fixtures and reports *inconclusive* honestly.

Target size for the first release: **under 1 500 lines of library code.**

### 4.2 Knowledge — what turns a spec into a head start

- **Contract import.** AsyncAPI 3.0 and OpenAPI 3.x are the two formats we read; both are
  normalised into one small internal contract (things, signals, commands, states).
- **Test ideas** derived from the contract, deterministically: state transitions, refused
  commands, boundary values. Printed as a checklist, not as generated test files.
- **Templates**: a handful of copyable test files (`control`, `product`, `timing`) and a
  `conftest.py` — examples, not a scaffold.
- **Knowledge pages**: short docs on testing asynchronous systems (bus personalities, waiting,
  oracles, honest verdicts). This is where test-management experience goes in, written down.
- **Two languages.** English is the source. Selected pages (README, getting started) have a
  German version that records the hash of its English source; a test fails when the source
  changed and the translation did not — drift detection, applied to our own docs.

### 4.3 Demos — the fastest proof

- A **demo plant**: a small simulated **packaging line** (filler → capper → inspector).
  - Each machine follows the **PackML** state model (ISA-TR88: `Idle`, `Starting`, `Execute`,
    `Held`, `Aborted`, …) — an industry standard that also exercises acting states.
  - It publishes over **MQTT** in a **Unified Namespace** (ISA-95 hierarchy, e.g.
    `acme/plant1/packaging/line1/capper/state`), described by an **AsyncAPI 3.0** file.
  - A small **MES** service takes production orders over **REST** (OpenAPI) and reads the line
    over MQTT — so the demo has two systems, and the interplay is what is tested.
  - Later: **Sparkplug B** payloads and an **OPC UA** server for the same line.
- A **fault switch** in the plant (`stuck sensor`, `slow capper`, `silent rejects`) so a demo
  can show a suite catching a fault — and a control-only suite missing one.
- One command starts it: **`docker compose up`** (Mosquitto + plant + MES + panel). The project
  needs no external broker; an own broker is used by setting its address in the environment.
- Supported platform: **Ubuntu** (also GitHub Actions). Docker Desktop on Windows/macOS should
  work but is not tested.

### 4.4 Agent layer — skills and playbooks

What a good harness for agents needs, from looking at others:

- **A narrow action space.** A few well-named commands (`busproof ideas`, `busproof run`,
  `busproof probe`) the agent calls — no free-form scripting against the bus.
- **Good observations.** Failures that explain themselves are what lets an agent diagnose; this
  is the core's job, not the agent's.
- **Recovery and limits.** A stance (`observe` / `drive` / `inject`) the environment enforces,
  and a hard step budget.
- **A human gate.** An agent proposes a test; a person accepts it (a pull request is enough).

So the agent layer ships as:

- **Skills** (`SKILL.md`, the open format several assistants read): *write a test from a
  requirement*, *diagnose a red run*, *explore a system under a charter*. Each under ~1 000 words,
  with details in referenced files.
- **Playbooks**: step-by-step procedures for a human *or* an agent — "onboard a new system from
  its AsyncAPI file", "triage a failing suite after a spec change".
- **Later, if it earns its upkeep:** an MCP server exposing the same commands.

## 5 · What is deliberately *not* in it (overkill for now)

- A multi-agent framework, LangGraph, or a role-play of "tester agent" and "reviewer agent".
  A plain loop with a gate is enough until it provably is not.
- A vector database or RAG. The contract and a few Markdown pages fit in context.
- A test *generator* that writes files nobody may edit (the lesson in [IDEAS §1](IDEAS.md#1--a-test-language-not-a-test-factory)).
- Its own UI beyond the demo panel and an HTML report.
- Kafka, AMQP, gRPC — until someone needs them. The `Bus` interface keeps the door open.
- A plugin system. Adapters are plain modules.

## 6 · How the code is written — so it stays readable

- **Plain Python 3.12**, `async`/`await`, dataclasses, type hints. No metaclasses, no
  decorators that hide control flow, no dependency injection framework.
- **Small files** (aim < 200 lines), one idea per module, a docstring that says *why* it exists.
- **Few dependencies**: `pytest`, `httpx`, `jsonschema`, `pyyaml`; `paho-mqtt` / `aiomqtt` as an
  optional extra. Each new one needs a sentence in this document.
- **Every module has a test**, and the library's tests run offline with a fake bus.
- **Tooling**: `uv` for environments, `ruff` for lint and format, `pyright` for types, GitHub
  Actions for CI. Version from Git tags.

## 7 · Repository layout (target)

```
busproof/
├─ src/busproof/          core (layer 1) and knowledge (layer 2)
│  ├─ expect.py  thing.py  bus.py  plugin.py
│  ├─ buses/     rest.py  mqtt.py
│  └─ contract/  asyncapi.py  openapi.py  ideas.py
├─ demo/                  the demo plant + its AsyncAPI/OpenAPI files (layer 3)
├─ examples/              example suites against the demo plant
├─ skills/                SKILL.md files (layer 4)
├─ playbooks/             step-by-step procedures (layer 4)
├─ docs/                  IDEAS, CONCEPT, knowledge pages
└─ tests/                 the library's own tests (offline)
```

## 8 · Milestones — each one shows something

| # | Milestone | Done when |
| --- | --- | --- |
| **M0** | Skeleton | `uv sync`, lint, pyright and an empty test suite run green in CI. |
| **M1** | The language | `Thing`, `expect` with 3 matchers, fake bus, MQTT adapter; tests offline. |
| **M2** | The demo plant | PackML line on MQTT (UNS topics, AsyncAPI file) + fault switch, `docker compose up`; an example suite catches a product fault a control suite misses. README shows it. **First public release.** |
| **M3** | Two systems | MES service over REST (OpenAPI); tests that span MES order → line → MQTT result. |
| **M4** | Knowledge | AsyncAPI/OpenAPI import → contract → test ideas checklist; templates; first knowledge pages. |
| **M5** | Agent layer | Three skills, two playbooks, tried against the demo plant; a recorded session in the docs. |
| **M6** | Evidence | JUnit + JSONL + an HTML report with *pass / fail / inconclusive / skipped-with-reason*. |
| **M7** | Catch power | A fault catalog for the demo plant and the fraction the shipped suite catches, stated honestly. |

M0–M2 are the minimum for the CV link to be worth clicking. After that, each milestone is a
release with a short changelog entry. Later candidates: OPC UA adapter, Sparkplug B payloads.

## 9 · Decisions

Made 2026-10-28:

1. **Domain: industrial (IIoT).** A PackML packaging line on a Unified Namespace — easy to
   simulate, and it speaks the standards IIoT teams use. Smart home is out of scope.
2. **Async only, no sync facade.** Buses in order: MQTT → REST (as an MES) → OPC UA.
3. **Demo via Docker Compose** with its own Mosquitto; Ubuntu is the supported platform.
4. **Docs in English, selected pages also in German**, kept in sync by a test.
5. **Contract** names the normalised internal model; files are called by their format.
6. **Work in the open.** The repository stays public; the history is part of what it shows.
   `main` only receives finished milestones, work happens on branches, and the README states
   the current milestone. The link goes into the CV from M2 on.
