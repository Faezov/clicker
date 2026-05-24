from __future__ import annotations

from collections.abc import Callable

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk

from game.buildings import (
    BUILDINGS,
    BUILDING_BY_KEY,
    can_purchase_building,
    current_cost,
)
from game.expeditions import EXPEDITIONS, can_run_expedition
from game.resources import format_amounts, format_number
from game.state import GameState


def section_heading(title: str) -> Gtk.Label:
    label = Gtk.Label(label=title)
    label.set_xalign(0)
    label.add_css_class("heading")
    return label


class ResourceBar(Gtk.Box):
    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.set_margin_top(12)
        self.set_margin_bottom(12)
        self.set_margin_start(12)
        self.set_margin_end(12)
        self.labels: dict[str, Gtk.Label] = {}

        for key, title in (
            ("wood", "Wood"),
            ("food", "Food"),
            ("iron", "Iron"),
            ("silver", "Silver"),
            ("fame", "Fame"),
            ("population", "Population"),
            ("discovery", "Discovery"),
        ):
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            box.set_hexpand(True)
            title_label = Gtk.Label(label=title)
            title_label.set_xalign(0)
            title_label.add_css_class("caption")
            title_label.add_css_class("dim-label")
            value_label = Gtk.Label(label="0")
            value_label.set_xalign(0)
            value_label.add_css_class("title-4")
            box.append(title_label)
            box.append(value_label)
            self.append(box)
            self.labels[key] = value_label

    def update(self, state: GameState) -> None:
        resources = state.resources
        self.labels["wood"].set_label(format_number(resources.wood))
        self.labels["food"].set_label(format_number(resources.food))
        self.labels["iron"].set_label(format_number(resources.iron))
        self.labels["silver"].set_label(format_number(resources.silver))
        self.labels["fame"].set_label(format_number(resources.fame))
        self.labels["population"].set_label(
            f"{resources.population}/{resources.population_cap}"
        )
        discovery_box = self.labels["discovery"].get_parent()
        if discovery_box is not None:
            discovery_box.set_visible(
                state.expeditions_available() or resources.discovery > 0
            )
        self.labels["discovery"].set_label(format_number(resources.discovery))


class ActionPanel(Gtk.Box):
    def __init__(self, on_action: Callable[[str], None]) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.append(section_heading("Actions"))
        self.buttons: dict[str, Gtk.Button] = {}

        for label, action_name in (
            ("Gather Wood", "gather_wood"),
            ("Fish", "fish"),
            ("Mine Iron", "mine_iron"),
            ("Hold Feast", "hold_feast"),
            ("Recruit Villager", "recruit_villager"),
        ):
            button = Gtk.Button(label=label)
            button.set_hexpand(True)
            button.connect("clicked", lambda _button, name=action_name: on_action(name))
            self.append(button)
            self.buttons[action_name] = button

        saga_button = Gtk.Button(label="Enter the Saga")
        saga_button.set_sensitive(False)
        saga_button.set_visible(False)
        saga_button.connect("clicked", lambda _button: on_action("enter_saga"))
        self.append(saga_button)
        self.buttons["enter_saga"] = saga_button

    def update(self, state: GameState) -> None:
        resources = state.resources
        self.buttons["hold_feast"].set_sensitive(resources.food >= 10)
        self.buttons["recruit_villager"].set_sensitive(
            resources.population < resources.population_cap
            and resources.can_afford({"food": 20, "wood": 5})
        )
        self.buttons["enter_saga"].set_visible(state.can_enter_saga())


class BuildingRow(Gtk.Box):
    def __init__(self, key: str, on_build: Callable[[str], None]) -> None:
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.key = key
        self.set_margin_top(6)
        self.set_margin_bottom(6)

        text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        text_box.set_hexpand(True)

        self.title_label = Gtk.Label()
        self.title_label.set_xalign(0)
        self.title_label.add_css_class("body")
        self.detail_label = Gtk.Label()
        self.detail_label.set_xalign(0)
        self.detail_label.set_wrap(True)
        self.detail_label.add_css_class("caption")
        self.detail_label.add_css_class("dim-label")

        text_box.append(self.title_label)
        text_box.append(self.detail_label)

        self.button = Gtk.Button(label="Build")
        self.button.set_valign(Gtk.Align.CENTER)
        self.button.connect("clicked", lambda _button: on_build(self.key))

        self.append(text_box)
        self.append(self.button)

    def update(self, state: GameState) -> None:
        building = BUILDING_BY_KEY[self.key]
        owned = state.buildings[self.key]
        cost = current_cost(building, owned)
        self.title_label.set_label(f"{building.name}  Owned: {owned}")

        effects: list[str] = [building.description, f"Cost: {format_amounts(cost)}"]
        if building.production:
            effects.append(f"Produces: {format_amounts(building.production)} / sec")
        if building.population_cap_bonus:
            effects.append(f"+{building.population_cap_bonus} population cap")
        if building.requires_population:
            effects.append(f"Requires: {building.requires_population} population")
        if building.unlocks_expeditions:
            effects.append("Unlocks expeditions")
        self.detail_label.set_label(" | ".join(effects))
        self.button.set_sensitive(
            can_purchase_building(state.resources, state.buildings, self.key)
        )


class BuildingsPanel(Gtk.Box):
    def __init__(self, on_build: Callable[[str], None]) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.append(section_heading("Buildings"))
        self.rows = [BuildingRow(building.key, on_build) for building in BUILDINGS]
        for row in self.rows:
            separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
            self.append(row)
            self.append(separator)

    def update(self, state: GameState) -> None:
        for row in self.rows:
            row.update(state)


class ExpeditionRow(Gtk.Box):
    def __init__(self, key: str, on_expedition: Callable[[str], None]) -> None:
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.key = key
        self.set_margin_top(6)
        self.set_margin_bottom(6)

        expedition = next(item for item in EXPEDITIONS if item.key == key)
        text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        text_box.set_hexpand(True)

        self.title_label = Gtk.Label(label=expedition.name)
        self.title_label.set_xalign(0)
        self.detail_label = Gtk.Label()
        self.detail_label.set_xalign(0)
        self.detail_label.set_wrap(True)
        self.detail_label.add_css_class("caption")
        self.detail_label.add_css_class("dim-label")

        text_box.append(self.title_label)
        text_box.append(self.detail_label)

        self.button = Gtk.Button(label="Send")
        self.button.set_valign(Gtk.Align.CENTER)
        self.button.connect("clicked", lambda _button: on_expedition(self.key))

        self.append(text_box)
        self.append(self.button)

    def update(self, state: GameState, unlocked: bool) -> None:
        expedition = next(item for item in EXPEDITIONS if item.key == self.key)
        self.detail_label.set_label(
            " | ".join(
                (
                    expedition.description,
                    f"Cost: {format_amounts(expedition.cost)}",
                    f"Requires: {expedition.requires_population} population",
                )
            )
        )
        self.button.set_sensitive(
            unlocked and can_run_expedition(state.resources, state.buildings, self.key)
        )


class ExpeditionsPanel(Gtk.Box):
    def __init__(self, on_expedition: Callable[[str], None]) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.append(section_heading("Expeditions"))
        self.locked_label = Gtk.Label(label="Build a Shipyard to open the sea-road.")
        self.locked_label.set_xalign(0)
        self.locked_label.add_css_class("dim-label")
        self.append(self.locked_label)

        self.rows = [
            ExpeditionRow(expedition.key, on_expedition) for expedition in EXPEDITIONS
        ]
        for row in self.rows:
            separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
            self.append(row)
            self.append(separator)

    def update(self, state: GameState) -> None:
        unlocked = state.expeditions_available()
        self.locked_label.set_visible(not unlocked)
        for row in self.rows:
            row.update(state, unlocked)


class EventLogPanel(Gtk.Box):
    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.append(section_heading("Event Log"))

        self.list_box = Gtk.ListBox()
        self.list_box.add_css_class("boxed-list")
        self.list_box.set_selection_mode(Gtk.SelectionMode.NONE)

        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroller.set_vexpand(True)
        scroller.set_child(self.list_box)
        self.append(scroller)

    def update(self, state: GameState) -> None:
        child = self.list_box.get_first_child()
        while child is not None:
            next_child = child.get_next_sibling()
            self.list_box.remove(child)
            child = next_child

        for message in state.event_log[-80:]:
            label = Gtk.Label(label=message)
            label.set_xalign(0)
            label.set_wrap(True)
            label.set_margin_top(6)
            label.set_margin_bottom(6)
            label.set_margin_start(8)
            label.set_margin_end(8)
            self.list_box.append(label)
