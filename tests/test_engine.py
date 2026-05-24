from __future__ import annotations

from saga.core.engine import GameEngine


def test_two_actions_auto_end_turn() -> None:
    engine = GameEngine(GameEngine.start_new_game(seed=2))

    first = engine.apply_action("gather_wood")
    second = engine.apply_action("fish_hunt")

    assert first.success
    assert second.success
    assert second.turn_ended
    assert engine.state.turn_index == 1
    assert engine.state.actions_taken_this_turn == 0


def test_manual_end_turn_after_one_action() -> None:
    engine = GameEngine(GameEngine.start_new_game(seed=2))

    engine.apply_action("gather_wood")
    assert engine.can_end_turn()

    engine.end_turn()

    assert engine.state.turn_index == 1
    assert engine.state.actions_taken_this_turn == 0


def test_winter_food_upkeep_is_harsher_than_summer() -> None:
    summer = GameEngine(GameEngine.start_new_game(seed=2))
    winter = GameEngine(GameEngine.start_new_game(seed=2))
    summer.state.turn_index = 1
    winter.state.turn_index = 3

    summer.apply_seasonal_upkeep()
    winter.apply_seasonal_upkeep()

    assert winter.state.resources.food < summer.state.resources.food


def test_visible_state_explains_rules_and_events() -> None:
    engine = GameEngine(GameEngine.start_new_game(seed=2))
    visible = engine.get_visible_state()

    assert any("upkeep" in rule for rule in visible["season_rules"])
    assert visible["event_chances"]
    assert "Expedition score" in visible["expedition_summary"]
