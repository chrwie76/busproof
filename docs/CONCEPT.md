# Concept — what BusProof becomes, and in which order

> Draft v4, 2026-10-29. Written to be argued with. [IDEAS.md](IDEAS.md) holds the *why*; this
> document holds the *what* and the *order*. When a decision here is made, it moves out of §9.

## 1 · In one sentence

**BusProof is a Python test language for the behaviour over time of systems that talk through
messages. A person in a QA role writes tests that read like the requirement, runs them against a
system reached only over the network and described by a contract, and gets failures that say
what was seen.**

Today that means MQTT, described by AsyncAPI. REST comes next, to show that a second bus changes
nothing above the seam. It is a niche on purpose: one thing done well, not every kind of backend
test.

## 2 · Who it is for, and what surrounds it

**One user:** someone in a QA role who works in code — a test engineer, or a developer testing
their own service. Being able to program is assumed. In five minutes they need to see a test that
reads like the requirement, and a failure that explains itself.

What BusProof exchanges with its surroundings:

| Neighbour | What comes in | What goes out |
| --- | --- | --- |
| The test author | Tests written in the language; where the system is (`busproof.toml`, environment variables) | A verdict per test; a failure that says what was expected and what was seen |
| The system under test | Its messages, over the network | Commands, over the network — and nothing else |
| Whoever owns the contract (architect, requirement owner) | The contract: what the system offers and how it behaves | An error that lists the names the contract does have, when a test asks for one it lacks |

Four limits follow from this, and every later decision is held against them:

- **Only through the interface.** BusProof knows the system under test by its messages alone.
  It never imports, patches or reaches into its code. Whether a real machine or a simulated
  neighbour answers, BusProof cannot tell. The demo plant is reached the same way a customer's
  plant would be.
- **Secrets stay apart.** Where the system is and how to log in are separate things; BusProof
  reads secrets from the environment and never from a file (decision 25).
- **Everything works without an agent.** A person can write, read and repair a test with the
  README and the examples alone. An agent may draft; a person reads and owns what stays. If a
  test cannot be written without an agent, the language is too complicated — a defect here.
- **No dependency that restricts use.** Nothing with a condition such as "non-commercial"
  comes in, directly or through another package.

### 2.1 Technical context — what BusProof talks to at run time

| Neighbour | Channel | State |
| --- | --- | --- |
| An MQTT broker, with the system under test behind it | MQTT, with TLS and a login | built |
| pytest, the test runner | Fixtures through the entry point | built |
| Contract files (AsyncAPI, `line.yaml`) | Files on disk | built |
| The environment (where the system is, credentials) | Environment variables, `busproof.toml` | built |
| A REST service | HTTP | planned, not built |

In the domain, BusProof talks to the machines of a line. Technically, it talks to a broker.

### 2.2 Constraints

| Kind | Constraint | What follows |
| --- | --- | --- |
| Technical | Python 3.12 or later, asynchronous throughout (asyncio) | No synchronous facade. |
| Technical | pytest is the test runner | No abstraction for exchangeable test runners. The plugin stays a small adapter at the edge. |
| Technical | Protocol libraries are optional extras | The core runs without them. |
| Technical | Few run-time dependencies (today PyYAML, optionally aiomqtt) | Each new one needs a reason. |
| Organisational | One maintainer, who works with AI help and must be able to explain every change | Limits how many protocols and layers BusProof can carry. The hardest constraint. |
| Organisational | A public repository, in English, under Apache-2.0 | Nothing confidential in the repository. |
| Organisational | The library's tests run offline; the demo, in its own repository, needs Docker | `make check` needs no broker. |
| Regulatory | No dependency that restricts use | Licences have to be checked, also those of packages pulled in by others. No tool does it yet. |
| Regulatory | Agents do not read secrets | Enforced by a guard before every tool call (`.claude/hooks/guard.py`). |

No constraint comes from outside: no client, no target plant, no deadline.

### 2.3 Quality goals, in this order

1. **Reliability — the verdict is right.** First no false green, then no false red. A green test
   on a plant that is wrong is the worst thing this tool can produce.
2. **Understandability — a person understands what is there.** Someone who can program writes a
   test quickly and reads someone else's, without an agent. This goal is about the tests of
   BusProof's users.
3. **Maintainability — BusProof itself stays small and changeable**, so that one maintainer can
   carry it. This goal is about BusProof's own code.

When two goals pull apart, the higher one wins: `remains` fails on a signal that never reports,
although letting it pass would be more convenient.

Each goal has scenarios it can be checked by:

| | Trigger | Expected | Measure | State |
| --- | --- | --- | --- | --- |
| R1 | A test uses `remains` on a signal that never reports, for example a misspelt name. | The test fails and says that nothing was seen. | No green without at least one message seen. | built |
| R2 | The line tests run several times in a row against the healthy demo plant. | Every run is green. | 10 runs, 0 failures. | 2 runs checked so far |
| U1 | Someone who can program and does not know BusProof writes a test for one machine of the demo. | They manage with the README and the examples, without an agent. | At most 30 minutes to their first own green test. | open — not shown yet |
| U2 | A test fails. | The message alone says what was expected, where, and what was seen. | No look into a log needed. | built |
| M1 | A second bus is added (REST). | One new module for the bus, and one place that chooses the bus. | No change to `signals`, `machines` and `expect`. | open — the plugin knows only MQTT today |
| M2 | Someone changes the core. | The rules for size and dependencies hold. | Every module under 200 lines; the core loads no protocol library. | the second is checked by a test, the first is not |

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
| 1 Agree the contract — or discover it from a recording, if none is written | | `draft-contract` |
| 2 Understand the system: read the contract, derive test ideas | | `plan-tests` |
| 3 Plan: state transitions, boundary values, equivalence classes | **G1** | `plan-tests` |
| 4 Write the test | | `write-test` |
| 5 Prove it catches: inject a fault, the test must turn red | | `write-test` |
| 6 Review and accept | **G2** | `review-test` (assists, does not decide) |
| 7 Run, produce evidence | | — |
| 8 Judge a red run | **G3** | `triage-run` |
| 9 Explore under a charter | | `explore-system` |
| 10 Release | **G4** | — |

The playbook itself is `docs/PLAYBOOK.md` in the test project's repository, a living draft: a step is written down
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

What BusProof is not:

- **A tool for people who do not program.** It is a library; its tests are code.
- **A replacement for the architect or the requirement owner.** What has to be proven comes from
  them. BusProof is the harness that proves it.
- **An assistant.** The product is the language and the tests a person owns, not an agent that
  is told "test this device".
- **A load or performance test tool.** Others do that well.

What is left out for now:

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

## 7 · Repository layout

Two repositories (decision 30). This one is the library:

```
busproof/
├─ src/busproof/     core (layer 1) and knowledge (layer 2)
├─ tests/            one file per module, and the checks on the guard and the package
├─ docs/             IDEAS, CONCEPT
└─ README.md  Makefile  AGENTS.md  pyproject.toml
```

The second is a test project with a plant to try it on — the user's side, laid out the way a
test project of their own would be:

```
busproof-test-project/
├─ tests/  machines/  conftest.py  busproof.toml    the test project, at the root
├─ AGENTS.md  .claude/                               its own rules for AI assistants, and the guard
├─ contracts/                                        the agreement: AsyncAPI per unit, packml.yaml, line.yaml
├─ docs/                                             its decisions, and the playbook
├─ plant/                                            the system under test; knows nothing of BusProof
└─ selftest/                                         checks on that repository itself
```

Who clones the test project installs it, starts the plant and runs the tests, all from its root.
Who wants to change the language works here. Three kinds of tests, three questions: `tests/`
here — does the tool work? `plant/tests/` there — does the simulation compute right? The test
project's `tests/` — does the *plant* work, and does the suite catch its faults? Only the last is
what the tool is for.

## 8 · Milestones — each one shows something

| # | Milestone | Done when |
| --- | --- | --- |
| **M0** | Skeleton | `uv sync`, lint, pyright and an empty test suite run green in CI. |
| **M1** | The language | A `line` fixture with hand-written, typed entity classes (autocompletion in VS Code, like page objects); `expect` with 3 matchers; a recorder that buffers every message of a test; fake bus and MQTT adapter; tests offline. |
| **M2** | The demo plant | Own small PackML simulation on MQTT: three machines and an SCU as services (UNS topics, mounted contracts) + fault switch + HTML page, `make demo` with secrets generated on first start and the security profiles `open` and `password` (default); an example suite catches a product fault a control suite misses. README shows it. |
| **M2-rest** | What M2 left open | **First public release, also on PyPI** (Trusted Publishing, TestPyPI first; the workflow is ready); what the SCU does when it restarts while the machines run; a test for a service that really dies, not only one that goes silent; processing times at the stations, so a line can jam. |
| **M3** | Two systems | MES service over REST (OpenAPI); tests that span MES order → line → MQTT result; security profile `mtls`. |
| **M4** | Knowledge | AsyncAPI/OpenAPI import → contract → test ideas checklist; **a contract discovered from a recording of the demo plant**, with its origin, and the loop that sharpens it (decision 24); templates; first knowledge pages. |
| **M5** | Evidence | The five parts of §4.5: JUnit + JSONL + a report for people with *pass / fail / inconclusive / skipped-with-reason*, mapped to the ISO/IEC/IEEE 29119-3 test documents. |
| **M6** | Agent layer | The playbook and its skills, tried against the demo plant; a recorded session in the docs. |
| **M7** | Catch power | A fault catalog for the demo plant and the fraction the shipped suite catches, stated honestly. |

M0–M2 are the minimum for the CV link to be worth clicking. After that, each milestone is a
release with a short changelog entry. Later candidates: an OPC UA adapter, shown by the same tests passing over another bus (decision 26); Sparkplug B payloads.

## 9 · Decisions

Made 2026-10-28 (1–12) and 2026-10-29 (13–24), 2026-10-30 (25–28), 2026-11-17 (29–30):

Decisions about the demo plant and the test project moved to that repository on 2026-11-17 and
keep their numbers there, so a reference such as "decision 26" still finds its text.

1. **Domain: industrial (IIoT).** A PackML packaging line on a Unified Namespace — easy to
   simulate, and it speaks the standards IIoT teams use. Smart home is out of scope.
2. **Async only, no sync facade.** Buses in order: MQTT → REST (as an MES) → OPC UA.
3. *Moved to the test project's decisions, with its number: Demo via Docker Compose.*
4. **Docs in English, selected pages also in German**, kept in sync by a test.
5. **Contract** names the normalised internal model; files are called by their format.
6. **Work in the open.** The repository stays public; the history is part of what it shows.
   `main` only receives finished milestones, work happens on branches, and the README states
   the current milestone. The link goes into the CV from M2 on.
7. **Evidence is the product** — five parts, four gates, the same with or without an agent (§4.5).
8. *Moved to the test project's decisions, with its number: One playbook for the whole process; skills are its agent form.*
9. **Plain pytest, no pytest-bdd** (§6).
10. **A vision beyond the milestones** is kept in §10, so M1–M2 can stay small.
11. *Moved to the test project's decisions, with its number: An own small simulation.*
12. *Moved to the test project's decisions, with its number: The web page is plain HTML.*
13. **Contracts: the wire and the behaviour are two files.** For MQTT, `asyncapi.yaml` says how
    the system speaks (topics, payloads, types, ranges); `line.yaml` says how it behaves and
    refers to the AsyncAPI channels. Other protocols bring their own wire format later —
    NodeSet2 XML for OPC UA, `.proto` for gRPC, OpenAPI for REST — and all are read into the
    same internal contract.
14. *Moved to the test project's decisions, with its number: Four files, four questions.*
15. **Secrets are off limits for every agent**, enforced where it can be and written down where
    it cannot: permission rules and a guard before every tool call refuse `.env` files, a
    `secrets/` folder and key files; a secret scan runs before each commit; and an agent that
    sees such a file open in the editor stops and asks for it to be closed. The rules live in
    `AGENTS.md`, which every assistant reads.
16. *Moved to the test project's decisions, with its number: The demo creates its own secrets on first start.*
17. *Moved to the test project's decisions, with its number: Security is a switch with three profiles — the same options the library offers a real system.* What stays
    here: the library connects without a login, with a password over TLS, and later with
    client certificates.
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
    *Amended by decision 29: the folders are now siblings, and the root is no longer the tool.*
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
    line file, default waiting time — is in **`busproof.toml`** of the test project.
    Topics follow ISA-95 as a Unified Namespace does: `{enterprise}/{site}/{area}/{line}/
    {machine}`, in the demo `acme/plant1/packaging/line1/capper` — `acme` being the classic
    made-up company of software examples, so no reader mistakes it for a real one. **One message
    per machine** carries its whole state, `{"state": 6, "good_count": 123, …}`, sent
    again on every change and at a steady pace: each machine is a unit of its own (PackML), the
    line's state stays what BusProof derives, and a repeated value is fresh evidence for
    `remains`. A signal is a topic plus a path into the payload, so a plant that sends one
    message per line works too. The part of a topic that differs per site is an AsyncAPI
    channel parameter, filled from **`line.yaml`** — not from `busproof.toml`, as first written
    here: the plant must know where it stands too, and it reads no BusProof file. Mounted into
    each machine's service, the same `line.yaml` is what the plant publishes under and what the
    tests read, so there is one source. On a real line this is the prefix an integrator sets
    at commissioning; `line.yaml` is its written-down form. Topics never go into `.env`: an
    agent writing a test must be able to read them. A machine gets its topics from a function,
    `topics("capper", "good_count")`; `read_line("…/line.yaml").topics` builds it from the
    contracts — what a machine *sends* are its signals, what it *receives* its commands — and a
    name the contract lacks fails at once, listing the names it has.
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
    *Added 2026-11-17:* the core needs one thing from a contract — a function from machine and
    name to an address (`Topics`). `read_line` is the one reader there is, for AsyncAPI files
    and a `line.yaml`. A test project with another format writes that function itself; a
    reader for a second format joins the library, as an optional part, when a user needs it.
24. **Contracts are central, but not an entry ticket.** Many plants run large machines with no
    written contract: it lives in the PLC program, the HMI tag list, a few heads — and in what
    the bus carries every day. BusProof meets them there instead of shutting them out. Step 1
    of the playbook has two ways in: **agree** a contract that exists, or **discover** one —
    listen in the `observe` stance, draft a contract from what was seen (topics, fields,
    types, observed ranges, states and the changes between them), and a person who knows the
    plant agrees it line by line. *Observed is not right*: a draft pins what the plant does,
    which may be a fault of many years. So every contract carries its **origin** — delivered
    by its maker, observed, agreed by whom and when — provenance for the test basis as for the
    tests. Then the **loop**: tests from the contract run against the plant, and each
    deviation asks *the plant or the contract?* — so the contract is sharpened by use and
    shows how far it carries. Agents help most here, in legacy plants: drafting from
    recordings, listing open questions, proposing what a deviation means; a person decides
    each time. This is what sets BusProof apart, and once it works it is shown as such (M4).
25. **The same tests anywhere: `BUSPROOF_ENV` picks, the environment supplies.** BusProof reads
    environment variables, never the `.env` file itself; `.env` is a local convenience, and CI
    sets the same names as its variables (GitLab: CI/CD variables, the password masked and
    protected). `BUSPROOF_ENV` picks a section of `busproof.toml`, which says which `line.yaml`
    counts; so a second plant is a section, not a change to a test. The fixtures every project
    needs — `settings`, `contract`, `bus` — come with BusProof as a pytest plugin, as `page`
    comes with pytest-playwright; what belongs to one plant — `line`, `running_line` — is in the
    project's `conftest.py`. A stand-in plant over the fake bus carried the tests through M1 and
    went once the plant ran in Docker: playing an SCU too, it would have become a second plant.
    So `make check` stays offline, and `make line-tests` needs Docker, also in CI.
26. *Moved to the test project's decisions, with its number: An SCU coordinates the line, and all of it speaks MQTT for now.*
27. *Moved to the test project's decisions, with its number: Bottles take time, and supplies run out.*
28. *Moved to the test project's decisions, with its number: Two handles for a test: faults while it runs, scenarios for how it starts.*
29. **Four folders side by side; the root is only the table of contents.** `library/`, `plant/`,
    `contracts/` and `test-project/` mirror the parties in §2: the tool, the system under test,
    the agreement, the test author. Amends decision 19, where the root was the tool and the
    other three sat inside `demo/`. *Why:* someone who wants to write a test had to find their
    way through the maker's repository, with a plant in it that is larger than the library.
    Now they open one folder (understandability, scenario U1). *Not separate repositories:* one
    maintainer; several repositories would mean the agent rules twice, several CI runs, and two
    steps for every change that touches language and tests together. A folder can later leave
    with its history; the way back is dearer. *Split when* someone else maintains a part, a part
    is released at its own pace, a part uses another technology, or a part needs other access
    rights. *What it costs:* `pyproject.toml` is divided — the package's description moves to
    `library/`, the workspace and shared settings stay at the root; the test project has an
    environment of its own but still takes the library from the folder next to it, so that the published package alone is enough has to be
    shown by a CI step of its own; and the separation stays an agreement, kept by the tests in
    `tests/repo/`. `make demo` stays the command that starts the plant. Earlier decisions name
    paths as they were on their day (`demo/…`, `src/…`).
    *Amended by decision 30 on the same day: the test project, the plant and the contracts left
    for a repository of their own.*
30. **Two repositories: the library here, the test project with its plant in its own.** Amends
    decision 29. *Why:* whoever clones a repository starts from its root. A test project inside
    the maker's repository had to be opened as a folder on its own to get its environment, its
    editor settings and its rules for AI assistants — a step nobody guesses, and the first try
    failed on it. With the test project at the root of its own repository, cloning, installing
    and running a test work the way they do in any project. *What it costs:* a change that
    touches language and tests together is two commits in two repositories; the test project
    needs BusProof from somewhere — from this repository cloned next to it until the first
    release, from PyPI after; the plant's tests against a real broker no longer run in this
    repository's CI; and the guard for AI assistants exists in both repositories.

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
