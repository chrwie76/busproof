# Playbook — from a plant to evidence

How to test a plant with BusProof, step by step. Written for a person: every step can be done by
hand, with no agent. A skill (`SKILL.md`) is the agent form of a step and points here instead of
repeating it (docs/CONCEPT.md §4.4).

> **A living draft.** A step is written down once it has been gone through for real, on the
> demo line in this repository — not designed on paper first. Steps not yet gone through are
> named, and nothing more.

| # | Step | Gate | Written |
| --- | --- | --- | --- |
| 1 | [Agree the contract](#1--agree-the-contract) — what the plant offers, and how it behaves; or discover it, if none is written | | ✓ (agree) |
| 2 | Understand the system — derive test ideas from the contract | | |
| 3 | Plan — state transitions, boundary values, equivalence classes | **G1** | |
| 4 | [Write the test](#4--write-the-test) — machine classes, fixtures, tests | | ✓ |
| 5 | [Prove it catches](#5--prove-it-catches) — inject a fault, the test must turn red | | ✓ |
| 6 | Review and accept | **G2** | |
| 7 | Run, produce evidence | | |
| 8 | Judge a red run | **G3** | |
| 9 | Explore under a charter | | |
| 10 | Release | **G4** | |

The four gates are where a person decides, with or without an agent (docs/CONCEPT.md §4.5).

---

## 1 · Agree the contract

**Why.** A test can only be as right as what it compares against. The contract is the *test
basis*: what the plant offers and how it behaves, written down so that the plant and the tests
both follow it — and neither owns it. Without it, a test checks what someone guessed.

**What goes in.** Whatever the machine builders deliver: interface descriptions, PLC tag
lists, an OPC UA NodeSet, the standard the machines claim (PackML, Weihenstephan Standards), and
the layout of the line. And a person who can answer questions about the plant.

**What comes out** (the demo's are in `demo/contracts/`):

| File | Answers |
| --- | --- |
| `machines/<machine>.asyncapi.yaml` | How one machine talks: topics, payload fields, types, ranges, commands |
| a state machine, e.g. `packml.yaml` | How a machine behaves: states, their numbers on the wire, the commands each accepts, where acting states lead |
| `line.yaml` | Which machines make the line, in which order, and where it stands |

**How, by hand.** Ask these questions in this order; each answer is a line in a contract.

1. **Which machines are there, and who built each?** One contract per machine, as each builder
   delivers one — so a machine can be tested alone at the maker's (FAT) and in the line (SAT).
2. **Where does a machine publish?** Topics follow ISA-95 down to the machine
   (`{enterprise}/{site}/{area}/{line}/capper`). The contract leaves the first four as
   parameters; where the machine stands is the line's business.
3. **What is in a message?** One message per machine with its whole state, or one per value?
   Ask how the plant really does it — do not choose what is easier to test.
4. **Names or numbers?** Real controllers, OPC UA and gRPC send states as numbers. Write the
   numbers into the contract as they are on the wire; the test project reads them by name
   (an `IntEnum`), never the other way round.
5. **How does a machine behave?** Its states, which command is accepted in which state, which
   states it leaves on its own. Write every allowed command out per state — no "everywhere
   except" rules a reader has to work out.
6. **What are the limits?** Types, ranges (`minimum`, `maximum`), required fields.

**Done when**

- [ ] every machine of the line has a contract, and every contract is valid AsyncAPI 3.0
      (`make check` validates it against the official schema)
- [ ] the state machine is sound: each state has its own number, every transition leads to a
      state that exists, every state can be reached
- [ ] every machine sends exactly the state numbers, and takes exactly the commands, of its
      state machine
- [ ] no contract names a server or a site
- [ ] a person who knows the plant has read the contracts and agrees *(the contract is a
      decision, not a draft)*

**What we ran into, and how it was avoided**

- *One contract for the whole line* felt simpler — but no machine builder delivers that, and
  it makes a test of one machine alone impossible.
- *Choosing the message shape for the tests' convenience* (one topic per value) — the contract
  describes the plant, not the wishes of its tests.
- *Readable state names on the wire* — fine for a demo, wrong for a real controller. Numbers
  on the wire, names in the test.
- *Leaving the state machine out* because AsyncAPI has no place for it — without it, a test
  cannot tell an allowed jump from a fault.
- *A second toolchain for one check* — the official AsyncAPI tools are JavaScript; the same
  schema checks the contract from Python.

### No contract yet? Discover it

*Not tried yet — the tool comes with M4 (docs/CONCEPT.md, decision 24).*

Many plants run without a written contract. It exists all the same — in the PLC program, the
HMI tag list, a few heads, and in what the bus carries every day. So it can be found:

1. **Listen.** Connect BusProof in the `observe` stance — it sends nothing — and record long
   enough to see the plant do its work: a shift, a batch, a start and a stop.
2. **Draft.** From the recording comes a contract draft: the topics seen, their fields and
   types, the ranges observed, the states and every change between them that occurred.
3. **Agree.** A person who knows the plant goes through the draft line by line. A change like
   `Execute → Idle` without `Stopping` gets a verdict: *meant so*, or *a fault we have had for
   years*. Only what is agreed becomes the contract.
4. **Loop.** Tests from the contract run against the plant. Each deviation asks: *the plant or
   the contract?* The answer sharpens one of them — and shows how far the contract carries.

**Observed is not right.** A draft pins what the plant does, not what it should do. Every
contract therefore says where it comes from — delivered by its maker, observed, or agreed by
whom and when — so an auditor can follow the test basis as well as the tests.

**With an agent** (later, as a skill): an agent may draft a contract — from what the builders
delivered, or from a recording — list its open questions, and propose what a deviation means.
It never invents a topic, field or state that neither the documents nor the recording contain
(AGENTS.md), and a person agrees the contract before step 2 begins. In a legacy plant this is
where an agent helps most: reading thousands of messages is its work, judging them is not.

---

## 4 · Write the test

*Written from the demo line; steps 2 and 3 are still to come, so what to test was chosen by hand.*

**What goes in.** The agreed contracts of step 1, and a plant to run against.

**What comes out** (the demo's are in `demo/line-tests/`):

| File | What it is |
| --- | --- |
| `busproof.toml` | One section per environment; `BUSPROOF_ENV` picks one |
| `machines/` | One class per machine, like page objects: signals and commands by their names in the contract, no `expect` inside |
| `conftest.py` | Preconditions in layers: `line` → `idle_line` → `running_line` |
| `tests/` | One folder per kind of question: control, product, timing |

**How, by hand.**

1. **Ask three questions, not one.** Control: does it obey? Product: what does it make? Timing: when?
   A suite that only asks the first runs green on a line that makes nothing.
2. **Bring the plant to a known state first.** It remembers the last test. A precondition starts from
   whatever is there, here with `Abort` and `Clear`, and waits until it has got there.
3. **Wait for the system, and only ever for the system.** No `sleep`. A command is answered later,
   and by more than one party: `Start` too soon after the machines are in `Idle` is refused by an SCU
   that is not there yet. Wait for whoever will take the next command.
4. **Name what must stay the same.** "Rejects stay at 0 for 8 seconds, while the filler keeps running"
   says more than a count at the end. Silence does not pass: `remains` needs fresh messages.
5. **Say what a whole run must add up to.** Some faults show in no single value: bottles filled must
   equal those accounted for.

**Done when**

- [ ] no test names a topic, and every name is in the contract
- [ ] every test sets up its own precondition, and passes in any order
- [ ] the whole suite is green several times in a row: **one green run proves little**

**What we ran into, and how it was avoided**

- *A test that did not check what its name says*: it waited for both sides to reach `Execute`, in any
  order, and was called "only once every machine is there". Read each test against its name.
- *A check that fired for the wrong reason*: "a counter went down" was true of every reset, so the
  test of that fault passed without finding it. Measure from where the behaviour starts.
- *A race that passed by luck*: green once, red the next time. Only repeated runs showed it.
- *A limit from wishful thinking*: "a bottle is never faster than 5 s" ignored that the plant moves in
  steps. A limit needs a reason.

## 5 · Prove it catches

A test that was never seen to fail proves little: it may check nothing at all. Here is how to see it fail.

**How, by hand.**

1. **Switch a real fault on.** A parameter where one causes it, a test handle otherwise
   (`demo/plant/FAULTS.md`), or change the plant's code for one run.
2. **Run the whole suite, and read what turns red.** Exactly the test meant for it should, and a good
   control test should stay green: a line showing `Execute` and making nothing is a fault of the
   product, not of control.
3. **Read the message.** It should explain the fault without opening the plant:
   `it rose by 0; seen: 0 (41 messages)`.
4. **Keep it.** Where a fault can be switched on in the test itself, write it down
   (`tests/faults/`): the check has to find the fault, and a clean run has to stay clean.
5. **Run the check that really contains the test.** A probe once came back green because the command
   used did not run the tests in question at all.

**Done when**

- [ ] every kind of fault you claim to catch has been seen turning a test red
- [ ] for each, a clean run stays green

**With an agent** (later, as a skill): an agent may propose faults and run this step. It never weakens
an expectation to make a test pass (`AGENTS.md`), and a test it wrote stays proposed until a person
accepts it (gate G2).
