from __future__ import annotations

from dataclasses import dataclass


SEASON_NAMES = ("Spring", "Summer", "Autumn", "Winter")


@dataclass(frozen=True)
class SeasonalEffects:
    wood_multiplier: float
    food_multiplier: float
    harvest_amount: int
    upkeep_food_per_person: float
    morale_delta: int


SEASONAL_EFFECTS = {
    "Spring": SeasonalEffects(
        wood_multiplier=1.0,
        food_multiplier=1.15,
        harvest_amount=4,
        upkeep_food_per_person=0.8,
        morale_delta=1,
    ),
    "Summer": SeasonalEffects(
        wood_multiplier=1.0,
        food_multiplier=1.25,
        harvest_amount=14,
        upkeep_food_per_person=0.7,
        morale_delta=1,
    ),
    "Autumn": SeasonalEffects(
        wood_multiplier=1.05,
        food_multiplier=1.0,
        harvest_amount=12,
        upkeep_food_per_person=0.9,
        morale_delta=0,
    ),
    "Winter": SeasonalEffects(
        wood_multiplier=0.75,
        food_multiplier=0.55,
        harvest_amount=0,
        upkeep_food_per_person=1.4,
        morale_delta=-4,
    ),
}


def season_for_turn(turn_index: int) -> str:
    return SEASON_NAMES[turn_index % len(SEASON_NAMES)]


def year_for_turn(turn_index: int) -> int:
    return (turn_index // len(SEASON_NAMES)) + 1


def describe_turn(turn_index: int) -> str:
    return f"Year {year_for_turn(turn_index)}, {season_for_turn(turn_index)}"

