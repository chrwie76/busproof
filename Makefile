# The command menu — like the "scripts" in package.json. `make` alone lists them.
# Every target runs through uv, so it uses the versions pinned in uv.lock.

.DEFAULT_GOAL := help
.PHONY: help install lint format typecheck test plant-tests line-tests fat security-tests demo demo-down demo-reset check clean

# The demo's security profile: `make demo SECURITY=open` for a quick try, with no login and no
# encryption. The default is a generated password over TLS. Compose reads what is exported here.
SECURITY ?= password
CREDENTIALS := $(CURDIR)/demo/secrets
export SECURITY
ifeq ($(SECURITY),open)
export BROKER_PORT := 1883
export BUSPROOF_MQTT_PORT ?= 1884
export PLANT_MQTT_URL := mqtt://mosquitto:1883
export PLANT_MQTT_USERNAME :=
TEST_CONNECTION := BUSPROOF_MQTT_URL=mqtt://localhost:$(BUSPROOF_MQTT_PORT)
else
export BROKER_PORT := 8883
export BUSPROOF_MQTT_PORT ?= 8884
# Read only when a test runs, and never printed.
TEST_CONNECTION := BUSPROOF_MQTT_URL=mqtts://localhost:$(BUSPROOF_MQTT_PORT) \
	BUSPROOF_MQTT_USERNAME=busproof BUSPROOF_MQTT_PASSWORD=$$(cat $(CREDENTIALS)/password) \
	BUSPROOF_MQTT_CA=$(CREDENTIALS)/ca.crt
endif

help:  ## List the commands
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-12s %s\n", $$1, $$2}'

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

# Starts the plant in Docker, runs tests against it on a real broker, and always cleans up.
# 1: the units to start, 2: the pytest arguments.
define against_the_plant
	docker compose -f demo/compose.yaml up -d --build --wait $(1)
	(cd demo/line-tests && BUSPROOF_ENV=local $(TEST_CONNECTION) uv run pytest $(2)); \
	code=$$?; docker compose -f demo/compose.yaml down; exit $$code
endef

line-tests:  ## Test the whole line: the plant in Docker, on a real broker
	$(call against_the_plant,,--ignore=tests/fat)

fat:  ## Test the capper alone, without the line and without the SCU
	$(call against_the_plant,mosquitto capper,tests/fat)

security-tests:  ## Test who gets into the broker, with the broker alone
	$(call against_the_plant,mosquitto,tests/security)

demo:  ## Start the plant and its page, in the background
	docker compose -f demo/compose.yaml up -d --build --wait
	@echo "The line is at http://localhost:$${BUSPROOF_WEB_PORT:-8088} (security: $(SECURITY))"
ifeq ($(SECURITY),open)
	@echo "INSECURE: no login and no encryption. For a quick try only."
else
	@echo "Log in as busproof, with the password in demo/secrets/password."
endif

demo-down:  ## Stop the plant
	docker compose -f demo/compose.yaml down

demo-reset: demo-down  ## Stop the plant and throw its generated credentials away
	docker run --rm -v $(CURDIR)/demo:/demo alpine:3.20 rm -rf /demo/secrets

check: lint typecheck test plant-tests  ## Everything that runs offline; CI also runs fat and line-tests

clean:  ## Remove caches and build output
	rm -rf .pytest_cache .ruff_cache dist build
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
