from __future__ import annotations

from pathlib import Path

from saga.core.engine import GameEngine
from saga.core.save import load_game, save_game


def test_save_load_round_trip(tmp_path: Path) -> None:
    engine = GameEngine(GameEngine.start_new_game(seed=77))
    engine.apply_action("gather_wood")
    engine.apply_action("fish_hunt")
    save_path = tmp_path / "save.json"

    save_game(save_path, engine.state)
    loaded = load_game(save_path)

    assert loaded.to_dict() == engine.state.to_dict()

