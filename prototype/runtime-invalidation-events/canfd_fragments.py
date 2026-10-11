"""Synthetic CAN-FD-sized fragment adapter, not a CAN bus driver.

9-byte fragment header; at most 55 bytes of logical payload per frame.
Caller provides monotonic time and a transfer ID unique among live transfers.
"""
import math
import struct

MAGIC = b"CF"
VERSION = 1
HEADER = struct.Struct(">2sBHBBH")  # magic, version, transfer ID, index, count, total bytes
FRAME_LIMIT = 64
CHUNK = FRAME_LIMIT - HEADER.size
MAX_MESSAGE = 256


def fragment(message, *, transfer_id):
    if type(message) is not bytes or not 1 <= len(message) <= MAX_MESSAGE:
        raise ValueError("invalid logical message")
    if type(transfer_id) is not int or not 0 <= transfer_id <= 65535:
        raise ValueError("invalid transfer ID")
    count = (len(message) + CHUNK - 1) // CHUNK
    return [HEADER.pack(MAGIC, VERSION, transfer_id, i, count, len(message))
            + message[i * CHUNK:(i + 1) * CHUNK] for i in range(count)]


def parse(frame):
    if type(frame) is not bytes or not HEADER.size < len(frame) <= FRAME_LIMIT:
        raise ValueError("invalid fragment length")
    magic, version, transfer_id, index, count, total = HEADER.unpack_from(frame)
    if magic != MAGIC or version != VERSION or not 1 <= total <= MAX_MESSAGE:
        raise ValueError("invalid fragment header")
    expected_count = (total + CHUNK - 1) // CHUNK
    if count != expected_count or index >= count:
        raise ValueError("invalid fragment index/count")
    expected_length = min(CHUNK, total - index * CHUNK)
    if len(frame) - HEADER.size != expected_length:
        raise ValueError("invalid fragment payload size")
    return transfer_id, index, count, total, frame[HEADER.size:]


class Reassembler:
    def __init__(self, *, timeout, max_active=4):
        if type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("invalid timeout")
        if type(max_active) is not int or not 1 <= max_active <= 64:
            raise ValueError("invalid capacity")
        self.timeout = float(timeout)
        self.max_active = max_active
        self.active = {}
        self.last_now = 0.0

    def accept(self, frame, *, source, now):
        if type(source) is not str or not source:
            raise ValueError("invalid source")
        if type(now) not in (int, float) or not math.isfinite(now) or now < self.last_now:
            raise ValueError("invalid monotonic time")
        now = float(now)
        self.last_now = now
        self.expire(now=now)
        tid, index, count, total, payload = parse(frame)
        key = (source, tid)
        entry = self.active.get(key)
        if entry is None:
            if len(self.active) >= self.max_active:
                raise ValueError("reassembly capacity exhausted")
            entry = {"count": count, "total": total, "parts": {}, "last": now}
            self.active[key] = entry
        if (entry["count"], entry["total"]) != (count, total):
            del self.active[key]
            raise ValueError("conflicting transfer metadata")
        if index in entry["parts"] and entry["parts"][index] != payload:
            del self.active[key]
            raise ValueError("conflicting duplicate fragment")
        entry["parts"][index] = payload
        entry["last"] = now
        if len(entry["parts"]) != count:
            return None
        message = b"".join(entry["parts"][i] for i in range(count))
        del self.active[key]
        if len(message) != total:
            raise ValueError("reassembly length mismatch")
        return message

    def expire(self, *, now):
        for key, entry in list(self.active.items()):
            if now - entry["last"] > self.timeout:
                del self.active[key]
