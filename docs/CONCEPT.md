# Concept — what BusProof becomes, and in which order

> Draft v4, 2026-10-29. Written to be argued with. [IDEAS.md](IDEAS.md) holds the *why*; this
> document holds the *what* and the *order*. When a decision here is made, it moves out of §9.

## 1 · In one sentence

**BusProof is a Python test language for asynchronous industrial interfaces (IIoT) — with the
knowledge, demos and agent skills to use it — so a team can point it at an MQTT-, REST- or
OPC UA-connected system described by AsyncAPI or OpenAPI and end up with a pytest suite that
catches real faults — and evidence an auditor can follow.**

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
│ 4  Agent layer   playbook + skills (Markdown), later MCP     │  optional
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

- A **demo plant**: a small simulation of its own (a few hundred lines, written for this repo),
  a simulated **packaging line** (filler → capper → inspector). It is given its contract files
  as a mounted volume, so plant, tests and panel read the same description (details: §9,
  contracts round).
  - Each machine follows the **PackML** state model (ISA-TR88: `Idle`, `Starting`, `Execute`,
    `Held`, `Aborted`, …) — an industry standard that also exercises acting states.
  - It publishes over **MQTT** in a **Unified Namespace** (ISA-95 hierarchy, e.g.
    `acme/plant1/packaging/line1/capper/state`), described by an **AsyncAPI 3.0** file.
  - A small **MES** service takes production orders over **REST** (OpenAPI) and reads the line
    over MQTT — so the demo has two systems, and the interplay is what is tested.
  - Later: **Sparkplug B** payloads and an **OPC UA** server for the same line.
- A **web page** to watch and click: a single HTML file that connects to Mosquitto over MQTT
  WebSockets, shows states and counters live, and has buttons for the fault switches. No
  backend of its own.
- A **fault switch** in the plant (`stuck sensor`, `slow capper`, `silent rejects`) so a demo
  can show a suite catching a fault — and a control-only suite missing one.
- One command starts it: **`docker compose up`** (Mosquitto + plant + MES + panel). The project
  needs no external broker; an own broker is used by setting its address in the environment.
- Supported platform: **Ubuntu** (also GitHub Actions). Docker Desktop on Windows/macOS should
  work but is not tested.

### 4.4 Agent layer — the playbook and its skills

What a good harness for agents needs, from looking at others:

- **A narrow action space.** A few well-named commands (`busproof ideas`, `busproof run`,
  `busproof probe`) the agent calls — no free-form scripting against the bus.
- **Good observations.** Failures that explain themselves are what lets an agent diagnose; this
  is the core's job, not the agent's.
- **Recovery and limits.** A stance (`observe` / `drive` / `inject`) the environment enforces,
  and a hard step budget.
- **A human gate.** An agent proposes a test; a person accepts it (a pull request is enough).

So the agent layer ships as:

- **One playbook** describing the whole process for a person — each step says what to do by
  hand and which command helps. BusProof is fully usable from the playbook alone, with no agent.
- **Skills** (`SKILL.md`, the open format several assistants read) as the agent form of a
  playbook step. A skill *points to* its step instead of repeating it, so there is one
  description that cannot drift. Each skill stays under ~1 000 words.
- **Later, if it earns its upkeep:** an MCP server exposing the same commands.

| Playbook step | Gate | Skill (optional) |
| --- | --- | --- |
| 1 Agree the contract: one per machine, the state machine, the line | | `draft-contract` |
| 2 Understand the system: read the contract, derive test ideas | | `plan-tests` |
| 3 Plan: state transitions, boundary values, equivalence classes | **G1** | `plan-tests` |
| 4 Write the test | | `write-test` |
| 5 Prove it catches: inject a fault, the test must turn red | | `write-test` |
| 6 Review and accept | **G2** | `review-test` (assists, does not decide) |
| 7 Run, produce evidence | | — |
| 8 Judge a red run | **G3** | `triage-run` |
| 9 Explore under a charter | | `explore-system` |
| 10 Release | **G4** | — |

The playbook itself is [docs/PLAYBOOK.md](PLAYBOOK.md), a living draft: a step is written down
once it has been gone through for real on the demo line.

### 4.5 Evidence and where the person sits

The product of BusProof is **evidence**, not tests. Tests are how evidence is produced; in a
world where agents write test code cheaply, what stays scarce is a result someone can trust and
an auditor can follow. Hence the split: **agents write, the deterministic core proves, people
sign.**

**The evidence of a run has five parts**, each answering an auditor's question:

| Part | Question | Content |
| --- | --- | --- |
| **Run** | What ran, when, where, against what? | time, environment, stance, Git commit of the tests, hash of the AsyncAPI file, BusProof version |
| **Verdict** | What came out, and why? | per test: requirement ids, verdict (pass / fail / inconclusive / skipped with reason), what each expectation saw |
| **Observation** | What is the verdict based on? | the raw bus messages, with time and source |
| **Provenance** | Who wrote the test, who accepted it? | person or agent (model, version, playbook step), accepted by whom and when (pull request review) |
| **Catch power** | Does the test check anything? | fault X injected, test turned red, with a date |

A manifest with checksums covers all five. Output: JSONL for machines, JUnit for CI, a report
for people that shows each test as readable Given/When/Then steps.

**The person sits at four gates — the same with or without an agent.** An agent only replaces
the work *between* the gates, never a gate.

| Gate | Decision | Without an agent | With an agent |
| --- | --- | --- | --- |
| **G1 Plan** | What is tested? | the person plans | the agent proposes, the person approves |
| **G2 Acceptance** | Does the test join the regression suite? | pull request review | an agent's test stays *proposed* until the pull request is approved |
| **G3 Red run** | Bug, changed specification, or flaky? | the person decides | the agent proposes a diagnosis; it **never changes an expectation** |
| **G4 Release** | Ship or not? | the person signs | the agent summarises, the person signs |

There is deliberately no "healer" that repairs a red test to green: a test repaired by the
party that wanted it green is not evidence.

## 5 · What is deliberately *not* in it (overkill for now)

- A multi-agent framework, LangGraph, or a role-play of "tester agent" and "reviewer agent".
  A plain loop with a gate is enough until it provably is not.
- A vector database or RAG. The contract and a few Markdown pages fit in context.
- A test *generator* that writes files nobody may edit (the lesson in [IDEAS §1](IDEAS.md#1--a-test-language-not-a-test-factory)).
- Its own UI beyond the demo panel and an HTML report.
- Kafka, AMQP, gRPC — until someone needs them. The `Bus` interface keeps the door open.
- A plugin system. Adapters are plain modules.

## 6 · How the code is written — so it stays readable

- **Plain Python** — at least 3.12 (Ubuntu 24.04 LTS), developed on 3.13 — `async`/`await`,
  dataclasses, type hints. No metaclasses, no decorators that hide control flow, no dependency
  injection framework.
- **Plain pytest, no pytest-bdd.** BDD adds a second layer (feature files *and* step
  definitions) to write, review and maintain, and pytest-bdd has no async steps (open issues
  #223, #609, #629, #783 as of 2026-10). What BDD gives is kept another way: the requirement is
  a marker on the test (`@pytest.mark.requirement("REQ-012")`), the test reads as
  Given/When/Then, and the report renders it as steps. Acceptance criteria may be written in
  Gherkin as *input* to planning; they are not executed.
- **Small files** (aim < 200 lines), one idea per module, a docstring that says *why* it exists.
- **Few dependencies**: `pytest`, `httpx`, `jsonschema`, `pyyaml`; `paho-mqtt` / `aiomqtt` as an
  optional extra. Each new one needs a sentence in this document.
- **Every module has a test**, and the library's tests run offline with a fake bus.
- **Tooling**: `uv` for environments, `ruff` for lint and format, `pyright` for types, GitHub
  Actions for CI. Version from Git tags.
- **Root files a newcomer recognises** — `pyproject.toml`, `uv.lock`, `Makefile`,
  `.pre-commit-config.yaml`, CI workflow; mapped to their Node/Playwright counterparts in
  [CONTRIBUTING.md](../CONTRIBUTING.md).
- **Settings of a test project** live in `busproof.toml`, the counterpart of
  `playwright.config.ts`: environments (`local`, `ci`) with their broker and API addresses,
  default timeouts, the stance per environment, reporters. Secrets never go there — they come
  from the environment, documented in `.env.example`. Found by walking up from the current
  directory, as pytest finds its config. Arrives with M1.

## 7 · Repository layout (target)

```
busproof/                    the tool — the repository root is the library
├─ src/busproof/             core (layer 1) and knowledge (layer 2)
├─ tests/                    the tool's own tests: unit/ (one file per module), repo/, later integration/
├─ skills/  playbook/        layer 4
├─ docs/                     IDEAS, CONCEPT, knowledge pages
│
└─ demo/                     a customer's world, built to show the tool (layer 3)
   ├─ compose.yaml           broker + plant + web page
   ├─ contracts/             machines/*.asyncapi.yaml, packml.yaml, line.yaml — the agreement
   ├─ plant/                 the system under test; knows nothing of BusProof
   └─ line-tests/            the test project, written as a customer would
      ├─ busproof.toml  conftest.py
      ├─ machines/           machine objects (the page objects)
      └─ tests/              control/  product/  timing/
```

Three kinds of tests, three questions: `tests/` — does the tool work? `demo/plant/tests/` — does
the simulation compute right? `demo/line-tests/` — does the *plant* work, and does the suite
catch its faults? Only the last is what the tool is for.

## 8 · Milestones — each one shows something

| # | Milestone | Done when |
| --- | --- | --- |
| **M0** | Skeleton | `uv sync`, lint, pyright and an empty test suite run green in CI. |
| **M1** | The language | A `line` fixture with hand-written, typed entity classes (autocompletion in VS Code, like page objects); `expect` with 3 matchers; a recorder that buffers every message of a test; fake bus and MQTT adapter; tests offline. |
| **M2** | The demo plant | Own small PackML simulation on MQTT (UNS topics, mounted AsyncAPI file) + fault switch + HTML page, `make demo` with secrets generated on first start and the security profiles `open` and `password` (default); an example suite catches a product fault a control suite misses. README shows it. **First public release, also on PyPI** (Trusted Publishing, TestPyPI first). |
| **M3** | Two systems | MES service over REST (OpenAPI); tests that span MES order → line → MQTT result; security profile `mtls`. |
| **M4** | Knowledge | AsyncAPI/OpenAPI import → contract → test ideas checklist; templates; first knowledge pages. |
| **M5** | Evidence | The five parts of §4.5: JUnit + JSONL + a report for people with *pass / fail / inconclusive / skipped-with-reason*, mapped to the ISO/IEC/IEEE 29119-3 test documents. |
| **M6** | Agent layer | The playbook and its skills, tried against the demo plant; a recorded session in the docs. |
| **M7** | Catch power | A fault catalog for the demo plant and the fraction the shipped suite catches, stated honestly. |

M0–M2 are the minimum for the CV link to be worth clicking. After that, each milestone is a
release with a short changelog entry. Later candidates: OPC UA adapter, Sparkplug B payloads.

## 9 · Decisions

Made 2026-10-28 (1–12) and 2026-10-29 (13–23):

1. **Domain: industrial (IIoT).** A PackML packaging line on a Unified Namespace — easy to
   simulate, and it speaks the standards IIoT teams use. Smart home is out of scope.
2. **Async only, no sync facade.** Buses in order: MQTT → REST (as an MES) → OPC UA.
3. **Demo via Docker Compose** with its own Mosquitto; Ubuntu is the supported platform.
4. **Docs in English, selected pages also in German**, kept in sync by a test.
5. **Contract** names the normalised internal model; files are called by their format.
6. **Work in the open.** The repository stays public; the history is part of what it shows.
   `main` only receives finished milestones, work happens on branches, and the README states
   the current milestone. The link goes into the CV from M2 on.
7. **Evidence is the product** — five parts, four gates, the same with or without an agent (§4.5).
8. **One playbook for the whole process; skills are its agent form** and point to its steps (§4.4).
9. **Plain pytest, no pytest-bdd** (§6).
10. **A vision beyond the milestones** is kept in §10, so M1–M2 can stay small.
11. **An own small simulation** in `demo/plant/`, not an existing twin; contract files are mounted
    into it.
12. **The web page is plain HTML** on MQTT WebSockets, no Streamlit, no backend.
13. **Contracts: the wire and the behaviour are two files.** For MQTT, `asyncapi.yaml` says how
    the system speaks (topics, payloads, types, ranges); `line.yaml` says how it behaves and
    refers to the AsyncAPI channels. Other protocols bring their own wire format later —
    NodeSet2 XML for OPC UA, `.proto` for gRPC, OpenAPI for REST — and all are read into the
    same internal contract.
14. **Four files, four questions** — kept apart so none of them leaks into another:

    | File | Answers | Read by | In Git | Secrets |
    | --- | --- | --- | --- | --- |
    | `demo/contracts/` (AsyncAPI per machine, `packml.yaml`, `line.yaml`; decision 23) | What *should* the system do? | plant, tests, web page | yes | never |
    | `demo/plant/config.json` | In which state does this plant *start*? (levels, counters, speed, active faults, random seed, physics) | plant; tests as a precondition | yes, one file per scenario | never |
    | `.env` | *Where* does it run, and *who* may connect? | tests, Docker Compose | no — `.env.example` is | here, or generated into `demo/secrets/` (decision 16) |
    | `busproof.toml` | *How* do the tests run? (environments, timeouts, stance, reporters) | tests | yes | never — only variable *names* |

    The behaviour file holds what a test can check: topology and the flow of units (stations,
    transit times), variables with type, unit, range, normal range, warning and alarm limits and
    a *safety-critical* flag, setpoints, commands with their allowed states, alarms with their
    trigger, and the shape of a message (a whole state, or one value per topic). It does not
    hold how the web page draws a machine, nor the physics of the simulation — those belong to
    the page and to `config.json`. A test may read its *precondition* from `config.json`; what
    is *correct* always comes from the contract, or the tests would only mirror the plant.
15. **Secrets are off limits for every agent**, enforced where it can be and written down where
    it cannot: permission rules and a guard before every tool call refuse `.env` files, a
    `secrets/` folder and key files; a secret scan runs before each commit; and an agent that
    sees such a file open in the editor stops and asks for it to be closed. The rules live in
    `AGENTS.md`, which every assistant reads.
16. **The demo creates its own secrets on first start.** `make demo` finds no credentials and
    has a one-off container generate them: a random password, a small certificate authority,
    and certificates for the broker and its clients. They land in `demo/secrets/`, which Git
    ignores and the guard closes to agents. Nothing secret is ever in the repository, nobody
    has to create a file by hand, and every installation has keys of its own.
17. **Security is a switch with three profiles — the same options the library offers a real
    system:**

    | Profile | Meaning | For |
    | --- | --- | --- |
    | `open` | no login, no encryption (port 1883) | a quick try only; console and web page say *insecure* plainly |
    | `password` | user and password, always over TLS (port 8883) | the usual case — a password without encryption protects nothing |
    | `mtls` | client certificates (X.509) on both sides | what industrial customers expect, in the spirit of IEC 62443 |

    Chosen with `make demo SECURITY=…`. Order: `open` first with the switch built in, `password`
    as the default in M2, `mtls` after it. Under `mtls` the web page still connects with a
    password, because browsers handle client certificates poorly. The `.env.example` names file
    *paths* for CA, certificate and key — never their contents.
18. **Entities and fixtures follow the page-object pattern** — the same shape as a Playwright
    project, translated:

    | Playwright | BusProof | What it is |
    | --- | --- | --- |
    | `page` | `bus` | the connection |
    | `Locator` | `Signal` | a *handle* on a value, not the value; `expect` reads it, and waits |
    | page object | machine object (`Capper`) | a machine's signals and commands — no `expect` inside |
    | collector of page objects | `Line` | the machines of a line; the line's state is their consensus |

    A machine class is written **in its constructor**, plain Python with no hidden mechanism,
    and names signals by their name in `line.yaml`, never by topic:

    ```python
    class Capper(Machine):
        """The capping station: closes bottles, counts good and rejected ones."""

        def __init__(self, bus: Bus, topics: Topics):
            super().__init__(bus, topics, name="capper")  # gives it `state`, as PackML does
            self.good_count = self.signal("good_count")
            self.reject_count = self.signal("reject_count")

        async def start(self) -> None:
            await self.send("start")
    ```

    The library provides the building blocks (`Machine`, `Line`, `Signal`, `expect`); the
    machine classes belong to the test project, like page objects. Fixtures come in layers:
    `bus` (the connection from `busproof.toml` and the environment, plus the recorder that keeps
    every message as evidence) → `line` (the machine objects) → `running_line` (precondition:
    the line in `Execute`, counter baselines taken). Generating the machine classes from the
    contract stays in the vision (§10).
19. **Three worlds, one repository, clean seams.** The tool is the repository root; `demo/`
    holds a customer's world — `contracts/`, `plant/` (the system under test) and `line-tests/`
    (the test project) — as one uv workspace (§7). Three rules keep them apart, each to be
    checked by a test: the tool names no plant; the plant knows nothing of BusProof; the test
    project uses only `from busproof import …` and has its own `pyproject.toml` and
    `busproof.toml`. So each part can later leave for a repository of its own unchanged — the
    plant as an image with its contracts, the test project as a template — by deleting the one
    line that takes `busproof` from the workspace instead of from PyPI.
20. **Matcher names tell the kind of check.** `to_be…` asks where a signal ends up
    (`to_be("Execute")`, `to_be_in({...})`); a verb asks what it does over time (`rises_by(5)`,
    `remains(...)`, `remains_between(lo, hi, ...)`, `passes_through(state)`,
    `happens_before(other)`). `within=` for what must happen at some point, `during=` for what
    must hold all along, both in seconds as everywhere in Python. *Not* `holds`: in PackML,
    `Hold` is a command and `Held` a state, and an industrial reader would read
    `line.state.holds(...)` as "the line goes to Held".
21. **Each setting lives where it changes.** *What the plant offers* — topics, signal names,
    types, states — is in the **contract**, read by the plant and the tests alike, so the two
    cannot drift apart. *Where it runs* — broker address, user, password — is in **`.env`**,
    which changes with the environment and stays closed to agents. *How we test* — which
    contract, which line, default waiting time — is in **`busproof.toml`** of the test project.
    Topics follow ISA-95 as a Unified Namespace does: `{enterprise}/{site}/{area}/{line}/
    {machine}`, in the demo `acme/plant1/packaging/line1/capper` — `acme` being the classic
    made-up company of software examples, so no reader mistakes it for a real one. **One message
    per machine** carries its whole state, `{"state": "Execute", "good_count": 123, …}`, sent
    again on every change and at a steady pace: each machine is a unit of its own (PackML), the
    line's state stays what BusProof derives, and a repeated value is fresh evidence for
    `remains`. A signal is a topic plus a path into the payload, so a plant that sends one
    message per line works too. The part of a topic that differs per site is an AsyncAPI
    channel parameter, filled from `busproof.toml`. Topics never go into `.env`: an agent writing a
    test must be able to read them. Until the contract is read (M1 step 5), a machine gets its
    topics from a function the test writes by hand: `topics("capper", "good_count")`.
22. **States are numbers on the wire and names in a test.** The demo plant sends PackTags
    numbers (`"state": 6`), as real controllers do and as OPC UA and gRPC do anyway. A test
    reads them through an `IntEnum` the test project writes (`State.EXECUTE`, with
    autocompletion); the recorder keeps the raw number as evidence, a failure shows both
    (`EXECUTE (6)`), and a number the enum does not know stays a number — itself a finding.
    The **state machine** — states, the commands that leave each, the acting states a machine
    leaves on its own — is in `packml.yaml` (decision 23); the library knows no state name, so a
    plant on Weihenstephan Standards or its maker's own states brings its own file. The demo uses
    the PackML core of 12 states (Stopped, Resetting, Idle, Starting, Execute, Holding, Held,
    Unholding, Stopping, Aborting, Aborted, Clearing); Suspend and Complete can follow without
    rebuilding. Commands go to one topic per machine, `…/capper/cmd`, as
    `{"command": "Start"}`.
23. **One contract per machine, a line made of them.** Each machine has its own AsyncAPI file
    in `demo/contracts/machines/`, as each machine builder delivers its own interface — and as
    AsyncAPI means it: one document per application. Its topics start with
    `{enterprise}/{site}/{area}/{line}/` and it names no server, so it does not know where it
    stands: one contract serves a test at the maker's (FAT) and in the plant (SAT). The state
    machine all three follow is `packml.yaml`, once. `line.yaml` only composes: which machines,
    in which order, and the values of the address parameters. This refines decisions 13 and
    14, which spoke of one `asyncapi.yaml`.

To settle later:

- **Requirements** — in `line.yaml`, or in a file of their own with a link to where they are
  managed. Needed by M5 (evidence).

## 10 · Vision — horizon 2

Where BusProof goes after the milestones above. Kept here so no idea is lost and none of them
widens M1–M2.

- **Tests from contracts, by an agent.** Test ideas (§4.2) become drafted tests; G1 and G2 stay.
- **Exploratory learning.** Observe the bus, its addresses and events; from a recorded session
  an agent proposes a test. Such a test pins *what happened* — which may be a bug — so a person
  judges correctness at G2.
- **Test basis.** Whatever the requirements come from — specifications, interface control
  documents (ICDs), prose, tickets — is turned into structured requirements by a skill.
- **Mocks** of neighbouring services, generated from AsyncAPI first; Protobuf (with Sparkplug B)
  and ICDs later.
- **Entity classes generated** from the AsyncAPI file instead of written by hand, so a contract
  change shows up as type errors in the editor.
- **Standardised evidence.** The evidence maps onto ISO/IEC/IEEE 29119-3 documents; the audit
  trail (who changed and approved what, when) comes from Git and reviews, in the sense of
  21 CFR Part 11.
- **Beyond functional tests**, structured by ISO/IEC 25010: performance, security, reliability,
  scalability — proposed as test ideas like the functional ones.
- **Gaps and maintenance.** Find what is not covered, propose tests for it, keep the regression
  suite current when the contract changes (IDEAS §8).
- **Honest numbers instead of one score**: contract coverage, requirement coverage and catch
  power side by side. A single trust score invites optimising the number.
- **Branch-aware runs**: smoke and affected tests on a feature branch, full regression on
  `main`, non-functional tests at a release — pytest markers and CI rules.
- **A skill bench** (idea from JavaBench): fixed tasks against the demo plant ("write a test for
  REQ-7"); a skill's test counts only if it is green on the healthy plant *and* red with the
  fault injected; compared across context variants. Measures skills instead of claiming them.
- **A larger twin** (OPC UA, several lines) as an external system under test.
- **gRPC**, with `.proto` files as its contract.
- **Later, if needed:** an MCP server, other brokers (Kafka, AMQP), a UI beyond the demo page.
