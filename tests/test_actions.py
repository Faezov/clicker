from __future__ import annotations

from saga.core.engine import GameEngine


def action_by_id(engine: GameEngine, action_id: str):
    return next(action for action in engine.available_actions() if action.id == action_id)


def test_gather_wood_changes_resources_and_action_count() -> None:
    engine = GameEngine(GameEngine.start_new_game(seed=1))

    result = engine.apply_action("gather_wood")

    assert result.success
    assert engine.state.resources.wood > 20
    assert engine.state.resources.morale == 48
    assert engine.state.actions_taken_this_turn == 1


def test_unavailable_actions_are_blocked() -> None:
    engine = GameEngine(GameEngine.start_new_game(seed=1))

    build_shipyard = action_by_id(engine, "build_shipyard")
    result = engine.apply_action("build_shipyard")

    assert not build_shipyard.available
    assert build_shipyard.unavailable_reason == "Needs 45 wood."
    assert not result.success
    assert result.message == "Needs 45 wood."


def test_harvest_is_unavailable_in_winter() -> None:
    engine = GameEngine(GameEngine.start_new_game(seed=1))
    engine.state.turn_index = 3

    harvest = action_by_id(engine, "harvest_crops")

    assert harvest.unavailable_reason == "Winter fields yield nothing."


def test_low_morale_reduces_production() -> None:
    normal = GameEngine(GameEngine.start_new_game(seed=1))
    low = GameEngine(GameEngine.start_new_game(seed=1))
    low.state.resources.morale = 10

    normal.apply_action("fish_hunt")
    low.apply_action("fish_hunt")

    assert low.state.resources.food < normal.state.resources.food

