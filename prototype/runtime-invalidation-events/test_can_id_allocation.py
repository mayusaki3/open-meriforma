from can_id_allocation import (KINDS, allocate_nodes, decode_id,
                               encode_id, validate_allocation)

nodes = allocate_nodes(("left", "right", "head"))
assert nodes == {"left": 1, "right": 2, "head": 3}
assert validate_allocation(nodes)
assert len({encode_id(kind, node) for kind in KINDS for node in nodes.values()}) == 12
for kind in KINDS:
    for node in nodes.values():
        assert decode_id(encode_id(kind, node))["kind"] == kind
        assert decode_id(encode_id(kind, node))["node"] == node
print("PASS deterministic address allocation, roundtrip and collision-free IDs")

for node in nodes.values():
    assert (encode_id("safety", node) < encode_id("heartbeat", node)
            < encode_id("control", node) < encode_id("diagnostic", node))
assert max(encode_id("safety", n) for n in nodes.values()) < min(
    encode_id("heartbeat", n) for n in nodes.values())
assert max(encode_id("heartbeat", n) for n in nodes.values()) < min(
    encode_id("control", n) for n in nodes.values())
assert max(encode_id("control", n) for n in nodes.values()) < min(
    encode_id("diagnostic", n) for n in nodes.values())
print("PASS safety-first CAN arbitration priority across nodes")

for bad in (0, 63, -1, True, 1.0):
    try:
        encode_id("heartbeat", bad)
    except ValueError:
        pass
    else:
        raise AssertionError(("reserved node accepted", bad))
for bad in (-1, 2048, True, 1.5, "0x40", 0, 63, 0x7ff, 0x100):
    try:
        decode_id(bad)
    except ValueError:
        pass
    else:
        raise AssertionError(("unassigned ID accepted", bad))
print("PASS reserved addresses, malformed and unassigned IDs rejected")

for bad in ((), ("left", "left"), ("",), (42,), tuple(str(i) for i in range(63))):
    try:
        allocate_nodes(bad)
    except ValueError:
        pass
    else:
        raise AssertionError(("invalid inventory accepted", bad))
for bad in ({"a": 1, "b": 1}, {"a": 0}, {"a": 63}, {"a": True}, {}):
    try:
        validate_allocation(bad)
    except ValueError:
        pass
    else:
        raise AssertionError(("invalid allocation accepted", bad))
print("PASS duplicate node addresses and invalid inventories rejected")

assert len({encode_id(kind, n) for kind in KINDS for n in range(1, 63)}) == 248
print("PASS complete 62-node by four-class ID uniqueness")
print("PASS all can-id-allocation checks")
