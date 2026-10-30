"""The MQTT bus keeps every message as evidence, reads its credentials only when it connects, and
says in one line when the broker cannot be reached. All offline: a real broker comes with the
demo plant (M2)."""

import socket

import pytest

from busproof.mqtt import BrokerUnreachable, MqttBus, broker, credentials, decode

URL = "mqtt://localhost:1883"
LINE = "acme/plant1/packaging/line1"


# --- what arrives --------------------------------------------------------------------------------


def test_a_json_payload_is_read_as_its_value():
    assert decode(b'{"state": 6, "good_count": 120}') == {"state": 6, "good_count": 120}


def test_a_payload_that_is_not_json_is_kept_as_text_not_dropped():
    assert decode(b"state=6") == "state=6"


def test_a_payload_that_is_not_even_text_is_kept_as_bytes():
    assert decode(b"\xff\xfe") == b"\xff\xfe"


def test_every_message_from_the_broker_lands_in_the_recorder():
    bus = MqttBus(URL, listen=f"{LINE}/#")

    bus.arrived(f"{LINE}/capper", b'{"state": 6}')
    bus.arrived(f"{LINE}/unknown", b"garbage")

    assert [(message.topic, message.value) for message in bus.recorder.messages()] == [
        (f"{LINE}/capper", {"state": 6}),
        (f"{LINE}/unknown", "garbage"),
    ]


# --- connecting ----------------------------------------------------------------------------------


def test_the_broker_comes_from_an_mqtt_url():
    assert broker("mqtt://broker.local:1884") == ("broker.local", 1884)
    assert broker("mqtt://broker.local") == ("broker.local", 1883)


def test_another_scheme_is_refused_with_a_reason():
    with pytest.raises(ValueError, match="only mqtt://host:port for now"):
        broker("mqtts://broker.local:8883")


def test_credentials_are_read_from_the_environment(monkeypatch):
    monkeypatch.setenv("BUSPROOF_MQTT_USERNAME", "tester")
    monkeypatch.setenv("BUSPROOF_MQTT_PASSWORD", "not-a-real-one")

    assert credentials() == ("tester", "not-a-real-one")


def test_without_a_username_the_bus_connects_anonymously(monkeypatch):
    monkeypatch.delenv("BUSPROOF_MQTT_USERNAME", raising=False)

    assert credentials() == (None, None)


async def test_an_unreachable_broker_is_said_in_one_line():
    with socket.socket() as probe:  # a port that was free a moment ago: nobody listens there
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]

    with pytest.raises(
        BrokerUnreachable, match=f"cannot reach the MQTT broker at 127.0.0.1:{port}"
    ):
        async with MqttBus(f"mqtt://127.0.0.1:{port}", listen=f"{LINE}/#"):
            pass


async def test_sending_before_connecting_says_how_to_connect():
    with pytest.raises(RuntimeError, match="async with MqttBus"):
        await MqttBus(URL, listen=f"{LINE}/#").send(f"{LINE}/capper/cmd", {"command": "Start"})
