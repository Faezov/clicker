from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from saga.content.story_events import EVENT_TEXT
from saga.core.rng import DeterministicRng
from saga.core.state import GameState


@dataclass(frozen=True)
class Event:
    id: str
    text: str
    weight: float
    apply: Callable[[GameState], None]


def _good_omen(state: GameState) -> None:
    state.resources.morale += 4
    state.resources.fame += 1


def _merchant_arrival(state: GameState) -> None:
    state.resources.iron += 2
    state.resources.silver += 1


def _storm_damage(state: GameState) -> None:
    loss = max(3, 8 - state.huts * 2)
    state.resources.wood -= loss
    state.resources.morale -= 2


def _sickness(state: GameState) -> None:
    if state.huts <= 0:
        state.resources.population -= 1
    state.resources.morale -= 4


def _wolf_attack(state: GameState) -> None:
    if state.resources.warriors <= 0:
        state.resources.population -= 1
        state.resources.morale -= 3
    else:
        state.resources.morale -= 1
        state.resources.fame += 1


def _bitter_feud(state: GameState) -> None:
    state.resources.morale -= 6


def _quiet_season(state: GameState) -> None:
    state.resources.morale += 1


EVENTS = (
    Event("good_omen", EVENT_TEXT["good_omen"], 1.0, _good_omen),
    Event("merchant_arrival", EVENT_TEXT["merchant_arrival"], 1.0, _merchant_arrival),
    Event("storm_damage", EVENT_TEXT["storm_damage"], 1.2, _storm_damage),
    Event("sickness", EVENT_TEXT["sickness"], 1.0, _sickness),
    Event("wolf_attack", EVENT_TEXT["wolf_attack"], 0.8, _wolf_attack),
    Event("bitter_feud", EVENT_TEXT["bitter_feud"], 0.9, _bitter_feud),
    Event("quiet_season", EVENT_TEXT["quiet_season"], 2.8, _quiet_season),
)


def select_random_event(state: GameState, rng: DeterministicRng) -> Event:
    weights = [event.weight for event in EVENTS]
    if state.season == "Winter":
        weights = [
            weight * 1.35 if event.id in {"storm_damage", "sickness"} else weight
            for event, weight in zip(EVENTS, weights)
        ]
    index = rng.choice_index(weights)
    return EVENTS[index]


def apply_random_event(state: GameState, rng: DeterministicRng) -> Event:
    event = select_random_event(state, rng)
    event.apply(state)
    state.resources.clamp()
    state.current_story = event.text
    state.log(f"{state.turn_label}: {event.text}")
    return event

