from __future__ import annotations

from collections.abc import Callable

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk

from saga.core.actions import Action


RESOURCE_LABELS = {
    "wood": "Wood",
    "food": "Food",
    "iron": "Iron",
    "silver": "Silver",
    "fame": "Fame",
    "population": "Population",
    "morale": "Morale",
    "ships": "Ships",
    "warriors": "Warriors",
    "discovery": "Discovery",
}


class ResourcePanel(Gtk.Box):
    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.labels: dict[str, Gtk.Label] = {}

        heading = Gtk.Label(label="Resources")
        heading.set_xalign(0)
        heading.add_css_class("heading")
        self.append(heading)

        grid = Gtk.Grid(column_spacing=12, row_spacing=4)
        for row, (key, label) in enumerate(RESOURCE_LABELS.items()):
            name_label = Gtk.Label(label=label)
            name_label.set_xalign(0)
            value_label = Gtk.Label(label="0")
            value_label.set_xalign(1)
            grid.attach(name_label, 0, row, 1, 1)
            grid.attach(value_label, 1, row, 1, 1)
            self.labels[key] = value_label
        self.append(grid)

    def update(self, resources: dict[str, int]) -> None:
        for key, label in self.labels.items():
            label.set_label(str(resources[key]))


class StoryPanel(Gtk.Box):
    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.turn_label = Gtk.Label()
        self.turn_label.set_xalign(0)
        self.turn_label.add_css_class("title-3")
        self.story_label = Gtk.Label()
        self.story_label.set_xalign(0)
        self.story_label.set_wrap(True)
        self.story_label.set_vexpand(True)
        self.rules_label = Gtk.Label()
        self.rules_label.set_xalign(0)
        self.rules_label.set_wrap(True)
        self.rules_label.add_css_class("dim-label")
        self.append(self.turn_label)
        self.append(self.story_label)
        self.append(self.rules_label)

    def update(
        self,
        turn: str,
        actions_remaining: int,
        story: str,
        season_rules: list[str],
        expedition_summary: str,
    ) -> None:
        self.turn_label.set_label(f"{turn} | Actions remaining: {actions_remaining}")
        self.story_label.set_label(story)
        rules_text = "\n".join([*season_rules, expedition_summary])
        self.rules_label.set_label(rules_text)


class ActionsPanel(Gtk.Box):
    def __init__(self, on_action: Callable[[str], None]) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.on_action = on_action
        self.buttons: dict[str, Gtk.Button] = {}

        heading = Gtk.Label(label="Actions")
        heading.set_xalign(0)
        heading.add_css_class("heading")
        self.append(heading)

    def update(self, actions: list[Action]) -> None:
        for child in list(iter_children(self)):
            if isinstance(child, Gtk.Button):
                self.remove(child)
        self.buttons.clear()

        for action in actions:
            label = f"{action.name}\n{action.effect_summary}"
            if not action.available and action.unavailable_reason:
                label = f"{action.name} - {action.unavailable_reason}\n{action.effect_summary}"
            button = Gtk.Button(label=label)
            button.set_sensitive(action.available)
            button.set_tooltip_text(action.description)
            button.connect("clicked", lambda _button, action_id=action.id: self.on_action(action_id))
            self.append(button)
            self.buttons[action.id] = button


class LogPanel(Gtk.Box):
    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        heading = Gtk.Label(label="Village Log")
        heading.set_xalign(0)
        heading.add_css_class("heading")
        self.append(heading)

        self.list_box = Gtk.ListBox()
        self.list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.list_box.add_css_class("boxed-list")

        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroller.set_vexpand(True)
        scroller.set_child(self.list_box)
        self.append(scroller)

    def update(self, entries: list[str]) -> None:
        child = self.list_box.get_first_child()
        while child is not None:
            next_child = child.get_next_sibling()
            self.list_box.remove(child)
            child = next_child

        for entry in entries:
            label = Gtk.Label(label=entry)
            label.set_xalign(0)
            label.set_wrap(True)
            label.set_margin_top(6)
            label.set_margin_bottom(6)
            label.set_margin_start(8)
            label.set_margin_end(8)
            self.list_box.append(label)


class EventPanel(Gtk.Box):
    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        heading = Gtk.Label(label="Random Events")
        heading.set_xalign(0)
        heading.add_css_class("heading")
        self.append(heading)

        self.event_label = Gtk.Label()
        self.event_label.set_xalign(0)
        self.event_label.set_wrap(True)
        self.event_label.add_css_class("dim-label")
        self.append(self.event_label)

    def update(self, event_chances: list[dict[str, str]]) -> None:
        lines = [
            f"{event['name']}: {event['chance']} - {event['effect']}"
            for event in event_chances
        ]
        self.event_label.set_label("\n".join(lines))


def iter_children(widget: Gtk.Widget):
    child = widget.get_first_child()
    while child is not None:
        yield child
        child = child.get_next_sibling()
