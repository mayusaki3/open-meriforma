import struct
import zlib

from protocol_boundary import ProtocolBoundary
from wire_envelope import CRC, HEADER, decode, encode, MAX_FRAME


def message(**changes):
    m = dict(kind="heartbeat", unit="left", main_boot="M1", challenge="C1",
             forma_boot="F1", session="S1", sequence=1, ready=True)
    m.update(changes)
    return m


original = message()
frame = encode(original)
assert decode(frame) == original
assert len(frame) <= MAX_FRAME
assert decode(encode(message(kind="ready", sequence=0, ready=False))) == message(
    kind="ready", sequence=0, ready=False)
print("PASS binary envelope round trip and message kinds")

for broken in (frame[:-1], frame + b"x", b"", b"junk", frame[:3]):
    try:
        decode(broken)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid frame length accepted")
print("PASS truncated, oversized and malformed frames rejected")

bad_crc = bytearray(frame)
bad_crc[-1] ^= 1
try:
    decode(bytes(bad_crc))
except ValueError:
    pass
else:
    raise AssertionError("corrupted CRC accepted")
print("PASS accidental corruption detected by CRC32")

def repack(body):
    return body + CRC.pack(zlib.crc32(body))

for offset, replacement in ((0, b"XX"), (2, b"\\x02"), (3, b"\\x63")):
    body = bytearray(frame[:-CRC.size])
    body[offset:offset + len(replacement)] = replacement
    try:
        decode(repack(bytes(body)))
    except ValueError:
        pass
    else:
        raise AssertionError("invalid header accepted")
body = bytearray(frame[:-CRC.size])
body[HEADER.size - 2:HEADER.size] = struct.pack(">H", 100)
try:
    decode(repack(bytes(body)))
except ValueError:
    pass
else:
    raise AssertionError("invalid payload length accepted")
print("PASS version, kind, magic and length validation")

for invalid in (message(sequence=-1), message(sequence=True),
                message(ready=1), message(unit=""),
                message(session="x" * 49), message(kind="command"),
                dict(message(), unknown=1)):
    try:
        encode(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid logical message accepted")
print("PASS invalid logical fields rejected")

p = ProtocolBoundary(("left",), timeout=0.5)
p.start_main(boot_id="M1", challenge="C1")
assert p.establish("left", forma_boot="F1", main_boot="M1",
                   challenge="C1", session="S1")
assert p.receive(decode(frame), now=0.1)
assert p.authorize(explicit=True, now=0.1)
assert not p.receive(decode(frame), now=0.2)
assert p.eligible(now=0.2)
assert not p.eligible(now=0.7)
print("PASS decoded messages preserve session, sequence and timeout checks")
print("PASS all wire-envelope checks")
