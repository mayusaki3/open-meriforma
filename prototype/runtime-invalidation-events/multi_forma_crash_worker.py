"""Suite 63 child process: abrupt coordinator exit after partial/all reservations."""
import os
from pathlib import Path
import sys

from causal_integrated_can import CausalIntegratedCan
from monotonic_generation_crash_worker import FileWitness
from monotonic_generation_guard import MonotonicGenerationGuard as Guard


def ready():
    model = CausalIntegratedCan(("left", "right"))
    model.start(boot_id="M1", challenge="C1")
    for peer in model.link.units:
        assert model.submit(peer, 0, now=0.001, deadline=0.04)
    model.advance(until=0.02)
    model.deliver_acks(until=0.04)
    assert model.link.authorize(explicit=True, now=0.04)
    return model.link


def main():
    folder, mode = sys.argv[1:]
    root = Path(folder)
    guards = []
    try:
        for peer in ("left", "right"):
            witness = FileWitness(root / (peer + ".txt"))
            guard = Guard(str(root / (peer + ".sqlite")), witness)
            guards.append(guard)
            guard.bind(ready(), now=0.04)
            if mode == "after_left" and peer == "left":
                os._exit(71)
        if mode == "after_both":
            os._exit(71)
        raise ValueError("unknown mode")
    finally:
        for guard in guards:
            guard.close()


if __name__ == "__main__":
    main()
