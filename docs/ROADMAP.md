# Roadmap — where BusProof may go

Nothing in this document is built. These are ideas, each with the reason behind it, kept so that
none is lost and none slips into the library unnoticed. What BusProof is today is in
[CONCEPT.md](CONCEPT.md) §1 and §2, and what it is built on in [IDEAS.md](IDEAS.md). The focus
there decides what comes next: a small library that one maintainer can carry, and tests a person
can write and read without an agent.

The sections keep the numbers they had in IDEAS.md.

## Described in IDEAS, and not built either

Some sections of IDEAS mix what exists with what does not. Not built yet:

- **Matchers** beyond `to_be`, `rises_by` and `remains` (IDEAS §1).
- **Types generated from the contract** (IDEAS §1).
- **Buses other than MQTT**, and what an adapter declares about itself (IDEAS §2).
- **Uses of the contract** beyond addresses: test ideas, structural drift, the destination gap
  (IDEAS §3). A reader for a contract format other than AsyncAPI belongs here too.
- **The verdict *inconclusive*, and skips that are visible and justified** (IDEAS §6).
- **A neutrality test** that keeps domain words of one plant out of the library (IDEAS §11).

## 5 · Observing and exploring

### An observation is a session

A recording is a folder, not a file: a **header** (who started it, why, under which stance, which
sources, each source's clock offset ± uncertainty), an **inventory** (what each source declared),
and the **stream** (events, each with its source and address). Every later question — timeline,
drift, product check — reads a session.

- **Interruption writes, it does not discard.** Ctrl-C or a size limit leaves a valid, partial
  session that says *why* it is partial: operator abort, budget reached, or a source failed.
  The buffers belong to the caller, so cancellation cannot take them along.
- **Budgets are per source** — a chatty machine must not use up the budget of the quiet one; the
  quiet one is often the interesting one.
- **One dead source does not kill the session**; it is recorded as silent.
- **"Silent" needs an inventory.** Without knowing what a source declared, "nothing arrived" cannot
  be told from "nothing exists" — the header says `silent: unknown`, never `0 silent`.
- Observe **all sources in parallel** against one clock.

### A timeline is computed, never stored

Questions about a moment ("what did the plant show at t=20?") are answered from the session, not
recorded as interpretation — an artifact that already contains the reading cannot be read again
honestly.

- The unit of order is the **publish cycle**, not the event: values sampled together carry the same
  timestamp, and reading file order as sequence produces confident wrong findings. Group with a
  small tolerance.
- **Comparing sources needs an explicit grid.** A change stream says "became X" and then stays
  silent; "what was it at t?" means carrying values forward, and *how far* is the whole statement.
  So the grid is a required argument; a value carried too far is **marked, not dropped**.
- Clock offsets between sources are often dominated by **read latency, not drift** — one read
  cannot tell them apart.

### Exploratory sessions

A time-boxed session from a **charter** ("explore what happens when the capper faults mid-batch"),
gated by a **stance** (may it only observe? may it drive? may it inject faults?), producing a
findings report. Exploration works on **digests** of the stream, never on raw floods.

## 7 · Evidence and traceability

- **A run leaves evidence**: a machine-readable log of every step (JSONL), JUnit for CI, and a
  report for **humans** — what was checked, what was not, what is open.
- **The chain is explicit**: requirement → contract element → test → run → finding. It can be
  emitted as a traceability matrix, and its completeness can be measured.
- **Evidence sessions per test case**: who triggered the run and why, the inventory, the stream,
  the artifacts — plus a checksum manifest so a receiver can tell it is complete.
- **A release decision** is a consumer of declared thresholds (hard failures, safety coverage,
  requirement coverage) producing GO/NO-GO with a sign-off field — the tool proposes, a person signs.
- Regulated vocabulary to speak: ISO/IEC/IEEE 29119, ISTQB, GAMP 5, 21 CFR Part 11 — the tool
  itself needs qualification evidence too (its own tests, reproducible in CI).

## 8 · When the system changes

- **Drift** is a detected deviation between specification and system (or between versions).
  *Detection* is deterministic; *triage* must understand the cause — "tests drift and nobody knows
  why" is the failure mode to avoid. Sources: a spec change, or a developer (intended or not).
- **The triage ladder**: first the contract (does it explain the deviation?), then **precedent**
  (a ratified earlier finding with the same signature), only then a model. A repeat case is
  decided by precedent, without tokens.
- **Findings are the memory**: ratified by a person, stored in Git (JSONL), searchable by key.
  Retrieval mechanism by trade-off — keyed first; semantic search only when keyed provably misses.
- **Regression is asymmetric**: only PASS→FAIL, lost coverage or a vanished test break the build;
  improvements never do. A regression index is *derived*, never a second source of truth.
- **Change impact**: from a contract diff to the tests it touches.
- **Maintenance mode**: the spec moves, the test follows — demonstrably **without repairing to
  green**. A repair may touch mechanics (timeouts, fixtures, names), never the assertion.

## 9 · AI at the edge, human at the gate

- **The core needs no model and no tokens.** Deriving, running, checking, coverage: free and
  deterministic.
- **AI where structure runs out**: translating prose requirements into structured criteria,
  drafting a test for a requirement, diagnosing a red run, triaging a drift that neither contract
  nor precedent explains.
- **AI proposes, a person disposes.** Nothing an AI writes becomes part of the regression suite
  without a human approving it.
- **One provider interface**; every AI path is testable **offline** with a scripted provider (no
  key, no network). A trace switch shows the exact exchange with the model.
- **Grounding stays short**: conventions are a few lines; determinism enforces the rest. A long
  instruction file is a smell.
- **Guardrails and budgets**: an agent never reads or logs secrets, never rewrites, deletes or
  pushes the repository, and runs under a **hard step and token limit**. It gives up on purpose.
- **The authoring agent** acts as a test analyst: drive the system into a defined state, take a
  requirement, **iterate until the test is reproducible**, and propose it with remarks. Iteration
  may change mechanics, never the `then`.
- **Autonomy is an experiment, not a product**: running the loop without the human gate is easy;
  its value is measuring whether it optimises for "catches real faults" or merely for "green"
  (commenting out assertions, pinning bugs as expected behaviour). The gate is on by default and
  only an explicit flag turns it off.
- **Local models** answer a customer question ("nothing may leave our network"), not a feature
  question — measure whether a small model carries the prompts before building for it.
- **Agent skills ship with the package, installed on request**, owning only their own files: an
  unchanged file may be updated; a changed one is kept and the new version placed beside it;
  projects extend skills through a local rules file instead of editing them; a copy under another
  name belongs to the team; every update is a Git diff.

## 10 · Test levels, stances and the lifecycle of a test

- **Test levels**: an isolated service with mocked neighbours, a fully simulated system, real
  hardware. The same test language on every level. The tool must know which level it is on and
  what it may do there.
- **Stance**: `observe-only` · `drive` · `inject`. Production is observe-only *by environment*, not
  by convention — the environment imposes the stance and a command is refused before it is sent.
- **A test's lifecycle**: *proposed* (by derivation or an agent, regenerable) → *accepted* by a
  person → part of the **stable regression suite** (runs without AI, maintained, never thrown
  away). At scale, accepting needs a process — a pull request is a natural gate.
- **Two places for tests**, both using the same library: in the service's own repository as a CI
  stage (close to the code, neighbours mocked), and in a system test repository against a
  simulation or hardware.
- **Catch power** is the metric that matters: a stated fraction of a **fault catalog** (transport,
  logic, timing faults injected into a simulation) caught by the shipped suite — written down
  together with the ones it missed. Classic mutation testing does not apply to an external system;
  fault injection does.
- **A maturity ladder instead of percentages**: L0 open · L1 first cut · L2 working in a real
  project · L3 proven (edge cases *and* a dated run) · L4 sustained (measured repeatedly, survives
  a change to the system). A row reaches L3 only with a date and a run; a green counter is not
  evidence. The target grows, so every percentage lies.

## 13 · Rethink — open on purpose

- **How small can the core stay?** Few concepts, few commands; pip and pytest do the rest.
- **Sync or async tests?** Async is the honest model (drive and observe at once); a sync facade may
  read easier for simple cases.
- **Agents:** the loop *propose → run → diagnose → human approval* maps naturally onto a graph with
  checkpoints and an interrupt for the approval (LangGraph). Is that worth a dependency, or is a
  plain loop enough? Role-based multi-agent frameworks add a layer the problem does not need.
- **A frontend for conversational use** (MCP server or assistant skills) next to the CLI — does it
  justify its upkeep?
- **Mining invariants from sessions** (Daikon-style) — useful, or bounded by low observed diversity
  and drowning in false positives?
- **The demo plant**: a new, small simulation with a web panel — which domain shows the idea best?

## 14 · The order to build it in

1. **The language**: things, signals, `expect`, a fixture, one bus (REST), a tiny demo plant,
   tests that catch a product fault a control suite misses. CI green.
2. **Visible**: the demo plant's web panel and a README animation of a test turning red.
3. **Reach**: MQTT and OPC UA adapters, environments and address maps, probe.
4. **Safety net**: types from the contract, test ideas from the state machine.
5. **Evidence**: sessions, JSONL + JUnit + a human report, traceability.
6. **Change**: drift detection, the triage ladder, findings.
7. **AI**: drafting and diagnosing behind one provider, offline-testable; skills on request.
8. **Measure**: a fault catalog against the demo plant and the catch power of the shipped suite.
