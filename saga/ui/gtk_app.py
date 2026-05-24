from __future__ import annotations

from pathlib import Path
from typing import cast

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gio, Gtk

from saga.core.engine import GameEngine
from saga.core.save import load_game, save_game
from saga.ui.widgets import ActionsPanel, LogPanel, ResourcePanel, StoryPanel


APP_ID = "io.github.sagasettlement.FirstWinter"
DEFAULT_SAVE_PATH = Path.home() / ".local" / "share" / "saga-settlement-first-winter" / "save.json"


class SagaWindow(Adw.ApplicationWindow):
    def __init__(self, application: Adw.Application) -> None:
        super().__init__(application=application, title="Saga Settlement: The First Winter")
        self.set_default_size(1120, 760)
        self.engine = GameEngine(GameEngine.start_new_game())

        self.toast_overlay = Adw.ToastOverlay()
        self.resource_panel = ResourcePanel()
        self.story_panel = StoryPanel()
        self.actions_panel = ActionsPanel(self.on_action)
        self.log_panel = LogPanel()
        self.end_turn_button = Gtk.Button(label="End Turn")
        self.end_turn_button.connect("clicked", lambda _button: self.end_turn())

        self.set_content(self.build_layout())
        self.refresh()

    def build_layout(self) -> Adw.ToolbarView:
        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()

        new_button = Gtk.Button(label="New Game")
        new_button.connect("clicked", lambda _button: self.new_game())
        save_button = Gtk.Button(label="Save Game")
        save_button.connect("clicked", lambda _button: self.save_game())
        load_button = Gtk.Button(label="Load Game")
        load_button.connect("clicked", lambda _button: self.load_game())

        header.pack_start(new_button)
        header.pack_end(load_button)
        header.pack_end(save_button)
        toolbar.add_top_bar(header)

        root = Gtk.Grid(column_spacing=16, row_spacing=16)
        root.set_margin_top(16)
        root.set_margin_bottom(16)
        root.set_margin_start(16)
        root.set_margin_end(16)
        root.set_hexpand(True)
        root.set_vexpand(True)

        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        left.set_size_request(240, -1)
        left.append(self.resource_panel)

        center = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        center.set_hexpand(True)
        center.set_vexpand(True)
        center.append(self.story_panel)
        center.append(self.actions_panel)
        center.append(self.end_turn_button)

        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        right.set_size_request(330, -1)
        right.append(self.log_panel)

        root.attach(left, 0, 0, 1, 1)
        root.attach(center, 1, 0, 1, 1)
        root.attach(right, 2, 0, 1, 1)
        self.toast_overlay.set_child(root)
        toolbar.set_content(self.toast_overlay)
        return toolbar

    def on_action(self, action_id: str) -> None:
        result = self.engine.apply_action(action_id)
        self.refresh()
        if not result.success:
            self.toast_overlay.add_toast(Adw.Toast.new(result.message))

    def end_turn(self) -> None:
        if self.engine.can_end_turn():
            self.engine.end_turn()
            self.refresh()
        else:
            self.toast_overlay.add_toast(
                Adw.Toast.new("Take at least one action before ending the season.")
            )

    def new_game(self) -> None:
        self.engine = GameEngine(GameEngine.start_new_game())
        self.refresh()

    def save_game(self) -> None:
        try:
            save_game(DEFAULT_SAVE_PATH, self.engine.state)
        except OSError as exc:
            self.toast_overlay.add_toast(Adw.Toast.new(f"Save failed: {exc}"))
            return
        self.toast_overlay.add_toast(Adw.Toast.new(f"Saved to {DEFAULT_SAVE_PATH}"))

    def load_game(self) -> None:
        try:
            self.engine = GameEngine(load_game(DEFAULT_SAVE_PATH))
        except (OSError, ValueError) as exc:
            self.toast_overlay.add_toast(Adw.Toast.new(f"Load failed: {exc}"))
            return
        self.refresh()

    def refresh(self) -> None:
        visible = self.engine.get_visible_state()
        self.resource_panel.update(visible["resources"])
        self.story_panel.update(
            visible["turn"],
            visible["actions_remaining"],
            visible["story"],
        )
        self.actions_panel.update(visible["actions"])
        self.log_panel.update(visible["log"])
        self.end_turn_button.set_sensitive(visible["can_end_turn"])


class SagaGtkApplication(Adw.Application):
    def __init__(self) -> None:
        super().__init__(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )

    def do_activate(self) -> None:
        window = self.props.active_window
        if window is None:
            window = SagaWindow(self)
        cast(SagaWindow, window).present()


def run_gtk(argv: list[str] | None = None) -> int:
    return SagaGtkApplication().run(argv)
