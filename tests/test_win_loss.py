from __future__ import annotations

from saga.core.engine import GameEngine


def test_morale_collapse_loss() -> None:
    engine = GameEngine(GameEngine.start_new_game(seed=1))
    engine.state.resources.morale = 0

    engine.check_win_loss()

    assert engine.state.game_over
    assert engine.state.ending_id == "morale_lost"


def test_population_collapse_loss() -> None:
    engine = GameEngine(GameEngine.start_new_game(seed=1))
    engine.state.resources.population = 0

    engine.check_win_loss()

    assert engine.state.game_over
    assert engine.state.ending_id == "population_lost"


def test_winter_starvation_loss() -> None:
    engine = GameEngine(GameEngine.start_new_game(seed=1))
    engine.state.turn_index = 3
    engine.state.resources.food = 0

    engine.check_win_loss()

    assert engine.state.game_over
    assert engine.state.ending_id == "winter_starvation"


def test_expedition_victory_path() -> None:
    engine = GameEngine(GameEngine.start_new_game(seed=1))
    engine.state.turn_index = 8
    engine.state.resources.food = 50
    engine.state.resources.ships = 1
    engine.state.resources.warriors = 5
    engine.state.resources.morale = 80
    engine.state.resources.fame = 6
    engine.state.resources.discovery = 6

    result = engine.apply_action("launch_expedition")

    assert result.success
    assert engine.state.game_over
    assert engine.state.victory
    assert engine.state.ending_id == "victory"

