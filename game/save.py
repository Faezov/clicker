from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from game.state import GameState


SCHEMA_VERSION = 1


def default_save_path() -> Path:
    snap_user_data = os.environ.get("SNAP_USER_DATA")
    if snap_user_data:
        return Path(snap_user_data) / "save.json"

    xdg_data_home = os.environ.get("XDG_DATA_HOME")
    if xdg_data_home:
        return Path(xdg_data_home) / "saga-settlement" / "save.json"

    return Path.home() / ".local" / "share" / "saga-settlement" / "save.json"


def save_game(state: GameState, path: Path | None = None) -> Path:
    path = path or default_save_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    state.mark_saved()
    data = state.to_save_data()
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    temp_path.replace(path)
    return path


def load_game(path: Path | None = None, apply_offline: bool = True) -> GameState:
    path = path or default_save_path()
    if not path.exists():
        return GameState.new_game()

    data = json.loads(path.read_text(encoding="utf-8"))
    validate_save_data(data)
    state = GameState.from_save_data(data)
    if apply_offline:
        state.apply_offline()
    return state


def validate_save_data(data: Any) -> None:
    if not isinstance(data, dict):
        raise ValueError("Save data must be a JSON object.")
    version = int(data.get("schema_version", SCHEMA_VERSION))
    if version != SCHEMA_VERSION:
        raise ValueError(f"Unsupported save schema version: {version}")

