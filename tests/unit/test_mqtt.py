"""The MQTT bus keeps every message as evidence, reads its credentials only when it connects, and
says in one line when the broker cannot be reached. All offline: a real broker comes with the
demo plant (M2)."""

import socket
import ssl

import pytest

from busproof.mqtt import BrokerUnreachable, MqttBus, broker, credentials, decode, tls_context

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
    assert broker("mqtt://broker.local:1884") == ("broker.local", 1884, False)
    assert broker("mqtt://broker.local") == ("broker.local", 1883, False)


def test_mqtts_means_tls_and_its_own_default_port():
    assert broker("mqtts://broker.local:8884") == ("broker.local", 8884, True)
    assert broker("mqtts://broker.local") == ("broker.local", 8883, True)


def test_another_scheme_is_refused_with_a_reason():
    with pytest.raises(ValueError, match="expected mqtt://host:port"):
        broker("http://broker.local")


def test_tls_always_checks_the_certificate_of_the_broker(monkeypatch):
    monkeypatch.delenv("BUSPROOF_MQTT_CA", raising=False)

    context = tls_context()

    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.check_hostname


def test_a_missing_certificate_authority_is_an_error_not_a_weaker_check(monkeypatch, tmp_path):
    monkeypatch.setenv("BUSPROOF_MQTT_CA", str(tmp_path / "no-such-ca.crt"))

    with pytest.raises(OSError):
        tls_context()


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
        BrokerUnreachable, match=f"cannot connect to the MQTT broker at 127.0.0.1:{port}"
    ):
        async with MqttBus(f"mqtt://127.0.0.1:{port}", listen=f"{LINE}/#"):
            pass


async def test_sending_before_connecting_says_how_to_connect():
    with pytest.raises(RuntimeError, match="async with MqttBus"):
        await MqttBus(URL, listen=f"{LINE}/#").send(f"{LINE}/capper/cmd", {"command": "Start"})
