"""Provisional application ACK envelope. CRC32 is NOT authentication."""
import struct
import zlib

MAGIC = b"MA"
VERSION = 1
HEADER = struct.Struct(">2sBHHHH")  # magic, version, transfer, source, destination, generation lengths
CRC = struct.Struct(">I")
MAX_IDENTIFIER = 64


def encode_ack(*, transfer_id, source, destination, generation):
    if type(transfer_id) is not int or not 0 <= transfer_id <= 65535:
        raise ValueError("invalid transfer ID")
    parts = []
    for value in (source, destination, generation):
        if type(value) is not str or not value:
            raise ValueError("invalid ACK identifier")
        data = value.encode("utf-8")
        if len(data) > MAX_IDENTIFIER:
            raise ValueError("ACK identifier too long")
        parts.append(data)
    body = HEADER.pack(MAGIC, VERSION, transfer_id, *(len(x) for x in parts))
    body += b"".join(parts)
    return body + CRC.pack(zlib.crc32(body))


def decode_ack(frame):
    if type(frame) is not bytes or len(frame) < HEADER.size + 3 + CRC.size:
        raise ValueError("invalid ACK frame")
    magic, version, tid, a, b, c = HEADER.unpack_from(frame)
    if magic != MAGIC or version != VERSION or any(
            not 1 <= n <= MAX_IDENTIFIER for n in (a, b, c)):
        raise ValueError("invalid ACK header")
    if len(frame) != HEADER.size + a + b + c + CRC.size:
        raise ValueError("ACK length mismatch")
    body = frame[:-CRC.size]
    if zlib.crc32(body) != CRC.unpack_from(frame, len(body))[0]:
        raise ValueError("ACK CRC mismatch")
    values = []
    offset = HEADER.size
    for length in (a, b, c):
        try:
            values.append(frame[offset:offset + length].decode("utf-8"))
        except UnicodeDecodeError as exc:
            raise ValueError("invalid ACK UTF-8") from exc
        offset += length
    return dict(transfer_id=tid, source=values[0],
                destination=values[1], generation=values[2])
