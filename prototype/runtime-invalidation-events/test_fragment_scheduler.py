from fragment_scheduler import FragmentScheduler
from canfd_fragments import fragment, parse

def frames(tid, size=120):
    return fragment(bytes([tid % 256]) * size, transfer_id=tid)

s = FragmentScheduler()
s.begin("M1:C1")
a, b = frames(7), frames(8)
for f in a:
    assert s.enqueue("diagnostic", "left", f, generation="M1:C1", now=0, deadline=0.02)
for f in b:
    assert s.enqueue("safety", "right", f, generation="M1:C1", now=0, deadline=0.02)
out = s.dispatch(until=0.02)
assert [r["key"] for r in out] == ([("M1:C1", "right", 8, i) for i in range(len(b))]
                                         + [("M1:C1", "left", 7, i) for i in range(len(a))])
assert all(parse(r["frame"])[1] == r["key"][3] for r in out)
print("PASS mixed-priority fragment identity and exact dispatch correlation")

s = FragmentScheduler()
s.begin("M1:C1")
assert s.enqueue("heartbeat", "left", frames(3)[0], generation="M1:C1", now=0, deadline=0.00001)
assert s.dispatch(until=0.01)[0]["late"]
assert s.status()["invalidated"] and not s.dispatch(until=0.02)
print("PASS fragment deadline miss fails closed and discards queued work")

s = FragmentScheduler(max_queue=1)
s.begin("M1:C1")
assert s.enqueue("diagnostic", "left", frames(1)[0], generation="M1:C1", now=0, deadline=1)
assert not s.enqueue("safety", "right", frames(2)[0], generation="M1:C1", now=0, deadline=1)
assert s.status()["invalidated"] and s.status()["queued"] == 0
print("PASS partial-transfer eviction invalidates whole generation")

s = FragmentScheduler()
s.begin("M1:C1")
assert s.enqueue("heartbeat", "left", frames(3)[0], generation="M1:C1", now=0, deadline=0.01)
s.begin("M2:C2")
assert not s.enqueue("heartbeat", "left", frames(3)[1], generation="M1:C1", now=0, deadline=0.01)
assert not s.dispatch(until=0.01)
assert s.enqueue("heartbeat", "left", frames(3)[0], generation="M2:C2", now=0.01, deadline=0.02)
assert s.dispatch(until=0.02)[0]["key"][0] == "M2:C2"
print("PASS session generation fencing and stale-fragment rejection")

s = FragmentScheduler()
s.begin("M1:C1")
f = frames(5)[0]
assert s.enqueue("control", "left", f, generation="M1:C1", now=0, deadline=0.01)
try:
    s.enqueue("control", "left", f, generation="M1:C1", now=0, deadline=0.01)
except ValueError:
    pass
else:
    raise AssertionError("duplicate fragment accepted")
assert not s.expire(now=0.02) and s.status()["queued"] == 0
assert not s.status()["physical_safety_verified"]
print("PASS duplicate identity rejection and pending-fragment expiry")
print("PASS all fragment-scheduler checks")
