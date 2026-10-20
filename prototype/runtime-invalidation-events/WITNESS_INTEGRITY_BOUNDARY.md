# Suite 60 — File witness integrity and recovery ambiguity

FileWitness is a plain-text fixture for subprocess testing, **not** a trusted monotonic counter. Suite 60 adds canonical unsigned decimal input validation (ASCII digits, no leading zeroes except 0, range 0..2^63-1), and exercises missing, empty, malformed, out-of-range, witness-ahead and witness-behind states. Startup must refuse all such states.

A coherent rollback of **both** the SQLite database and the untrusted witness file passes local consistency checks. This is an intentional demonstration of a remaining vulnerability; a matching value does not establish authenticity or freshness.

A corrupt/missing witness or inconsistent anchor must not trigger silent reprovisioning, counter reset, or automatic reauthorization. Recovery requires a separately designed authenticated operator/provisioning protocol and an actual independently protected monotonic source. No such mechanism is implemented.

Tests cover logical file contents and process-level behavior only, not interrupted file replacement, storage media failures, fsync guarantees, secure element behavior, real power loss, or actuator STOP.
