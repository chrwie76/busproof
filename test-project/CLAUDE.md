# CLAUDE.md

The tests of a packaging line, written with BusProof. What is where: [README.md](README.md).

Rules for every agent, above all about secrets and the contract: @AGENTS.md

## Commands

From the repository root, `make line-tests` starts the plant in Docker, runs these tests on a
real broker and cleans up; `make fat` does the same for the capper alone.
