# Playbook — from a plant to evidence

How to test a plant with BusProof, step by step. Written for a person: every step can be done by
hand, with no agent. A skill (`SKILL.md`) is the agent form of a step and points here instead of
repeating it (docs/CONCEPT.md §4.4).

> **A living draft.** A step is written down once it has been gone through for real, on the
> demo line in this repository — not designed on paper first. Steps not yet gone through are
> named, and nothing more.

| # | Step | Gate | Written |
| --- | --- | --- | --- |
| 1 | [Agree the contract](#1--agree-the-contract) — what the plant offers, and how it behaves | | ✓ |
| 2 | Understand the system — derive test ideas from the contract | | |
| 3 | Plan — state transitions, boundary values, equivalence classes | **G1** | |
| 4 | Write the test — machine classes, fixtures, tests | | |
| 5 | Prove it catches — inject a fault, the test must turn red | | |
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

**With an agent** (later, as a skill): an agent may draft a contract from what the builders
delivered and list its open questions. It never invents a topic, field or state the delivered
documents do not contain (AGENTS.md), and a person agrees the contract before step 2 begins.
