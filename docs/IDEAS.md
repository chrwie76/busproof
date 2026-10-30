# Ideas — what BusProof is built on

BusProof tests systems whose parts talk asynchronously: machines, controllers and services that
exchange events and messages over MQTT, OPC UA or REST. This document holds the ideas behind it —
each with the reason it exists, because a rule without its reason gets broken the first time it
is inconvenient. Where an idea came from a mistake, the mistake is described too.

Contents: [0 North star](#0--north-star) · [1 Test language](#1--a-test-language-not-a-test-factory) ·
[2 Reaching a system](#2--reaching-a-system) · [3 Contract](#3--the-contract-is-the-source-of-knowledge) ·
[4 Oracles](#4--three-things-to-check-not-one) · [5 Observing](#5--observing-and-exploring) ·
[6 Verdicts](#6--honest-verdicts) · [7 Evidence](#7--evidence-and-traceability) ·
[8 Change](#8--when-the-system-changes) · [9 AI](#9--ai-at-the-edge-human-at-the-gate) ·
[10 Process](#10--test-levels-stances-and-the-lifecycle-of-a-test) ·
[11 Engineering](#11--engineering-the-tool-itself) · [12 Lessons](#12--lessons-that-cost-time) ·
[13 Rethink](#13--rethink--open-on-purpose) · [14 Order](#14--the-order-to-build-it-in)

---

## 0 · North star

**One question decides every design choice:** does it help someone test *their* system end to
end — point it at their backend, get a maintained pytest suite that catches a real fault, keeps
up when the system changes, and leaves evidence an auditor accepts?

Not elegance, rigour, determinism or cleverness. Those are means, kept only where they visibly
serve the question. Two consequences:

- **"Done" means it helped a user test their system** — shown by a suite that is green on the
  right test level, first locally, then in CI. A merged feature with green unit tests is not done.
- **A gap that blocks a user is a defect**, not an honestly documented limitation.

## 1 · A test language, not a test factory

The first attempt generated tests from a specification and forbade editing them. It worked
technically and nobody wanted it: a generated test that a person may not touch is a test that
person does not own. So BusProof is the other way round — **a vocabulary for writing tests**, the
way Playwright is for browsers.

### Things, signals, commands

- A test names a **thing** (`capper`, `scanner`, `line`) and its **signals** (`OutCount`,
  `Temperature`). It never names a topic, a node id or a URL. *Why:* the moment a test contains
  `plant/line/cmd`, it can no longer run against the same plant over another bus.
- A thing has **commands** (`start`, `stop`, `reset`) and a **state**. Commands are sent; states
  and signals are asserted.
- **Aggregates** (a line made of stations) are things too. An aggregate's state is the
  **consensus** of its members — a mixed line has *no* state. *Why:* letting one member speak for
  all ("the capper is idle, so the line is idle") once let a precondition pass on a half-running
  plant.

### `expect` waits

A plant is asynchronous: a command is answered now, its effect arrives later, a counter moves when
a unit has travelled. An assertion that reads once is a race; a test that sleeps first is a guess.

- Every matcher **reads until the plant agrees or a deadline says it will not.**
- Matchers worth having from the start: `to_be(v)`, `to_be_in(states)`, `rises_by(n)`,
  `remains(during)`, `remains_between(lo, hi, during)`; later `passes_through(state)`,
  `happens_before(other)`. The name tells the kind of check: `to_be…` asks where a signal ends
  up, a verb asks what it does over time; `within=` for what must happen at some point,
  `during=` for what must hold all along.
- **A baseline is read inside the window**, not before it: a counter that moved during setup is
  not evidence that it moves now.
- **Silence is not stability.** `remains` on a signal that never reports must fail — otherwise a
  misspelt name is the easiest green there is.
- Several expectations can run **concurrently** (`asyncio.gather`): "good units come out *and* no
  rejects are added in the same window". *Why:* a "no rejects" check alone passes on a line that
  is not producing.

### Failures say what they saw

`expected capper.RejectCount to stay at 4 for 20s — it changed; seen: 4 → 5 (12 reads)`.
Distinct values in order, repeats collapsed, the number of reads. A red run explains itself
without opening a log — for a person and for an AI diagnosing it.

### Types from the system description

Generate **types**, never tests: states as `Literal[...]`, commands as methods, signals with their
type and unit. A typo in `"Exectue"` or `.strat()` is red in the editor (pyright/Pylance) before
anything runs. When the system description changes, regenerate the types and the type checker
lists every test that no longer fits — maintenance without a model and without tokens.

### The project owns its architecture

The library gives building blocks; **the test project decides its structure** — its own
"page objects" for the plant (`line.start()`, `line.run_batch()`), its fixtures, its folders.
A library that scaffolds and checksums a project's layout makes every upgrade a negotiation.
What works in one project becomes an example to copy, not a template enforced by a tool.

## 2 · Reaching a system

### One seam, many buses

Every bus is an adapter with the same small set of verbs: **observe** (subscribe/poll and emit
events), **send a command**, **wait until** a predicate holds, **stimulate and wait** (send, then
wait for the effect), plus **inventory** (what does the system declare?) and **probe** (is it
there?). Callers ask the seam for the adapter; nothing else imports a protocol SDK.

- **SDKs are optional extras** (`busproof[mqtt]`, `[opcua]`, `[rest]`). The base install must run
  every non-protocol command with no SDK present — once, a config read pulled in the MQTT client
  through a chain of imports and the whole tool died on `version`.
- **An adapter declares what it can do** (`drives: true/false`) so a caller refuses *before*
  announcing "running 10 tests" and then dying on the first command.
- **One payload shape across buses:** `{thing: {signal: value}}`. Everything above the seam reads
  this shape, so a new bus changes no line above it. Note: an event is not always a value — an
  MQTT message may carry a machine's whole state, an OPC UA notification a single node.

### Bus personalities matter

- **Publish/subscribe** (MQTT): the system speaks when it wants; silence can mean a dead
  transport.
- **Change-only subscriptions** (OPC UA): the system speaks only on change; silence means
  "unchanged". Reports can lag the real change by a sampling interval.
- **Request/response** (REST): the system speaks only when asked; temporal resolution *is* the
  poll interval — a state shorter than it does not exist for the test. Say so in the adapter.
  A command's own response is fresh evidence and shows an immediate transition without a poll.
- **Read first, then act**, on every bus: a wait needs to know what "before" looked like.

### Addresses are injected, never guessed

**Structure is committed; addresses come from the environment.** A thing's description says what
it is and how to drive it; *where* it runs comes from (1) an environment variable, (2) an
environment's address map (`env/local.yaml`, `env/ci.yaml`), or (3) nowhere — and then the run
**fails loudly**, naming both places. *Why:* a silent fallback to `localhost` made live tests skip
and the run report green while testing nothing.

- Addresses are a string *or* a mapping from day one (`endpoint`, `security`, …), so a new protocol
  extends the format instead of breaking it.
- Credentials bind to the address they were resolved for — a token never travels to another host.
- **Probe before you run**: every declared address is checked, and the check says where each
  address came from.

### Find the project, not the current directory

The tool finds its project root itself (walking up to its config, as pytest does). A tool that
reads `./config.yaml` breaks the first time someone runs `pytest` from `tests/`.

## 3 · The contract is the source of knowledge

A **contract** is a role, not a format: the versioned, named reference for what correct means.
It can be YAML, an OpenAPI document, an OPC UA address space, an AsyncAPI file or prose — an
importer normalises it. ("We have no spec, but we have documentation" is a supported case.)

What it holds:

- **Things** with **variables** (type, unit, range), **commands**, and the **state machine**:
  states, the commands allowed in each, the transitions.
- **Acting states** — states a machine leaves on its own clock (`Starting`, `Stopping`,
  `Aborting`) — with their expected dwell time. A command then has *two* expectations: it leads
  to the acting state, and the acting state leads on within its time. *Why:* treating every
  transition as instantaneous hides exactly the timing faults that reach the field.
- **State roles**, so no code depends on state names: which state *produces*, which is *faulted*,
  which are *healthy*. When one domain renamed "Running" to "Execute", every consumer that
  compared against the literal broke silently; reading the role survives the next rename.
- **Requirements** with ids, copied into the repo **with a link** to where they are managed — the
  evidence must survive the ticket system.

What it is used for:

- **Types** (see 1) and **test ideas** — deterministically, at no cost:
  - *state transition*: every allowed transition, every refused command per state (the negative
    cases acceptance criteria forget);
  - *boundary value*: on, just inside and just outside every range;
  - *equivalence partitioning*: one representative per class of input.
- **Structural drift**: compare what the contract declares with what the live system declares
  (types, widths, missing or extra signals). Two buses reporting the *same* drift is strong
  evidence that the drift is real.
- **The destination gap**: where the contract is silent (which state does `reset` lead to from
  here?), drive the system, **witness** the answer and let a human ratify it into the contract —
  never pin it silently. A witnessed behaviour may be a bug.

**A self-describing system is not equipment.** When a plant publishes its own control model
(state machine objects, type definitions), an inventory must not count those nodes as machines.

## 4 · Three things to check, not one

1. **Control** — does it reach the right state, in the right order, refuse what it must refuse?
2. **Product** — does it *make* what it should? Units in versus units out, rejects, pass rate,
   recipe targets (ISA-88 style: what a batch must contain). *Why this is a level of its own:* a
   complete control suite can run green on a line that produces nothing.
3. **Timing** — does it happen within the time promised: latencies, dwell times, ordering
   constraints between events.

Product and timing checks can run **on a recording** as well as live, so a captured session can be
judged again under a new rule without re-running the plant.

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

## 6 · Honest verdicts

- **Pass, fail — and inconclusive.** When the evidence cannot decide (a race in an acting state,
  a bus that cannot answer while nothing changes), say so. Never turn it into a pass, never into a
  bare failure, never into a silent skip.
- **A skip must be visible and justified.** A suite that "passes" by skipping is the most dangerous
  result there is. Measured once: making skips loud turned "2 failures, 3 silent skips, 1 false
  green" into "6 failures, 3 honest skips" under the same fault.
- **Freshness is evidence.** "Unchanged" must be proven by fresh readings — and what counts as
  fresh depends on the bus: on a change-only bus, silence is normal. A freshness rule calibrated on
  one bus produced ten false failures on another.
- **Counters carry history** — assert movement, not position.
- **Real plants are random** — assert the rate a requirement states, not "zero failures".
- **A race is not a defect.** Timing assertions get tolerances, and a result inside the noise is
  inconclusive.

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

## 11 · Engineering the tool itself

- **Pinned dependencies**, optional extras per protocol, one CLI entry point, Python ≥ 3.11.
- **Version from Git** (tag = release, commits after it = unique dev versions) — a hand-kept
  version number is kept by nobody. Compare versions as versions, not strings (`dev10` > `dev9`).
- **Gates that bite**: lint blocks a commit, the test suite blocks a push, CI repeats both on a
  server. A gate that silently skips when its environment is missing is no gate — make it say so.
- **A guard before the tool call** for AI assistants: refuse writes into protected areas, any touch
  of secrets, hand edits of generated files — with tests for both halves (what it refuses, what it
  must let through).
- **A neutrality test**: the library must not contain domain words of any one plant.
- **Generated files are read-only and guarded** (a drift test fails on hand edits); regenerate them.
- **Line endings pinned** in `.gitattributes`; Windows ↔ Linux moves otherwise bury real changes.
- **A demo system in the repo**, runnable with one command — the fastest proof that the tool works.

## 12 · Lessons that cost time

- A complete control suite ran **green on a line that produced nothing** → product oracle (§4).
- **Silent skips** made a broken run look healthy → visible, justified skips (§6).
- **Freshness rules don't transfer between buses** → bus-aware evidence (§2, §6).
- **One machine speaking for the line** let a precondition pass on a half-running plant →
  consensus for aggregates (§1).
- **State literals in consumers** broke when a domain renamed its states → state roles (§3).
- **A self-describing control model counted as equipment** inflated drift from 25 to 145 →
  inventories filter the system's own description (§3).
- **Stopping strands units in flight**; they are rejected while idle and fail inspection after the
  restart — a whole class of faults that only shows up *across* a stop/start → tests must cover
  transitions of the whole line, not only steady state.
- **Counters reset while units are still moving** produce impossible values (negative buffers) →
  invariants on counters belong in the product oracle.
- **A tool that guessed `localhost`** tested nothing and reported green → loud address resolution.
- **A config read pulled in a protocol SDK** and broke the base install → lazy imports, an
  import test with every SDK blocked.
- **Truncating payloads for prompt budgets** corrupted data on the wire → trimming belongs to the
  prompt, never to the transport.
- **A command spelling no branch handled was silently ignored** → refuse unknown commands by name,
  listing the accepted ones.
- **Code that existed only in a container image** was nearly lost → the image is built from Git,
  never the other way round.
- **Building the factory before the language**: a powerful generator, 28 commands and a scaffold
  that nobody adopted. Start with what a user types in a test.

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
