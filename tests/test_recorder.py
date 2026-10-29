"""The recorder keeps every message, in order, with the time since the recording started."""

from busproof.recorder import Recorder


class Clock:
    """A clock the test moves by hand, so no test has to wait for real time to pass."""

    def __init__(self, now: float = 100.0):
        self.now = now

    def __call__(self) -> float:
        return self.now


def test_messages_are_kept_in_arrival_order_with_the_time_since_the_start():
    clock = Clock()
    recorder = Recorder(clock)

    clock.now += 0.5
    recorder.record("line/capper/state", "Starting")
    clock.now += 2.0
    recorder.record("line/capper/state", "Execute")

    states = [(message.value, message.at) for message in recorder.messages()]
    assert states == [("Starting", 0.5), ("Execute", 2.5)]


def test_messages_can_be_asked_for_one_topic():
    recorder = Recorder()
    recorder.record("line/capper/state", "Execute")
    recorder.record("line/capper/good_count", 7)
    recorder.record("line/capper/good_count", 8)

    counts = [message.value for message in recorder.messages("line/capper/good_count")]
    assert counts == [7, 8]


def test_latest_is_the_newest_received_message_and_ignores_what_was_sent():
    recorder = Recorder()
    recorder.record("line/capper/state", "Idle")
    recorder.record("line/capper/state", "Execute")
    recorder.record("line/capper/state", "Stopped", direction="sent")

    latest = recorder.latest("line/capper/state")
    assert latest is not None
    assert latest.value == "Execute"


def test_latest_is_none_before_anything_arrived():
    assert Recorder().latest("line/capper/state") is None


def test_thousands_of_messages_are_all_kept():
    recorder = Recorder()
    for count in range(10_000):
        recorder.record("line/capper/good_count", count)

    assert len(recorder) == 10_000
    assert recorder.messages()[-1].value == 9_999


def test_what_is_handed_out_is_a_copy_and_cannot_change_the_record():
    recorder = Recorder()
    recorder.record("line/capper/state", "Execute")

    recorder.messages().clear()

    assert len(recorder) == 1
