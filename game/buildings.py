from __future__ import annotations

from dataclasses import dataclass, field
from math import ceil
from typing import Mapping

from game.resources import ResourceStock


BUILDING_COST_SCALE = 1.15


@dataclass(frozen=True)
class BuildingDefinition:
    key: str
    name: str
    description: str
    base_cost: dict[str, float]
    production: dict[str, float] = field(default_factory=dict)
    population_cap_bonus: int = 0
    requires_population: int = 0
    unlocks_expeditions: bool = False


BUILDINGS: tuple[BuildingDefinition, ...] = (
    BuildingDefinition(
        key="hut",
        name="Hut",
        description="Raises the settlement's shelter and population cap.",
        base_cost={"wood": 15, "food": 5},
        population_cap_bonus=2,
    ),
    BuildingDefinition(
        key="fishing_pier",
        name="Fishing Pier",
        description="Nets steady food from the cold shore.",
        base_cost={"wood": 35, "food": 10},
        production={"food": 0.25},
    ),
    BuildingDefinition(
        key="lumber_camp",
        name="Lumber Camp",
        description="Turns the nearby woods into beams and firewood.",
        base_cost={"wood": 30, "food": 5},
        production={"wood": 0.20},
    ),
    BuildingDefinition(
        key="forge",
        name="Forge",
        description="Smelts bog iron into nails, tools, and blades.",
        base_cost={"wood": 80, "iron": 25},
        production={"iron": 0.10},
        requires_population=3,
    ),
    BuildingDefinition(
        key="longhouse",
        name="Longhouse",
        description="Gives the village a hearth for oaths and stories.",
        base_cost={"wood": 120, "food": 60, "iron": 20},
        production={"fame": 0.05},
        requires_population=5,
    ),
    BuildingDefinition(
        key="shipyard",
        name="Shipyard",
        description="Opens the sea-road to trade, raids, and discoveries.",
        base_cost={"wood": 220, "iron": 75, "fame": 20},
        requires_population=7,
        unlocks_expeditions=True,
    ),
)

BUILDING_BY_KEY = {building.key: building for building in BUILDINGS}


def initial_building_counts() -> dict[str, int]:
    return {building.key: 0 for building in BUILDINGS}


def current_cost(building: BuildingDefinition, owned: int) -> dict[str, int]:
    return {
        resource: ceil(amount * (BUILDING_COST_SCALE**owned))
        for resource, amount in building.base_cost.items()
    }


def production_for_buildings(building_counts: Mapping[str, int]) -> dict[str, float]:
    totals: dict[str, float] = {}
    for key, owned in building_counts.items():
        building = BUILDING_BY_KEY[key]
        for resource, amount in building.production.items():
            totals[resource] = totals.get(resource, 0.0) + amount * owned
    return totals


def can_purchase_building(
    resources: ResourceStock, building_counts: Mapping[str, int], key: str
) -> bool:
    building = BUILDING_BY_KEY[key]
    owned = building_counts.get(key, 0)
    if resources.population < building.requires_population:
        return False
    return resources.can_afford(current_cost(building, owned))


def purchase_building(
    resources: ResourceStock, building_counts: dict[str, int], key: str
) -> bool:
    if not can_purchase_building(resources, building_counts, key):
        return False

    building = BUILDING_BY_KEY[key]
    owned = building_counts.get(key, 0)
    resources.spend(current_cost(building, owned))
    building_counts[key] = owned + 1
    if building.population_cap_bonus:
        resources.add("population_cap", building.population_cap_bonus)
    return True


def expeditions_unlocked(building_counts: Mapping[str, int]) -> bool:
    return building_counts.get("shipyard", 0) > 0

