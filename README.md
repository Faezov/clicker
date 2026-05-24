# Saga Settlement

Saga Settlement is a native Python GTK4/libadwaita desktop idle/clicker MVP for Ubuntu. You begin with a small Viking shoreline settlement, gather basic resources by hand, raise buildings, recruit villagers, and unlock expeditions through a Shipyard.

This is a local-only app: no server, no web frontend, no Streamlit, no microtransactions.

## Requirements

- Python 3.12+
- GTK4 and libadwaita Python bindings

On Ubuntu:

```bash
sudo apt install python3 python3-gi gir1.2-gtk-4.0 gir1.2-adw-1
```

## Run

```bash
python3 main.py
```

The game autosaves every 10 seconds and also saves on window close. Use the Save and Load buttons in the header bar for manual control.

## Test

```bash
python3 -m unittest discover -s tests
```

The tests cover production, building purchases, seeded expedition outcomes, save/load, offline progress, manual actions, and recruitment constraints.

## Save Location

The default save path is:

- Snap runtime: `$SNAP_USER_DATA/save.json`
- With XDG data home: `$XDG_DATA_HOME/saga-settlement/save.json`
- Fallback: `~/.local/share/saga-settlement/save.json`

An example save lives at `examples/saga_settlement_example_save.json`.

## Project Layout

- `main.py`: app entrypoint
- `game/`: pure game model, balance data, ticking, expeditions, JSON saves
- `ui/`: GTK4/libadwaita application and widgets
- `tests/`: stdlib unittest coverage
- `examples/`: sample save data

## Packaging Notes

This repo is structured so a future Snap can wrap the Python entrypoint and desktop metadata. It is not yet a store-ready Snap package.

For a future `snap/snapcraft.yaml`, use strict confinement, `base: core24`, and the GNOME extension for the GTK/libadwaita runtime:

```yaml
name: saga-settlement
title: Saga Settlement
version: "0.1.0"
summary: A native Viking village idle game
description: |
  Build a shoreline settlement, gather resources, raise buildings,
  recruit villagers, and send expeditions across the sea-road.
base: core24
grade: devel
confinement: strict

apps:
  saga-settlement:
    command: bin/saga-settlement
    extensions: [gnome]
    desktop: usr/share/applications/io.github.sagasettlement.SagaSettlement.desktop
    common-id: io.github.sagasettlement.SagaSettlement.desktop
```

Canonical's Snapcraft docs for GTK4/GNOME apps recommend `extensions: [gnome]`, AppStream/desktop metadata, and a `common-id`: https://documentation.ubuntu.com/snapcraft/stable/how-to/integrations/craft-a-gtk4-app/

The GNOME extension supports `core22` and `core24` and supplies the desktop runtime setup and common plugs: https://documentation.ubuntu.com/snapcraft/en/latest/reference/extensions/gnome-extension/

Desktop launcher files should follow Snap's desktop file rules: https://snapcraft.io/docs/reference/development/yaml-schemas/the-snap-format/

## Roadmap

- Add timed expeditions with assigned crews and ships.
- Expand discoveries into outposts and trade routes.
- Implement Enter the Saga prestige reset rules.
- Add AppStream metadata, desktop file, icon assets, and a real Snapcraft project.
- Add optional sound and richer writing once the core loop is tuned.

