from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass
class DeterministicRng:
    seed: int
    rolls_made: int = 0

    def _random(self) -> random.Random:
        rng = random.Random(self.seed)
        for _ in range(self.rolls_made):
            rng.random()
        return rng

    def random(self) -> float:
        rng = self._random()
        value = rng.random()
        self.rolls_made += 1
        return value

    def randint(self, low: int, high: int) -> int:
        value = low + int(self.random() * ((high - low) + 1))
        return min(high, value)

    def choice_index(self, weights: list[float]) -> int:
        total = sum(weights)
        if total <= 0:
            return 0
        roll = self.random() * total
        cumulative = 0.0
        for index, weight in enumerate(weights):
            cumulative += weight
            if roll <= cumulative:
                return index
        return len(weights) - 1

