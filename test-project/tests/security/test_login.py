"""Security: under the password profile, the broker lets in only who should get in. A wrong
guess must not work, and neither may talking to it without encryption."""

import os
from urllib.parse import urlsplit

import pytest

from busproof.mqtt import BrokerUnreachable, MqttBus

URL = os.environ.get("BUSPROOF_MQTT_URL", "")
pytestmark = pytest.mark.skipif(
    not URL.startswith("mqtts:"), reason="only the password profile has a login"
)


async def connects() -> bool:
    try:
        async with MqttBus(URL, listen="#"):
            return True
    except BrokerUnreachable:
        return False


async def test_the_right_user_and_password_get_in():
    assert await connects()


async def test_no_login_is_refused(monkeypatch):
    monkeypatch.delenv("BUSPROOF_MQTT_USERNAME", raising=False)

    assert not await connects()


async def test_a_wrong_password_is_refused(monkeypatch):
    monkeypatch.setenv("BUSPROOF_MQTT_PASSWORD", "not-the-password")

    assert not await connects()


async def test_a_broker_we_have_no_reason_to_trust_is_refused(monkeypatch):
    monkeypatch.delenv("BUSPROOF_MQTT_CA", raising=False)

    assert not await connects()


async def test_talking_to_it_without_encryption_is_refused():
    parts = urlsplit(URL)

    with pytest.raises(BrokerUnreachable):
        async with MqttBus(f"mqtt://{parts.hostname}:{parts.port}", listen="#"):
            pass
