from __future__ import annotations

from random import Random
from typing import cast

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gio, GLib, Gtk

from game.save import default_save_path, load_game, save_game
from game.state import GameState
from ui.widgets import ActionPanel, BuildingsPanel, EventLogPanel, ExpeditionsPanel, ResourceBar


APP_ID = "io.github.sagasettlement.SagaSettlement"
AUTOSAVE_SECONDS = 10


class SagaSettlementWindow(Adw.ApplicationWindow):
    def __init__(self, application: Adw.Application) -> None:
        super().__init__(application=application, title="Saga Settlement")
        self.set_default_size(1100, 720)

        self.state = self.load_initial_state()
        self.rng = Random()
        self.save_path = default_save_path()
        self._tick_id = 0
        self._autosave_id = 0

        self.toast_overlay = Adw.ToastOverlay()
        self.resource_bar = ResourceBar()
        self.action_panel = ActionPanel(self.handle_action)
        self.buildings_panel = BuildingsPanel(self.handle_building)
        self.expeditions_panel = ExpeditionsPanel(self.handle_expedition)
        self.event_log_panel = EventLogPanel()

        self.set_content(self.build_layout())
        self.connect("close-request", self.handle_close_request)
        self.refresh()
        self.start_timers()

    def build_layout(self) -> Adw.ToolbarView:
        toolbar_view = Adw.ToolbarView()
        header = Adw.HeaderBar()

        save_button = Gtk.Button(label="Save")
        save_button.connect("clicked", lambda _button: self.save_now())
        load_button = Gtk.Button(label="Load")
        load_button.connect("clicked", lambda _button: self.load_now())
        header.pack_end(load_button)
        header.pack_end(save_button)
        toolbar_view.add_top_bar(header)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        root.append(self.resource_bar)

        content = Gtk.Grid(column_spacing=12, row_spacing=12)
        content.set_margin_start(12)
        content.set_margin_end(12)
        content.set_margin_bottom(12)
        content.set_hexpand(True)
        content.set_vexpand(True)

        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        left.set_size_request(270, -1)
        left.append(self.action_panel)
        left.append(self.expeditions_panel)

        buildings_scroller = Gtk.ScrolledWindow()
        buildings_scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        buildings_scroller.set_hexpand(True)
        buildings_scroller.set_vexpand(True)
        buildings_scroller.set_child(self.buildings_panel)

        log_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        log_box.set_size_request(320, -1)
        log_box.set_vexpand(True)
        log_box.append(self.event_log_panel)

        content.attach(left, 0, 0, 1, 1)
        content.attach(buildings_scroller, 1, 0, 1, 1)
        content.attach(log_box, 2, 0, 1, 1)

        root.append(content)
        self.toast_overlay.set_child(root)
        toolbar_view.set_content(self.toast_overlay)
        return toolbar_view

    def load_initial_state(self) -> GameState:
        try:
            return load_game()
        except (OSError, ValueError) as exc:
            state = GameState.new_game()
            state.log(f"Could not load the previous save: {exc}")
            return state

    def start_timers(self) -> None:
        self._tick_id = GLib.timeout_add_seconds(1, self.on_tick)
        self._autosave_id = GLib.timeout_add_seconds(AUTOSAVE_SECONDS, self.on_autosave)

    def on_tick(self) -> bool:
        self.state.tick(1.0)
        self.refresh()
        return GLib.SOURCE_CONTINUE

    def on_autosave(self) -> bool:
        self.save_now(show_toast=False)
        return GLib.SOURCE_CONTINUE

    def handle_action(self, action_name: str) -> None:
        method = getattr(self.state, action_name)
        method()
        self.refresh()

    def handle_building(self, key: str) -> None:
        self.state.buy_building(key)
        self.refresh()

    def handle_expedition(self, key: str) -> None:
        self.state.run_expedition(key, self.rng)
        self.refresh()

    def save_now(self, show_toast: bool = True) -> None:
        try:
            self.save_path = save_game(self.state, self.save_path)
        except OSError as exc:
            self.show_toast(f"Save failed: {exc}")
            return
        if show_toast:
            self.show_toast(f"Saved to {self.save_path}")

    def load_now(self) -> None:
        try:
            self.state = load_game(self.save_path)
        except (OSError, ValueError) as exc:
            self.show_toast(f"Load failed: {exc}")
            return
        self.refresh()
        self.show_toast(f"Loaded from {self.save_path}")

    def refresh(self) -> None:
        self.resource_bar.update(self.state)
        self.action_panel.update(self.state)
        self.buildings_panel.update(self.state)
        self.expeditions_panel.update(self.state)
        self.event_log_panel.update(self.state)

    def show_toast(self, message: str) -> None:
        self.toast_overlay.add_toast(Adw.Toast.new(message))

    def handle_close_request(self, _window: Gtk.Window) -> bool:
        if self._tick_id:
            GLib.source_remove(self._tick_id)
            self._tick_id = 0
        if self._autosave_id:
            GLib.source_remove(self._autosave_id)
            self._autosave_id = 0
        self.save_now(show_toast=False)
        return False


class SagaSettlementApplication(Adw.Application):
    def __init__(self) -> None:
        super().__init__(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )

    def do_activate(self) -> None:
        window = self.props.active_window
        if window is None:
            window = SagaSettlementWindow(self)
        cast(SagaSettlementWindow, window).present()


def main(argv: list[str] | None = None) -> int:
    app = SagaSettlementApplication()
    return app.run(argv)
