# Receiver Transfer-ID Lifecycle — Suite 53 Design Review

Status: provisional engineering decision record (2026-10-18). Not an approved HLDocS specification or a verified embedded safety design.

## Observed prototype behavior

- `canfd_fragments.py` defines a 16-bit transfer ID (0–65535), 55-byte maximum fragment payload, and 256-byte maximum logical message.
- `FormaCommandReceiver` scopes IDs by (generation, source, transfer ID), tracks `reserved_transfers`, `seen_transfers`, and `expired_transfers` as Python sets, and rejects new IDs after `max_transfer_ids` is reached.
- The default `max_transfer_ids=65536` is a count of **unique (generation, source, ID) keys across all sources**, not 65536 IDs per Forma. Multiple sources share the capacity.
- An ID is reserved on the first received fragment, including incomplete transfers. An expired partial transfer cannot be resurrected. The receiver is revoked on capacity exhaustion.
- A fresh `FormaCommandReceiver` is needed for a fresh generation. No persistent anti-replay or authenticated generation exists.

## Capacity and operational implications

For an uninterrupted generation, at most 65,536 distinct transfer IDs exist **per source**, but the default receiver's global budget also caps the aggregate across sources at 65,536. For two equally active sources, this may exhaust near 32,768 IDs each. At 10 new transfers per second aggregate, 65,536 IDs last approximately 109 minutes; at 100/s aggregate, approximately 10.9 minutes. These are arithmetic examples, not measured traffic rates or guarantees.

Python sets and tuple/string objects have runtime-dependent overhead; the current implementation does not measure embedded memory. A theoretical 65,536-bit bitmap is 8,192 bytes **per source** (16,384 bytes for two sources) before session state, fragment buffers, validity markers, allocation overhead and other firmware needs. A bitmap can represent exact use within one generation but does not by itself authenticate epochs, persist history across reboot or authorize reuse.

## Proposed lifecycle contract (not implemented)

1. Treat a transfer ID as consumed when its first fragment is admitted, even if assembly later times out or is malformed.
2. Never evict consumed IDs within the same authenticated generation. A duplicate or replay remains rejected, including after 16-bit wrap.
3. Before exhaustion, Main initiates a planned generation rollover: revoke control authority, discard pending commands and partial buffers, establish a demonstrably fresh Main challenge and fresh Forma sessions for **all required peers**, re-check readiness and explicitly reauthorize. Do not automatically resume motion.
4. Reset transfer-ID history **only after** the new generation has been established and bound to the receiver. Old-generation frames must be rejected at the receiving boundary.
5. If rollover cannot be completed, or freshness/authenticity cannot be established, remain fail-closed. A mere new Python receiver instance is not proof of a safe rollover.
6. Define a reserved capacity margin and a traffic/latency budget before selecting an embedded representation. Per-source accounting and a global memory limit must be specified explicitly.

## Risks and unresolved questions

- Main challenge uniqueness and peer identity are trusted inputs in the current synthetic protocol; no cryptographic authentication or power-loss-safe monotonic counter is implemented.
- Restart while an old CAN frame is in flight needs a real wire-level epoch binding and receiver boot-state policy.
- A receiver's local `accepted` list is unbounded; the current tests use it as evidence and it is not suitable as an embedded command log.
- `Reassembler` permits identical duplicate fragments while a transfer is active. The exact retransmission contract and ordering policy remain undecided.
- The current `max_transfer_ids` budget is shared across sources, despite the per-source ID namespace; firmware should decide per-source vs global accounting.
- The current receiver marks expired IDs only when another fragment arrives; explicit timeout servicing without new traffic is not modeled.
- The current synthetic code does not encode the generation in fragment bytes; metadata is fixture-supplied.
- The physical inhibit/STOP path, timing, watchdog and actual CAN behavior are not verified.

## Proposed suite 53 scope

- Assert budget accounting with multiple sources and fail-closed exhaustion.
- Assert no ID reuse within a generation, including 65535→0 and late fragments.
- Assert a rollover **cannot** occur on mere receiver reconstruction with the same generation.
- Assert old-generation frames fail after a genuinely fresh generation and explicit reauthorization.
- Keep all tests synthetic; do not claim authenticated freshness or real motor safety.

## Decision gate

Do not replace the set-based reference with a bitmap or adopt a rollover implementation until per-source traffic budget, firmware memory budget, epoch authenticity and boot/recovery requirements are agreed.
