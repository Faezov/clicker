from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Mapping


RESOURCE_ORDER = (
    "wood",
    "food",
    "iron",
    "silver",
    "fame",
    "discovery",
    "population",
    "population_cap",
)

COUNT_RESOURCE_NAMES = {"population", "population_cap"}


@dataclass
class ResourceStock:
    wood: float = 0.0
    food: float = 0.0
    iron: float = 0.0
    silver: float = 0.0
    fame: float = 0.0
    discovery: float = 0.0
    population: int = 2
    population_cap: int = 5

    def get(self, name: str) -> float:
        self._validate_name(name)
        return float(getattr(self, name))

    def set(self, name: str, value: float) -> None:
        self._validate_name(name)
        if name in COUNT_RESOURCE_NAMES:
            setattr(self, name, max(0, int(value)))
            return
        setattr(self, name, max(0.0, float(value)))

    def add(self, name: str, amount: float) -> None:
        self.set(name, self.get(name) + amount)

    def gain(self, amounts: Mapping[str, float]) -> None:
        for name, amount in amounts.items():
            self.add(name, amount)

    def can_afford(self, cost: Mapping[str, float]) -> bool:
        return all(self.get(name) >= amount for name, amount in cost.items())

    def spend(self, cost: Mapping[str, float]) -> bool:
        if not self.can_afford(cost):
            return False
        for name, amount in cost.items():
            self.add(name, -amount)
        return True

    def clamp_population(self) -> None:
        self.population = max(1, min(self.population, self.population_cap))

    def as_dict(self) -> dict[str, float | int]:
        return {field.name: getattr(self, field.name) for field in fields(self)}

    @classmethod
    def from_dict(cls, data: Mapping[str, object] | object | None) -> "ResourceStock":
        stock = cls()
        if not isinstance(data, Mapping):
            return stock
        for field in fields(cls):
            raw_value = data.get(field.name, getattr(stock, field.name))
            if field.name in COUNT_RESOURCE_NAMES:
                setattr(stock, field.name, max(0, int(raw_value)))
            else:
                setattr(stock, field.name, max(0.0, float(raw_value)))
        stock.clamp_population()
        return stock

    @staticmethod
    def _validate_name(name: str) -> None:
        if name not in RESOURCE_ORDER:
            raise KeyError(f"Unknown resource: {name}")


def format_number(value: float) -> str:
    if value == int(value):
        return str(int(value))
    if abs(value) >= 100:
        return str(int(value))
    return f"{value:.1f}"


def format_amounts(amounts: Mapping[str, float]) -> str:
    if not amounts:
        return "None"
    parts: list[str] = []
    for name in RESOURCE_ORDER:
        if name in amounts and amounts[name] != 0:
            parts.append(f"{format_number(amounts[name])} {name.replace('_', ' ')}")
    for name, amount in amounts.items():
        if name not in RESOURCE_ORDER and amount != 0:
            parts.append(f"{format_number(amount)} {name.replace('_', ' ')}")
    return ", ".join(parts) if parts else "None"
