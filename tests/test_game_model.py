from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from random import Random

from game.buildings import current_cost, BUILDING_BY_KEY
from game.save import load_game, save_game
from game.state import GameState
from game.tick import OFFLINE_PROGRESS_CAP_SECONDS, offline_seconds_since


class GameModelTests(unittest.TestCase):
    def test_manual_actions_and_recruitment_constraints(self) -> None:
        state = GameState.new_game()

        state.gather_wood()
        state.fish()
        state.mine_iron()

        self.assertEqual(state.resources.wood, 1)
        self.assertEqual(state.resources.food, 1)
        self.assertEqual(state.resources.iron, 1)
        self.assertFalse(state.hold_feast())

        state.resources.food = 10
        self.assertTrue(state.hold_feast())
        self.assertEqual(state.resources.food, 0)
        self.assertEqual(state.resources.fame, 3)

        state.resources.food = 100
        state.resources.wood = 100
        state.resources.population = state.resources.population_cap
        self.assertFalse(state.recruit_villager())

        state.resources.population_cap += 1
        self.assertTrue(state.recruit_villager())
        self.assertEqual(state.resources.population, 6)
        self.assertEqual(state.resources.food, 80)
        self.assertEqual(state.resources.wood, 95)

    def test_building_purchase_cost_scaling_and_population_cap(self) -> None:
        state = GameState()
        state.resources.wood = 100
        state.resources.food = 100

        self.assertTrue(state.buy_building("hut"))
        self.assertEqual(state.buildings["hut"], 1)
        self.assertEqual(state.resources.wood, 85)
        self.assertEqual(state.resources.food, 95)
        self.assertEqual(state.resources.population_cap, 7)

        next_hut_cost = current_cost(BUILDING_BY_KEY["hut"], 1)
        self.assertEqual(next_hut_cost, {"wood": 18, "food": 6})

        state.resources.wood = 500
        state.resources.iron = 500
        self.assertFalse(state.buy_building("forge"))
        state.resources.population = 3
        self.assertTrue(state.buy_building("forge"))
        self.assertEqual(state.buildings["forge"], 1)

    def test_buildings_produce_resources_over_time(self) -> None:
        state = GameState()
        state.buildings["fishing_pier"] = 2
        state.buildings["lumber_camp"] = 1
        state.buildings["forge"] = 1

        gained = state.tick(10)

        self.assertAlmostEqual(gained["food"], 5.0)
        self.assertAlmostEqual(gained["wood"], 2.0)
        self.assertAlmostEqual(gained["iron"], 1.0)
        self.assertAlmostEqual(state.resources.food, 5.0)
        self.assertAlmostEqual(state.resources.wood, 2.0)
        self.assertAlmostEqual(state.resources.iron, 1.0)

    def test_expedition_success_and_population_loss_are_seeded(self) -> None:
        state = GameState()
        state.buildings["shipyard"] = 1
        state.resources.population = 4
        state.resources.food = 100
        state.resources.wood = 100
        state.resources.iron = 100

        self.assertTrue(state.run_expedition("local_trade", Random(1)))
        self.assertEqual(state.resources.silver, 10)
        self.assertEqual(state.resources.food, 96)
        self.assertEqual(state.resources.wood, 96)

        self.assertTrue(state.run_expedition("coastal_raid", Random(2)))
        self.assertEqual(state.resources.population, 3)
        self.assertEqual(state.resources.silver, 22)
        self.assertEqual(state.resources.fame, 4)
        self.assertEqual(state.resources.iron, 98)

    def test_save_load_round_trip_and_missing_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "save.json"
            state = GameState.new_game()
            state.resources.wood = 7
            state.buildings["hut"] = 2
            state.log("A test message.")

            save_game(state, path)
            raw = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(raw["schema_version"], 1)

            loaded = load_game(path, apply_offline=False)
            self.assertEqual(loaded.resources.wood, 7)
            self.assertEqual(loaded.buildings["hut"], 2)
            self.assertIn("A test message.", loaded.event_log)

            minimal_path = Path(temp_dir) / "minimal.json"
            minimal_path.write_text(
                json.dumps({"schema_version": 1, "resources": {"wood": 5}}),
                encoding="utf-8",
            )
            minimal = load_game(minimal_path, apply_offline=False)
            self.assertEqual(minimal.resources.wood, 5)
            self.assertEqual(minimal.resources.population, 2)
            self.assertEqual(minimal.resources.population_cap, 5)

    def test_offline_progress_and_cap(self) -> None:
        now = datetime(2026, 5, 24, 12, 0, tzinfo=timezone.utc)
        state = GameState()
        state.buildings["lumber_camp"] = 1
        state.last_saved_at = (now - timedelta(hours=1)).isoformat()

        seconds, gained = state.apply_offline(now)

        self.assertEqual(seconds, 3600)
        self.assertAlmostEqual(gained["wood"], 720.0)
        self.assertAlmostEqual(state.resources.wood, 720.0)
        self.assertEqual(state.last_saved_at, now.isoformat())

        capped_seconds = offline_seconds_since(
            (now - timedelta(days=3)).isoformat(), now
        )
        self.assertEqual(capped_seconds, OFFLINE_PROGRESS_CAP_SECONDS)


if __name__ == "__main__":
    unittest.main()

