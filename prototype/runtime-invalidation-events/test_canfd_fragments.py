from canfd_fragments import CHUNK, Reassembler, fragment, parse
from wire_envelope import decode, encode
from protocol_boundary import ProtocolBoundary


def msg(unit="left", seq=0):
    return dict(kind="heartbeat", unit=unit, main_boot="M1",
                challenge="C1" + "x" * 40, forma_boot=unit + "-boot",
                session=unit + "-session", sequence=seq, ready=True)


wire = encode(msg())
frames = fragment(wire, transfer_id=7)
assert len(frames) >= 2 and all(len(f) <= 64 for f in frames)
r = Reassembler(timeout=0.5)
output = None
for f in frames:
    output = r.accept(f, source="peer-a", now=0.1)
assert output == wire and decode(output) == msg()
print("PASS 64-byte fragmentation and reassembly")

r = Reassembler(timeout=0.5)
assert r.accept(frames[-1], source="peer-a", now=0.1) is None
assert r.accept(frames[-1], source="peer-a", now=0.2) is None
for f in frames[:-1]:
    output = r.accept(f, source="peer-a", now=0.2)
assert output == wire
print("PASS out-of-order and identical duplicate fragments")

r = Reassembler(timeout=0.5)
a = fragment(encode(msg("left")), transfer_id=10)
b = fragment(encode(msg("right")), transfer_id=10)
assert r.accept(a[0], source="left", now=0.1) is None
assert r.accept(b[0], source="right", now=0.1) is None
left = right = None
for f in a[1:]:
    left = r.accept(f, source="left", now=0.2)
for f in b[1:]:
    right = r.accept(f, source="right", now=0.2)
assert decode(left) == msg("left") and decode(right) == msg("right")
print("PASS interleaved peers with independent transfer identity")

r = Reassembler(timeout=0.2, max_active=1)
assert r.accept(frames[0], source="peer-a", now=0.0) is None
try:
    r.accept(fragment(wire, transfer_id=8)[0], source="peer-a", now=0.1)
except ValueError:
    pass
else:
    raise AssertionError("capacity limit not enforced")
assert r.accept(frames[1], source="peer-a", now=0.3) is None
assert len(r.active) == 1
print("PASS timeout expiry and bounded active transfers")

for invalid in (b"", b"x" * 65, frames[0][:-1],
                bytes([0]) + frames[0][1:]):
    try:
        parse(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError("malformed fragment accepted")
r = Reassembler(timeout=0.5)
assert r.accept(frames[0], source="peer-a", now=0.1) is None
tampered = bytearray(frames[0])
tampered[-1] ^= 1
try:
    r.accept(bytes(tampered), source="peer-a", now=0.2)
except ValueError:
    pass
else:
    raise AssertionError("conflicting duplicate accepted")
assert not r.active
print("PASS malformed fragments and conflicting duplicates rejected")

r = Reassembler(timeout=0.5)
corrupted = bytearray(frames[-1])
corrupted[-1] ^= 1
received = None
for f in frames[:-1] + [bytes(corrupted)]:
    received = r.accept(f, source="peer-a", now=0.1)
try:
    decode(received)
except ValueError:
    pass
else:
    raise AssertionError("corrupted envelope passed CRC")
print("PASS end-to-end CRC32 rejects corrupted reassembly")

p = ProtocolBoundary(("left",), timeout=0.5)
p.start_main(boot_id="M1", challenge="C1" + "x" * 40)
assert p.establish("left", forma_boot="left-boot", main_boot="M1",
                   challenge="C1" + "x" * 40, session="left-session")
r = Reassembler(timeout=0.5)
for f in frames:
    received = r.accept(f, source="left", now=0.1)
assert p.receive(decode(received), now=0.1)
assert p.authorize(explicit=True, now=0.1)
assert not p.receive(decode(received), now=0.2)
print("PASS reassembled envelope reaches session and heartbeat checks")
print("PASS all canfd-fragment checks")
