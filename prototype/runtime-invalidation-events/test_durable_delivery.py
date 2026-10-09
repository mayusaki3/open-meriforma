import tempfile
from pathlib import Path

from durable_delivery import DurableDelivery

with tempfile.TemporaryDirectory() as folder:
    path = str(Path(folder) / "delivery.sqlite")
    first = DurableDelivery(path)
    key = "body_graph:stance_01:invalidation"
    payload = {"domain": "body_graph", "execution_id": "stance_01", "kind": "execution_invalidated"}
    assert first.enqueue(key, payload)
    assert not first.enqueue(key, payload)
    batch = first.deliver(10.0)
    assert len(batch) == 1 and batch[0]["attempt"] == 1 and batch[0]["payload"] == payload
    assert first.deliver(10.5) == []
    first.close()
    print("PASS stable event key deduplicates enqueue and unacknowledged event survives restart")

    second = DurableDelivery(path)
    batch = second.deliver(11.0)
    assert len(batch) == 1 and batch[0]["attempt"] == 2
    assert second.acknowledge(key)
    assert not second.acknowledge(key)
    assert second.deliver(12.0) == []
    second.close()
    print("PASS missing ACK retries after interval and acknowledged event stops redelivery")

    third = DurableDelivery(path)
    assert third.deliver(20.0) == []
    assert not third.enqueue(key, payload)
    assert third.deliver(21.0) == []
    print("PASS acknowledged event replay remains suppressed across restart")

    assert third.watch_action("stop:1", 30.0)
    assert not third.watch_action("stop:1", 99.0)
    assert third.expired_actions(30.0) == []
    assert third.expired_actions(30.1) == ["stop:1"]
    assert third.action_status("stop:1") == "timed_out"
    assert not third.complete_action("stop:1", 30.1)
    print("PASS action deadline expires once and late completion cannot override timeout")

    assert third.watch_action("stop:2", 40.0)
    assert third.complete_action("stop:2", 39.9)
    assert third.expired_actions(41.0) == []
    assert third.action_status("stop:2") == "completed"
    assert not third.complete_action("stop:2", 39.9)
    third.close()
    reopened = DurableDelivery(path)
    assert reopened.action_status("stop:1") == "timed_out"
    assert reopened.action_status("stop:2") == "completed"
    reopened.close()
    print("PASS timely completion and terminal timeout state persist across restart")

print("PASS all durable-delivery checks")
