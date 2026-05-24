from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Mapping

from game.buildings import expeditions_unlocked
from game.resources import ResourceStock, format_amounts


@dataclass(frozen=True)
class ExpeditionOutcome:
    chance: float
    reward: dict[str, float]
    population_delta: int
    message: str


@dataclass(frozen=True)
class ExpeditionDefinition:
    key: str
    name: str
    description: str
    requires_population: int
    cost: dict[str, float]
    outcomes: tuple[ExpeditionOutcome, ...]


EXPEDITIONS: tuple[ExpeditionDefinition, ...] = (
    ExpeditionDefinition(
        key="local_trade",
        name="Local Trade",
        description="Low-risk barter with farms and hamlets beyond the fjord.",
        requires_population=2,
        cost={"food": 12, "wood": 4},
        outcomes=(
            ExpeditionOutcome(
                chance=0.85,
                reward={"silver": 10, "food": 8},
                population_delta=0,
                message="Traders return with bright silver and sacks of grain.",
            ),
            ExpeditionOutcome(
                chance=0.15,
                reward={"silver": 18, "food": 12, "fame": 1},
                population_delta=0,
                message="A shrewd bargain becomes a story told around the hearth.",
            ),
        ),
    ),
    ExpeditionDefinition(
        key="coastal_raid",
        name="Coastal Raid",
        description="A dangerous strike against a guarded coast.",
        requires_population=4,
        cost={"food": 18, "iron": 6},
        outcomes=(
            ExpeditionOutcome(
                chance=0.80,
                reward={"silver": 24, "fame": 8, "iron": 10},
                population_delta=0,
                message="The raiders beach at dawn and come home laden with spoil.",
            ),
            ExpeditionOutcome(
                chance=0.20,
                reward={"silver": 12, "fame": 4, "iron": 4},
                population_delta=-1,
                message="The raid succeeds, but one oar-bench comes home empty.",
            ),
        ),
    ),
    ExpeditionDefinition(
        key="explore_unknown_shore",
        name="Explore Unknown Shore",
        description="Follow sea mist toward places not yet marked on the map.",
        requires_population=3,
        cost={"food": 20, "wood": 20},
        outcomes=(
            ExpeditionOutcome(
                chance=0.75,
                reward={"discovery": 1, "fame": 5},
                population_delta=0,
                message="Scouts mark a sheltered inlet beyond the whale-road.",
            ),
            ExpeditionOutcome(
                chance=0.25,
                reward={"fame": 1},
                population_delta=0,
                message="The shore yields little, but the crew returns wiser.",
            ),
        ),
    ),
)

EXPEDITION_BY_KEY = {expedition.key: expedition for expedition in EXPEDITIONS}


def can_run_expedition(
    resources: ResourceStock, building_counts: Mapping[str, int], key: str
) -> bool:
    if not expeditions_unlocked(building_counts):
        return False
    expedition = EXPEDITION_BY_KEY[key]
    if resources.population < expedition.requires_population:
        return False
    return resources.can_afford(expedition.cost)


def choose_outcome(expedition: ExpeditionDefinition, rng: Random) -> ExpeditionOutcome:
    roll = rng.random()
    cumulative = 0.0
    for outcome in expedition.outcomes:
        cumulative += outcome.chance
        if roll < cumulative:
            return outcome
    return expedition.outcomes[-1]


def run_expedition(
    resources: ResourceStock,
    building_counts: Mapping[str, int],
    key: str,
    rng: Random,
) -> tuple[bool, str]:
    if not can_run_expedition(resources, building_counts, key):
        return False, "The village is not ready for that expedition."

    expedition = EXPEDITION_BY_KEY[key]
    resources.spend(expedition.cost)
    outcome = choose_outcome(expedition, rng)
    resources.gain(outcome.reward)
    if outcome.population_delta:
        resources.add("population", outcome.population_delta)
        resources.clamp_population()

    reward_text = format_amounts(outcome.reward)
    return True, f"{outcome.message} (+{reward_text})"

