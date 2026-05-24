from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from random import Random
from typing import Mapping

from game.buildings import (
    BUILDING_BY_KEY,
    expeditions_unlocked,
    initial_building_counts,
    purchase_building,
)
from game.expeditions import run_expedition
from game.resources import ResourceStock, format_amounts
from game.tick import apply_offline_progress, apply_production, utc_now


MAX_EVENT_LOG_ENTRIES = 80
PRESTIGE_FAME_REQUIREMENT = 1000


@dataclass
class GameState:
    resources: ResourceStock = field(default_factory=ResourceStock)
    buildings: dict[str, int] = field(default_factory=initial_building_counts)
    last_saved_at: str = field(default_factory=lambda: utc_now().isoformat())
    event_log: list[str] = field(default_factory=list)
    saga_entries: int = 0
    prestige_points: int = 0

    def __post_init__(self) -> None:
        normalized = initial_building_counts()
        normalized.update(
            {key: max(0, int(value)) for key, value in self.buildings.items()}
        )
        self.buildings = normalized
        self.resources.clamp_population()

    @classmethod
    def new_game(cls) -> "GameState":
        state = cls()
        state.log("A small settlement wakes beside the cold shore.")
        return state

    @classmethod
    def from_save_data(cls, data: Mapping[str, object]) -> "GameState":
        resources = ResourceStock.from_dict(data.get("resources"))
        buildings = initial_building_counts()
        raw_buildings = data.get("buildings")
        if isinstance(raw_buildings, Mapping):
            for key in buildings:
                buildings[key] = max(0, int(raw_buildings.get(key, 0)))
        raw_event_log = data.get("event_log", [])
        event_log = [str(item) for item in raw_event_log][-MAX_EVENT_LOG_ENTRIES:]
        state = cls(
            resources=resources,
            buildings=buildings,
            last_saved_at=str(data.get("last_saved_at") or utc_now().isoformat()),
            event_log=event_log,
            saga_entries=int(data.get("saga_entries", 0)),
            prestige_points=int(data.get("prestige_points", 0)),
        )
        return state

    def to_save_data(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "resources": self.resources.as_dict(),
            "buildings": dict(self.buildings),
            "last_saved_at": self.last_saved_at,
            "event_log": list(self.event_log[-MAX_EVENT_LOG_ENTRIES:]),
            "saga_entries": self.saga_entries,
            "prestige_points": self.prestige_points,
        }

    def log(self, message: str) -> None:
        self.event_log.append(message)
        if len(self.event_log) > MAX_EVENT_LOG_ENTRIES:
            self.event_log = self.event_log[-MAX_EVENT_LOG_ENTRIES:]

    def gather_wood(self) -> bool:
        self.resources.add("wood", 1)
        self.log("Axes ring through the pines. (+1 wood)")
        return True

    def fish(self) -> bool:
        self.resources.add("food", 1)
        self.log("A line comes back silver with fish. (+1 food)")
        return True

    def mine_iron(self) -> bool:
        self.resources.add("iron", 1)
        self.log("Bog ore stains the hands dark. (+1 iron)")
        return True

    def hold_feast(self) -> bool:
        cost = {"food": 10}
        if not self.resources.spend(cost):
            self.log("The feast waits; the stores are too thin.")
            return False
        self.resources.add("fame", 3)
        self.log("The hall warms with song and boasting. (+3 fame)")
        return True

    def recruit_villager(self) -> bool:
        if self.resources.population >= self.resources.population_cap:
            self.log("No more families can fit beneath the current roofs.")
            return False
        cost = {"food": 20, "wood": 5}
        if not self.resources.spend(cost):
            self.log("Recruitment falters; the village needs food and timber.")
            return False
        self.resources.add("population", 1)
        self.log("A new household joins the shoreline settlement. (+1 population)")
        return True

    def buy_building(self, key: str) -> bool:
        building = BUILDING_BY_KEY[key]
        if purchase_building(self.resources, self.buildings, key):
            self.log(f"{building.name} raised against wind and salt.")
            if building.unlocks_expeditions:
                self.log("The shipyard opens the sea-road.")
            return True
        self.log(f"{building.name} remains a sketch in the sand.")
        return False

    def run_expedition(self, key: str, rng: Random | None = None) -> bool:
        rng = rng or Random()
        success, message = run_expedition(self.resources, self.buildings, key, rng)
        self.log(message)
        return success

    def tick(self, seconds: float = 1.0) -> dict[str, float]:
        return apply_production(self.resources, self.buildings, seconds)

    def apply_offline(
        self, now: datetime | None = None
    ) -> tuple[float, dict[str, float]]:
        seconds, gained = apply_offline_progress(
            self.resources, self.buildings, self.last_saved_at, now
        )
        self.last_saved_at = (now or utc_now()).isoformat()
        if seconds >= 1:
            if gained:
                self.log(
                    "While you were away, the village gathered "
                    f"{format_amounts(gained)}."
                )
            else:
                self.log("The village kept watch while you were away.")
        return seconds, gained

    def mark_saved(self, now: datetime | None = None) -> None:
        self.last_saved_at = (now or utc_now()).isoformat()

    def expeditions_available(self) -> bool:
        return expeditions_unlocked(self.buildings)

    def can_enter_saga(self) -> bool:
        return self.resources.fame >= PRESTIGE_FAME_REQUIREMENT

    def enter_saga(self) -> bool:
        # Prestige is intentionally stubbed for MVP so the future reset rules
        # have a clear method boundary without affecting current saves.
        self.log("The saga is not ready to be entered in this version.")
        return False

