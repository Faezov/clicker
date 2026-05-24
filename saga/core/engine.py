from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from saga.content.endings import ENDING_TEXT
from saga.core import balance
from saga.core.actions import Action, apply_action, available_actions
from saga.core.events import apply_random_event
from saga.core.rng import DeterministicRng
from saga.core.seasons import SEASONAL_EFFECTS, describe_turn
from saga.core.state import GameState


@dataclass(frozen=True)
class ActionResult:
    success: bool
    message: str
    turn_ended: bool = False


class GameEngine:
    def __init__(self, state: GameState | None = None) -> None:
        self.state = state or self.start_new_game()

    @staticmethod
    def start_new_game(seed: int = 8675309) -> GameState:
        state = GameState(rng_seed=seed)
        state.log("A handful of families drag their boats above the tideline and name the place home.")
        state.log(f"The first season begins: {describe_turn(state.turn_index)}.")
        return state

    def rng(self) -> DeterministicRng:
        return DeterministicRng(self.state.rng_seed, self.state.rng_rolls_made)

    def commit_rng(self, rng: DeterministicRng) -> None:
        self.state.rng_rolls_made = rng.rolls_made

    def available_actions(self) -> list[Action]:
        return available_actions(self.state)

    def can_end_turn(self) -> bool:
        return not self.state.game_over and self.state.actions_taken_this_turn > 0

    def apply_action(self, action_id: str) -> ActionResult:
        if self.state.game_over:
            return ActionResult(False, "The saga has ended.")

        success, message = apply_action(self.state, action_id)
        if not success:
            return ActionResult(False, message)

        if action_id == "launch_expedition":
            self.resolve_expedition()
            return ActionResult(True, self.state.current_story, False)

        self.check_win_loss()
        if self.state.game_over:
            return ActionResult(True, self.state.current_story, False)

        if self.state.actions_taken_this_turn >= balance.ACTIONS_PER_TURN:
            self.end_turn()
            return ActionResult(True, message, True)

        return ActionResult(True, message, False)

    def end_turn(self) -> None:
        if self.state.game_over:
            return

        self.apply_seasonal_upkeep()
        if self.check_win_loss():
            return

        rng = self.rng()
        apply_random_event(self.state, rng)
        self.commit_rng(rng)
        if self.check_win_loss():
            return

        self.update_weakness_chain()
        if self.check_win_loss():
            return

        self.state.turn_index += 1
        self.state.actions_taken_this_turn = 0

        if self.state.turn_index >= balance.TOTAL_TURNS:
            self.end_game(False, "time_lost")
            return

        self.state.current_story = f"{describe_turn(self.state.turn_index)} begins."
        self.state.log(self.state.current_story)

    def apply_seasonal_upkeep(self) -> None:
        effects = SEASONAL_EFFECTS[self.state.season]
        food_needed = int(round(self.state.resources.population * effects.upkeep_food_per_person))
        self.state.resources.food -= food_needed
        self.state.resources.morale += effects.morale_delta
        if self.state.resources.food < 0:
            self.state.resources.morale += self.state.resources.food
        self.state.resources.clamp()
        self.state.log(
            f"{self.state.turn_label}: upkeep consumes {food_needed} food."
        )

    def update_weakness_chain(self) -> None:
        resources = self.state.resources
        weak = (
            resources.population <= balance.WEAKNESS_POPULATION_THRESHOLD
            or resources.morale <= balance.WEAKNESS_MORALE_THRESHOLD
            or resources.food <= balance.WEAKNESS_FOOD_THRESHOLD
        )
        if weak:
            self.state.weak_event_chain += 1
            self.state.log(
                f"Weakness deepens in the settlement ({self.state.weak_event_chain}/{balance.WEAKNESS_EVENT_LIMIT})."
            )
        else:
            self.state.weak_event_chain = 0

    def resolve_expedition(self) -> None:
        resources = self.state.resources
        score = (
            resources.warriors * balance.EXPEDITION_WARRIOR_SCORE
            + resources.morale * balance.EXPEDITION_MORALE_SCORE
            + resources.fame * balance.EXPEDITION_FAME_SCORE
            + resources.discovery * balance.EXPEDITION_DISCOVERY_SCORE
        )
        if self.state.year < balance.WIN_EXPEDITION_EARLIEST_YEAR:
            resources.fame += 2
            resources.silver += 3
            self.state.current_story = "The coast is mapped, but the saga-winning voyage must wait for Year 3."
            self.state.log(f"{self.state.turn_label}: {self.state.current_story}")
            self.check_win_loss()
            return

        rng = self.rng()
        roll = rng.randint(0, 6)
        self.commit_rng(rng)
        if score + roll >= balance.EXPEDITION_BASE_TARGET:
            self.end_game(True, "victory")
        else:
            resources.ships = max(0, resources.ships - 1)
            resources.warriors = max(0, resources.warriors - 1)
            resources.morale -= 12
            resources.clamp()
            self.end_game(False, "expedition_failed")

    def check_win_loss(self) -> bool:
        resources = self.state.resources
        if resources.population <= 0:
            self.end_game(False, "population_lost")
        elif self.state.season == "Winter" and resources.food <= 0:
            self.end_game(False, "winter_starvation")
        elif resources.morale <= 0:
            self.end_game(False, "morale_lost")
        elif self.state.weak_event_chain >= balance.WEAKNESS_EVENT_LIMIT:
            self.end_game(False, "weakness_chain")
        return self.state.game_over

    def end_game(self, victory: bool, ending_id: str) -> None:
        self.state.game_over = True
        self.state.victory = victory
        self.state.ending_id = ending_id
        self.state.current_story = ENDING_TEXT[ending_id]
        self.state.log(self.state.current_story)

    def get_visible_state(self) -> dict[str, Any]:
        return {
            "title": "Saga Settlement: The First Winter",
            "turn": self.state.turn_label,
            "actions_remaining": max(0, balance.ACTIONS_PER_TURN - self.state.actions_taken_this_turn),
            "resources": self.state.resources.as_dict(),
            "story": self.state.current_story,
            "log": list(self.state.village_log[-60:]),
            "actions": self.available_actions(),
            "can_end_turn": self.can_end_turn(),
            "game_over": self.state.game_over,
            "victory": self.state.victory,
            "shipyard_built": self.state.shipyard_built,
            "huts": self.state.huts,
            "tools": self.state.tools,
        }
