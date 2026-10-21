# Suite 64 — Peer-local group-commit gate (synthetic)

A peer-local gate starts denied, requires a complete exact tuple of local peer, required peers, group epoch, generation, sequence and committed peers, and remains denied after revocation or restart until a fresh proof is explicitly installed. Tests cover missing/partial/mismatched/malformed proofs and stale execution contexts.

**This is only structural matching of a Python dict.** A caller can forge the entire proof; there is no cryptographic authentication, Main/peer identity verification, durable group-commit proof, peer-to-peer evidence, replay-resistant nonce, CAN-FD frame validation, or actuator output gate. It is a separate proof model, **not integrated into FormaCommandReceiver.receive()**. A matching forged proof must never be interpreted as production authority. Future work must integrate receiver-local gating and specify an authenticated transcript with device-bound peer commitments and crash-safe recovery.
