from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping

from saga.core import balance
from saga.core.seasons import describe_turn, season_for_turn, year_for_turn


@dataclass
class Resources:
    wood: int = balance.INITIAL_RESOURCES["wood"]
    food: int = balance.INITIAL_RESOURCES["food"]
    iron: int = balance.INITIAL_RESOURCES["iron"]
    silver: int = balance.INITIAL_RESOURCES["silver"]
    fame: int = balance.INITIAL_RESOURCES["fame"]
    population: int = balance.INITIAL_RESOURCES["population"]
    morale: int = balance.INITIAL_RESOURCES["morale"]
    ships: int = balance.INITIAL_RESOURCES["ships"]
    warriors: int = balance.INITIAL_RESOURCES["warriors"]
    discovery: int = balance.INITIAL_RESOURCES["discovery"]

    def clamp(self) -> None:
        for name in ("wood", "food", "iron", "silver", "fame", "ships", "warriors", "discovery"):
            setattr(self, name, max(0, int(getattr(self, name))))
        self.population = max(0, int(self.population))
        self.morale = min(balance.MORALE_MAX, max(balance.MORALE_MIN, int(self.morale)))

    def as_dict(self) -> dict[str, int]:
        self.clamp()
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | object | None) -> "Resources":
        resources = cls()
        if not isinstance(data, Mapping):
            return resources
        for name in asdict(resources):
            if name in data:
                setattr(resources, name, int(data[name]))
        resources.clamp()
        return resources


@dataclass
class GameState:
    resources: Resources = field(default_factory=Resources)
    turn_index: int = 0
    actions_taken_this_turn: int = 0
    rng_seed: int = 8675309
    rng_rolls_made: int = 0
    village_log: list[str] = field(default_factory=list)
    current_story: str = "A handful of families drag their boats above the tideline and name the place home."
    game_over: bool = False
    victory: bool = False
    ending_id: str | None = None
    shipyard_built: bool = False
    huts: int = 0
    tools: int = 0
    weak_event_chain: int = 0

    @property
    def year(self) -> int:
        return year_for_turn(self.turn_index)

    @property
    def season(self) -> str:
        return season_for_turn(self.turn_index)

    @property
    def turn_label(self) -> str:
        return describe_turn(self.turn_index)

    def log(self, message: str) -> None:
        self.village_log.append(message)
        if len(self.village_log) > 120:
            self.village_log = self.village_log[-120:]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "resources": self.resources.as_dict(),
            "turn_index": self.turn_index,
            "actions_taken_this_turn": self.actions_taken_this_turn,
            "rng_seed": self.rng_seed,
            "rng_rolls_made": self.rng_rolls_made,
            "village_log": list(self.village_log),
            "current_story": self.current_story,
            "game_over": self.game_over,
            "victory": self.victory,
            "ending_id": self.ending_id,
            "shipyard_built": self.shipyard_built,
            "huts": self.huts,
            "tools": self.tools,
            "weak_event_chain": self.weak_event_chain,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "GameState":
        state = cls(
            resources=Resources.from_dict(data.get("resources")),
            turn_index=int(data.get("turn_index", 0)),
            actions_taken_this_turn=int(data.get("actions_taken_this_turn", 0)),
            rng_seed=int(data.get("rng_seed", 8675309)),
            rng_rolls_made=int(data.get("rng_rolls_made", 0)),
            village_log=[str(item) for item in data.get("village_log", [])],
            current_story=str(data.get("current_story", "")),
            game_over=bool(data.get("game_over", False)),
            victory=bool(data.get("victory", False)),
            ending_id=data.get("ending_id"),
            shipyard_built=bool(data.get("shipyard_built", False)),
            huts=int(data.get("huts", 0)),
            tools=int(data.get("tools", 0)),
            weak_event_chain=int(data.get("weak_event_chain", 0)),
        )
        state.resources.clamp()
        return state

