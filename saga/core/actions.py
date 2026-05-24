from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from saga.content.action_text import ACTION_TEXT
from saga.core import balance
from saga.core.seasons import SEASONAL_EFFECTS
from saga.core.state import GameState


@dataclass(frozen=True)
class Action:
    id: str
    name: str
    description: str
    unavailable_reason: str | None = None

    @property
    def available(self) -> bool:
        return self.unavailable_reason is None


def _text(action_id: str) -> dict[str, str]:
    return ACTION_TEXT[action_id]


def _tool_bonus(state: GameState) -> float:
    return 1.0 + (state.tools * balance.TOOL_PRODUCTION_BONUS)


def _morale_multiplier(state: GameState) -> float:
    if state.resources.morale < balance.LOW_MORALE_THRESHOLD:
        return balance.LOW_MORALE_PRODUCTION_MULTIPLIER
    return 1.0


def _production_amount(state: GameState, base: int, season_multiplier: float) -> int:
    amount = base * season_multiplier * _tool_bonus(state) * _morale_multiplier(state)
    warrior_penalty = max(0, state.resources.warriors - 2)
    return max(1, int(round(amount - warrior_penalty * 0.35)))


def _afford_reason(state: GameState, costs: dict[str, int]) -> str | None:
    for resource, amount in costs.items():
        if getattr(state.resources, resource) < amount:
            return f"Needs {amount} {resource}."
    return None


def _reason_for(state: GameState, action_id: str) -> str | None:
    if state.game_over:
        return "The saga has ended."
    if state.actions_taken_this_turn >= balance.ACTIONS_PER_TURN:
        return "No actions remain this season."
    if action_id == "harvest_crops" and state.season == "Winter":
        return "Winter fields yield nothing."
    if action_id == "forge_tools":
        if state.tools >= balance.TOOLS_MAX:
            return "The village already has enough basic tools."
        return _afford_reason(
            state,
            {"wood": balance.TOOLS_WOOD_COST, "iron": balance.TOOLS_IRON_COST},
        )
    if action_id == "build_huts":
        return _afford_reason(state, {"wood": balance.HUT_WOOD_COST})
    if action_id == "train_warriors":
        if state.resources.population - state.resources.warriors <= 1:
            return "Too few free hands remain."
        return _afford_reason(
            state,
            {
                "food": balance.TRAIN_WARRIOR_FOOD_COST,
                "iron": balance.TRAIN_WARRIOR_IRON_COST,
            },
        )
    if action_id == "hold_feast":
        return _afford_reason(
            state,
            {"food": balance.FEAST_FOOD_COST, "silver": balance.FEAST_SILVER_COST},
        )
    if action_id == "trade_locally":
        return _afford_reason(
            state,
            {"food": balance.TRADE_FOOD_COST, "wood": balance.TRADE_WOOD_COST},
        )
    if action_id == "scout_coast":
        return _afford_reason(state, {"food": balance.SCOUT_FOOD_COST})
    if action_id == "build_shipyard":
        if state.shipyard_built:
            return "The shipyard is already built."
        return _afford_reason(
            state,
            {"wood": balance.SHIPYARD_WOOD_COST, "iron": balance.SHIPYARD_IRON_COST},
        )
    if action_id == "build_longship":
        if not state.shipyard_built:
            return "Requires a shipyard."
        return _afford_reason(
            state,
            {
                "wood": balance.LONGSHIP_WOOD_COST,
                "iron": balance.LONGSHIP_IRON_COST,
                "silver": balance.LONGSHIP_SILVER_COST,
            },
        )
    if action_id == "launch_expedition":
        if state.resources.ships < 1:
            return "Requires at least one longship."
        if state.resources.warriors < 3:
            return "Requires at least three warriors."
        return _afford_reason(state, {"food": balance.EXPEDITION_FOOD_COST})
    return None


ACTION_IDS = (
    "gather_wood",
    "fish_hunt",
    "harvest_crops",
    "build_huts",
    "forge_tools",
    "train_warriors",
    "hold_feast",
    "trade_locally",
    "scout_coast",
    "build_shipyard",
    "build_longship",
    "launch_expedition",
)


def available_actions(state: GameState) -> list[Action]:
    actions: list[Action] = []
    for action_id in ACTION_IDS:
        text = _text(action_id)
        actions.append(
            Action(
                id=action_id,
                name=text["name"],
                description=text["description"],
                unavailable_reason=_reason_for(state, action_id),
            )
        )
    return actions


def require_available(state: GameState, action_id: str) -> str | None:
    if action_id not in ACTION_IDS:
        return "Unknown action."
    return _reason_for(state, action_id)


def _apply_gather_wood(state: GameState) -> str:
    effects = SEASONAL_EFFECTS[state.season]
    gained = _production_amount(state, 10, effects.wood_multiplier)
    state.resources.wood += gained
    state.resources.morale -= 2
    return f"{_text('gather_wood')['result']} (+{gained} wood, -2 morale)"


def _apply_fish_hunt(state: GameState) -> str:
    effects = SEASONAL_EFFECTS[state.season]
    gained = _production_amount(state, 9, effects.food_multiplier)
    state.resources.food += gained
    return f"{_text('fish_hunt')['result']} (+{gained} food)"


def _apply_harvest_crops(state: GameState) -> str:
    gained = SEASONAL_EFFECTS[state.season].harvest_amount
    state.resources.food += gained
    return f"{_text('harvest_crops')['result']} (+{gained} food)"


def _apply_build_huts(state: GameState) -> str:
    state.resources.wood -= balance.HUT_WOOD_COST
    state.huts += 1
    state.resources.morale += 4
    return f"{_text('build_huts')['result']} (-{balance.HUT_WOOD_COST} wood, +4 morale)"


def _apply_forge_tools(state: GameState) -> str:
    state.resources.wood -= balance.TOOLS_WOOD_COST
    state.resources.iron -= balance.TOOLS_IRON_COST
    state.tools += balance.TOOLS_GAIN
    return f"{_text('forge_tools')['result']} (tools {state.tools}/{balance.TOOLS_MAX})"


def _apply_train_warriors(state: GameState) -> str:
    state.resources.food -= balance.TRAIN_WARRIOR_FOOD_COST
    state.resources.iron -= balance.TRAIN_WARRIOR_IRON_COST
    state.resources.warriors += 1
    state.resources.morale += 1
    return f"{_text('train_warriors')['result']} (+1 warrior)"


def _apply_hold_feast(state: GameState) -> str:
    state.resources.food -= balance.FEAST_FOOD_COST
    state.resources.silver -= balance.FEAST_SILVER_COST
    state.resources.morale += balance.FEAST_MORALE_GAIN
    state.resources.fame += balance.FEAST_FAME_GAIN
    return (
        f"{_text('hold_feast')['result']} "
        f"(+{balance.FEAST_MORALE_GAIN} morale, +{balance.FEAST_FAME_GAIN} fame)"
    )


def _apply_trade_locally(state: GameState) -> str:
    state.resources.food -= balance.TRADE_FOOD_COST
    state.resources.wood -= balance.TRADE_WOOD_COST
    state.resources.silver += balance.TRADE_SILVER_GAIN
    state.resources.iron += balance.TRADE_IRON_GAIN
    return (
        f"{_text('trade_locally')['result']} "
        f"(+{balance.TRADE_SILVER_GAIN} silver, +{balance.TRADE_IRON_GAIN} iron)"
    )


def _apply_scout_coast(state: GameState) -> str:
    state.resources.food -= balance.SCOUT_FOOD_COST
    state.resources.discovery += balance.SCOUT_DISCOVERY_GAIN
    state.resources.fame += 1
    return f"{_text('scout_coast')['result']} (+{balance.SCOUT_DISCOVERY_GAIN} discovery, +1 fame)"


def _apply_build_shipyard(state: GameState) -> str:
    state.resources.wood -= balance.SHIPYARD_WOOD_COST
    state.resources.iron -= balance.SHIPYARD_IRON_COST
    state.shipyard_built = True
    state.resources.fame += 2
    return f"{_text('build_shipyard')['result']} (+2 fame)"


def _apply_build_longship(state: GameState) -> str:
    state.resources.wood -= balance.LONGSHIP_WOOD_COST
    state.resources.iron -= balance.LONGSHIP_IRON_COST
    state.resources.silver -= balance.LONGSHIP_SILVER_COST
    state.resources.ships += 1
    state.resources.fame += 3
    return f"{_text('build_longship')['result']} (+1 ship, +3 fame)"


def _apply_launch_expedition(state: GameState) -> str:
    state.resources.food -= balance.EXPEDITION_FOOD_COST
    return _text("launch_expedition")["result"]


APPLIERS: dict[str, Callable[[GameState], str]] = {
    "gather_wood": _apply_gather_wood,
    "fish_hunt": _apply_fish_hunt,
    "harvest_crops": _apply_harvest_crops,
    "build_huts": _apply_build_huts,
    "forge_tools": _apply_forge_tools,
    "train_warriors": _apply_train_warriors,
    "hold_feast": _apply_hold_feast,
    "trade_locally": _apply_trade_locally,
    "scout_coast": _apply_scout_coast,
    "build_shipyard": _apply_build_shipyard,
    "build_longship": _apply_build_longship,
    "launch_expedition": _apply_launch_expedition,
}


def apply_action(state: GameState, action_id: str) -> tuple[bool, str]:
    reason = require_available(state, action_id)
    if reason is not None:
        return False, reason
    message = APPLIERS[action_id](state)
    state.resources.clamp()
    state.actions_taken_this_turn += 1
    state.current_story = message
    state.log(f"{state.turn_label}: {message}")
    return True, message

