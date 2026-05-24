from __future__ import annotations

from saga.core.events import apply_random_event
from saga.core.rng import DeterministicRng
from saga.core.state import GameState


def test_same_seed_selects_same_event_and_effects() -> None:
    state_a = GameState(rng_seed=123)
    state_b = GameState(rng_seed=123)
    rng_a = DeterministicRng(123)
    rng_b = DeterministicRng(123)

    event_a = apply_random_event(state_a, rng_a)
    event_b = apply_random_event(state_b, rng_b)

    assert event_a.id == event_b.id
    assert state_a.resources.as_dict() == state_b.resources.as_dict()
    assert rng_a.rolls_made == rng_b.rolls_made

