# Suite 62 — Synthetic partial group generation reservations

Suite 62 uses two separate SQLite generation registries and two SimulatedWitness counters. It checks all-peer reservation, missing/extra peers, an unauthorized second peer after the first commits, and a second-peer witness mismatch. The group gate remains disabled on partial failure, existing receiver instances are revoked, and the same group object cannot retry after an ambiguous partial reservation.

This is a **single-process sequential coordinator**, not a distributed protocol. The coordinator can set `enabled=True` only after both reservations succeed; it does not implement authenticated acknowledgments, group-commit proofs, local receiver enforcement of group permission, durable coordinator state, or a multi-node consensus protocol. Even a successful test cannot demonstrate that a Forma cannot actuate independently. The synthetic witness is not protected hardware. No actual CAN-FD, brownout, motor output or physical STOP is tested.

Future protocol design must bind identity, required-peer membership, group epoch, local sequence and cryptographic authorization; handle coordinator crash between peer reservations and after final reservation, delayed/duplicated acknowledgments, and a Forma independently verifying the group-commit proof before enabling its actuator.
