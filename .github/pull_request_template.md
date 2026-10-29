<!--
Title: "<milestone or area>: <what changes, in a few words>" — e.g. "M1: expect waits and says what it saw".
Delete any section that does not apply, and say why in one line instead of leaving it empty.
-->

## What and why

<!-- One or two sentences: what this changes, and the reason a user would recognise. -->

Milestone: <!-- M0 … M7, or "none" --> · Concept: <!-- section of docs/CONCEPT.md, if any -->

## Changes

<!-- The few changes a reviewer needs to know about — not a copy of the commit list. -->

-

## Provenance

<!-- Gate G2 needs to know who wrote what. -->

- Written by: <!-- a person / an agent (tool and model) / both -->
- Playbook step or skill used: <!-- if an agent wrote it; otherwise "—" -->

## Evidence

- [ ] `make check` green locally
- [ ] CI green for the final commit
- [ ] Every new piece has a test; a new check was seen to fail before it passed
- [ ] Docs updated where behaviour or a file's purpose changed (CONCEPT, CONTRIBUTING, README)

## Acceptance (gate G2)

- [ ] No secret in the change, and none needed to review it (`AGENTS.md`)
- [ ] No expectation weakened to make a test pass; if one changed, the reason is stated above
- [ ] Reviewed and approved by a person
