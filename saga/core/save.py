from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from saga.core.state import GameState


SCHEMA_VERSION = 1


def save_game(path: str | Path, state: GameState) -> Path:
    save_path = Path(path)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    data = state.to_dict()
    temp_path = save_path.with_suffix(save_path.suffix + ".tmp")
    temp_path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    temp_path.replace(save_path)
    return save_path


def load_game(path: str | Path) -> GameState:
    save_path = Path(path)
    data = json.loads(save_path.read_text(encoding="utf-8"))
    validate_save_data(data)
    return GameState.from_dict(data)


def validate_save_data(data: Any) -> None:
    if not isinstance(data, dict):
        raise ValueError("Save file must contain a JSON object.")
    version = int(data.get("schema_version", SCHEMA_VERSION))
    if version != SCHEMA_VERSION:
        raise ValueError(f"Unsupported save schema version: {version}")

