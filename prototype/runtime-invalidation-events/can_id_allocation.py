"""Provisional 11-bit CAN identifier allocation, not a wire standard.

Bits 10..9 priority, 8..6 message class, 5..0 node address.
A smaller CAN ID wins arbitration; source authenticity is not provided.
"""
KINDS = {"safety": (0, 0), "heartbeat": (1, 1),
         "control": (2, 2), "diagnostic": (3, 3)}
REVERSE = {(priority, message_class): kind
           for kind, (priority, message_class) in KINDS.items()}
MAX_ID = 0x7FF
BROADCAST = 0
RESERVED = 63


def encode_id(kind, node):
    if type(kind) is not str or kind not in KINDS:
        raise ValueError("unknown message kind")
    if type(node) is not int or not 1 <= node <= 62:
        raise ValueError("node address must be in 1..62")
    priority, message_class = KINDS[kind]
    return (priority << 9) | (message_class << 6) | node


def decode_id(identifier):
    if type(identifier) is not int or not 0 <= identifier <= MAX_ID:
        raise ValueError("not an 11-bit standard CAN ID")
    priority = (identifier >> 9) & 0b11
    message_class = (identifier >> 6) & 0b111
    node = identifier & 0b111111
    kind = REVERSE.get((priority, message_class))
    if kind is None or not 1 <= node <= 62:
        raise ValueError("unassigned or reserved CAN ID")
    return {"kind": kind, "node": node, "priority": priority}


def allocate_nodes(names):
    """Allocate deterministic addresses from a declared, ordered unit inventory."""
    if type(names) not in (tuple, list) or not 1 <= len(names) <= 62:
        raise ValueError("invalid inventory")
    if any(type(name) is not str or not name for name in names):
        raise ValueError("invalid node name")
    if len(set(names)) != len(names):
        raise ValueError("duplicate node name")
    return {name: index for index, name in enumerate(names, 1)}


def validate_allocation(mapping):
    if type(mapping) is not dict or not mapping:
        raise ValueError("invalid allocation")
    if any(type(name) is not str or not name for name in mapping):
        raise ValueError("invalid node name")
    if any(type(node) is not int or not 1 <= node <= 62
           for node in mapping.values()):
        raise ValueError("invalid node address")
    if len(set(mapping.values())) != len(mapping):
        raise ValueError("duplicate node address")
    return True
