"""Suite 53: synthetic receiver generation rollover coordinator.

Process-local guard only. No durable epoch uniqueness, authentication, or motor control.
"""
from forma_command_receiver import FormaCommandReceiver


class ReceiverGenerationRegistry:
    def __init__(self):
        self.generations = set()
        self.current = None

    def bind(self, link, *, max_transfer_ids=65536):
        generation = link.generation
        # Never reconstruct a fresh history for a generation already used.
        if generation in self.generations:
            raise ValueError("generation already bound; history reset forbidden")
        if not link.eligible(now=0.04):
            raise ValueError("generation requires explicit live authorization")
        self.generations.add(generation)
        if self.current is not None:
            self.current._deny()
        self.current = FormaCommandReceiver(link, max_transfer_ids=max_transfer_ids)
        return self.current
