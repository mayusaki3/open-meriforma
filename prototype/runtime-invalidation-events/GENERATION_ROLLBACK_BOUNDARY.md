# Suite 57 — Durable generation rollback boundary

The SQLite registry from suites 54–56 protects against reusing generations in an intact, current local history. It does not protect against replacing the entire database with an earlier, internally consistent snapshot.

## Reproduction

1. Provision history and commit M1:C1.
2. Save a coherent database snapshot.
3. Commit M2:C2 to the current database.
4. Restore the older snapshot. SQLite quick_check and schema validation pass, because the snapshot is internally consistent.
5. A newly authorized synthetic link with M2:C2 can be bound again. This is an **expected demonstrated limitation**, not a safety property.

## External witness concept

An independently retained set or monotonic high-watermark can reject a restored history that omits known committed generations. The suite uses a simple set as a **test oracle only**. A witness rolled back with the database cannot detect the loss. A real solution requires defining identity, monotonicity, trust boundaries, atomic update ordering, failure handling, and recovery/provisioning policy.

A high-watermark only works if generation IDs are ordered by a trusted monotonic sequence. Current boot/challenge strings are not ordered or authenticated. Neither a second unprotected file nor a local hash is sufficient against coherent rollback.

## Not verified

Authentication of Main/Forma, secure monotonic counter or secure element, power-loss durability, physical CAN, firmware memory limits, actuator inhibition, or physical STOP. No production anti-rollback mechanism is implemented.
