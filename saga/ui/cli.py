from __future__ import annotations

from pathlib import Path

from saga.core.engine import GameEngine
from saga.core.save import load_game, save_game


DEFAULT_SAVE_PATH = Path("saga_save.json")


def print_state(engine: GameEngine) -> None:
    visible = engine.get_visible_state()
    print()
    print(f"== {visible['title']} ==")
    print(f"{visible['turn']} | Actions remaining: {visible['actions_remaining']}")
    print(
        "Resources: "
        + ", ".join(
            f"{name}={value}" for name, value in visible["resources"].items()
        )
    )
    print()
    print(visible["story"])
    print()
    print("Season rules:")
    for rule in visible["season_rules"]:
        print(f" - {rule}")
    print(f" - {visible['expedition_summary']}")
    print()
    print("Random event this season:")
    for event in visible["event_chances"]:
        print(f" - {event['name']}: {event['chance']} chance. {event['effect']}")
    print()
    print("Actions:")
    for index, action in enumerate(visible["actions"], start=1):
        suffix = "" if action.available else f" [locked: {action.unavailable_reason}]"
        print(f"{index}. {action.name}{suffix}")
        print(f"   {action.description}")
        print(f"   Effect: {action.effect_summary}")
    print("e. End Turn   s. Save   l. Load   n. New Game   q. Quit")


def run_cli(seed: int = 8675309) -> int:
    engine = GameEngine(GameEngine.start_new_game(seed))

    while True:
        print_state(engine)
        if engine.state.game_over:
            choice = input("Game over. Choose n for new game or q to quit: ").strip().lower()
        else:
            choice = input("> ").strip().lower()

        if choice == "q":
            return 0
        if choice == "n":
            engine = GameEngine(GameEngine.start_new_game(seed))
            continue
        if choice == "e":
            if engine.can_end_turn():
                engine.end_turn()
            else:
                print("Take at least one action before ending the season.")
            continue
        if choice == "s":
            save_game(DEFAULT_SAVE_PATH, engine.state)
            print(f"Saved to {DEFAULT_SAVE_PATH}")
            continue
        if choice == "l":
            if DEFAULT_SAVE_PATH.exists():
                engine = GameEngine(load_game(DEFAULT_SAVE_PATH))
                print(f"Loaded from {DEFAULT_SAVE_PATH}")
            else:
                print(f"No save found at {DEFAULT_SAVE_PATH}")
            continue

        try:
            action_index = int(choice) - 1
        except ValueError:
            print("Choose an action number, s, l, n, or q.")
            continue

        actions = engine.available_actions()
        if action_index < 0 or action_index >= len(actions):
            print("No such action.")
            continue

        result = engine.apply_action(actions[action_index].id)
        print(result.message)


if __name__ == "__main__":
    raise SystemExit(run_cli())
