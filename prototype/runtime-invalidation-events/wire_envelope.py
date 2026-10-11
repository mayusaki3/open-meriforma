"""Provisional transport-neutral binary envelope (NOT a CAN-FD wire format).

CRC32 detects accidental corruption, not spoofing or malicious modification.
A frame is complete only when the caller supplies its exact bytes.
"""
import struct
import zlib

MAGIC = b"MF"
VERSION = 1
KINDS = {"heartbeat": 1, "ready": 2}
REVERSE_KINDS = {v: k for k, v in KINDS.items()}
FIELDS = frozenset({"kind", "unit", "main_boot", "challenge",
                    "forma_boot", "session", "sequence", "ready"})
MAX_FIELD = 48
MAX_PAYLOAD = 128
MAX_FRAME = 256
HEADER = struct.Struct(">2sBBIBH")  # magic, version, kind, sequence, ready, payload length
CRC = struct.Struct(">I")


def _encode_fields(message):
    result = bytearray()
    for key in ("unit", "main_boot", "challenge", "forma_boot", "session"):
        value = message[key]
        if type(value) is not str or not value:
            raise ValueError("invalid identifier")
        data = value.encode("utf-8")
        if len(data) > MAX_FIELD:
            raise ValueError("identifier too long")
        result.append(len(data))
        result.extend(data)
    if len(result) > MAX_PAYLOAD:
        raise ValueError("payload too large")
    return bytes(result)


def encode(message):
    if type(message) is not dict or set(message) != FIELDS:
        raise ValueError("invalid message fields")
    if message["kind"] not in KINDS:
        raise ValueError("invalid kind")
    seq = message["sequence"]
    if type(seq) is not int or not 0 <= seq <= 0xFFFFFFFF:
        raise ValueError("invalid sequence")
    if type(message["ready"]) is not bool:
        raise ValueError("invalid ready flag")
    payload = _encode_fields(message)
    body = HEADER.pack(MAGIC, VERSION, KINDS[message["kind"]],
                       seq, int(message["ready"]), len(payload)) + payload
    frame = body + CRC.pack(zlib.crc32(body))
    if len(frame) > MAX_FRAME:
        raise ValueError("frame too large")
    return frame


def decode(frame):
    if type(frame) is not bytes or not HEADER.size + CRC.size <= len(frame) <= MAX_FRAME:
        raise ValueError("invalid frame length")
    magic, version, kind, sequence, ready, length = HEADER.unpack_from(frame)
    if magic != MAGIC or version != VERSION or kind not in REVERSE_KINDS or ready not in (0, 1):
        raise ValueError("invalid frame header")
    if length > MAX_PAYLOAD or len(frame) != HEADER.size + length + CRC.size:
        raise ValueError("payload length mismatch")
    body = frame[:-CRC.size]
    (received_crc,) = CRC.unpack_from(frame, len(body))
    if zlib.crc32(body) != received_crc:
        raise ValueError("frame CRC mismatch")
    payload = frame[HEADER.size:-CRC.size]
    offset = 0
    values = {}
    for key in ("unit", "main_boot", "challenge", "forma_boot", "session"):
        if offset >= len(payload):
            raise ValueError("missing identifier")
        size = payload[offset]
        offset += 1
        if not 1 <= size <= MAX_FIELD or offset + size > len(payload):
            raise ValueError("invalid identifier length")
        try:
            values[key] = payload[offset:offset + size].decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("invalid UTF-8") from exc
        offset += size
    if offset != len(payload):
        raise ValueError("trailing payload")
    return {"kind": REVERSE_KINDS[kind], "sequence": sequence,
            "ready": bool(ready), **values}
