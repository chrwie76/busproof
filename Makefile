# The command menu — like the "scripts" in package.json. `make` alone lists them.
# Every target runs through uv, so it uses the versions pinned in uv.lock.

.DEFAULT_GOAL := help
.PHONY: help install lint format typecheck test plant-tests line-tests fat check clean

help:  ## List the commands
	@grep -E '^[a-z]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-10s %s\n", $$1, $$2}'

install:  ## Create .venv, install everything, set up the Git hooks
	uv sync --all-packages --all-extras
	uv run pre-commit install --hook-type pre-commit --hook-type pre-push

lint:  ## Check style and common mistakes
	uv run ruff check .
	uv run ruff format --check .

format:  ## Fix style in place
	uv run ruff check --fix .
	uv run ruff format .

typecheck:  ## Check types
	uv run pyright

test:  ## Run the tests
	uv run pytest

plant-tests:  ## Run the demo plant's own tests: does the simulation compute right?
	cd demo/plant && uv run pytest

line-tests:  ## Run the demo's test project, offline against its stand-in plant
	cd demo/line-tests && BUSPROOF_ENV=offline uv run pytest

fat:  ## Test the capper alone, on a real broker in Docker
	docker compose -f demo/compose.yaml up -d --build mosquitto capper
	(cd demo/line-tests && BUSPROOF_ENV=local BUSPROOF_MQTT_URL=mqtt://localhost:$${BUSPROOF_MQTT_PORT:-1884} uv run pytest tests/fat); \
	code=$$?; docker compose -f demo/compose.yaml down; exit $$code

check: lint typecheck test plant-tests line-tests  ## Everything CI runs

clean:  ## Remove caches and build output
	rm -rf .pytest_cache .ruff_cache dist build
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
