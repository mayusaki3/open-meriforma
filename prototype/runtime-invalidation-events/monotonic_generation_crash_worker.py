"""Suite 59 worker: synthetic crash windows across witness and SQLite commits."""
import os
from pathlib import Path
import sys

from causal_integrated_can import CausalIntegratedCan
from monotonic_generation_guard import MonotonicGenerationGuard, SimulatedWitness


class FileWitness(SimulatedWitness):
    """Untrusted file-backed test fixture, NOT an anti-rollback counter."""

    def __init__(self, path, *, crash_on_advance=False):
        self.path = Path(path)
        self.crash_on_advance = crash_on_advance
        try:
            raw = self.path.read_bytes()
            # Canonical decimal only. This is validation, not authentication.
            if (not raw or len(raw) > 20 or not raw.isascii()
                    or not raw.isdigit() or (len(raw) > 1 and raw.startswith(b"0"))):
                raise ValueError("invalid witness encoding")
            value = int(raw)
            if value > 9223372036854775807:
                raise ValueError("witness outside SQLite INTEGER range")
        except (OSError, ValueError) as exc:
            raise ValueError("witness unavailable or malformed") from exc
        super().__init__(value)

    def advance(self, expected):
        next_value = super().advance(expected)
        temp = self.path.with_suffix(".tmp")
        temp.write_text(str(next_value), encoding="ascii")
        os.replace(temp, self.path)
        if self.crash_on_advance:
            os._exit(71)
        return next_value


def authorized_link():
    model = CausalIntegratedCan(("left", "right"))
    model.start(boot_id="M1", challenge="C1")
    for unit in model.link.units:
        assert model.submit(unit, 0, now=0.001, deadline=0.04)
    model.advance(until=0.02)
    model.deliver_acks(until=0.04)
    assert model.link.authorize(explicit=True, now=0.04)
    return model.link


def main():
    db_path, witness_path, mode = sys.argv[1:]
    witness = FileWitness(witness_path, crash_on_advance=mode == "after_witness")
    guard = MonotonicGenerationGuard(db_path, witness)
    if mode == "before_witness":
        os._exit(71)
    guard.bind(authorized_link(), now=0.04)
    if mode == "after_commit":
        os._exit(71)
    raise AssertionError("unknown crash mode")


if __name__ == "__main__":
    main()
