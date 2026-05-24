from __future__ import annotations

from datetime import datetime, timezone
from typing import Mapping

from game.buildings import production_for_buildings
from game.resources import ResourceStock


OFFLINE_PROGRESS_CAP_SECONDS = 24 * 60 * 60


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def apply_production(
    resources: ResourceStock, building_counts: Mapping[str, int], seconds: float
) -> dict[str, float]:
    seconds = max(0.0, float(seconds))
    production_per_second = production_for_buildings(building_counts)
    gained: dict[str, float] = {}
    for resource, amount_per_second in production_per_second.items():
        amount = amount_per_second * seconds
        if amount:
            resources.add(resource, amount)
            gained[resource] = amount
    return gained


def offline_seconds_since(
    last_saved_at: str | None, now: datetime | None = None
) -> float:
    if not last_saved_at:
        return 0.0
    now = now or utc_now()
    try:
        saved = datetime.fromisoformat(last_saved_at)
    except ValueError:
        return 0.0
    if saved.tzinfo is None:
        saved = saved.replace(tzinfo=timezone.utc)
    elapsed = (now - saved).total_seconds()
    return min(max(0.0, elapsed), OFFLINE_PROGRESS_CAP_SECONDS)


def apply_offline_progress(
    resources: ResourceStock,
    building_counts: Mapping[str, int],
    last_saved_at: str | None,
    now: datetime | None = None,
) -> tuple[float, dict[str, float]]:
    seconds = offline_seconds_since(last_saved_at, now)
    gained = apply_production(resources, building_counts, seconds)
    return seconds, gained

