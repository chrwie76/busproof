"""The fixtures every test project needs, as `page` comes with pytest-playwright.

Installed with BusProof, active without a line of code:

    settings  what busproof.toml says for the environment in BUSPROOF_ENV
    contract  the line and its machine contracts
    bus       the connection, open for one test, with a recorder of its own

What belongs to one plant — the machine objects and `running_line` — stays in the test project's
conftest.py, where a reader looks for it. These fixtures are asynchronous: the test project sets
`asyncio_mode = "auto"` for pytest-asyncio.
"""

from collections.abc import AsyncIterator

import pytest

from busproof.bus import Bus
from busproof.contract import LineContract, read_line
from busproof.settings import Settings, broker_url, read_settings


@pytest.fixture
def settings(request: pytest.FixtureRequest) -> Settings:
    return read_settings(request.config.rootpath)


@pytest.fixture
def contract(settings: Settings) -> LineContract:
    return read_line(settings.line)


@pytest.fixture
async def bus(settings: Settings, contract: LineContract) -> AsyncIterator[Bus]:
    # Imported only here: the core works without the mqtt extra, and so does collecting tests.
    from busproof.mqtt import MqttBus

    async with MqttBus(broker_url(), listen=contract.listen) as connected:
        yield connected
