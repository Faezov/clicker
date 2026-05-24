# Saga Settlement: The First Winter

Text-first Viking village survival and quest game for Ubuntu desktop.

You lead a small shoreline settlement through three years and twelve seasonal turns. Each season allows up to two actions: gather supplies, trade, train warriors, scout the coast, build ships, and eventually launch the coastal expedition that can make the village's first saga.

The game is intentionally not a web app, not an idle/clicker, and not a side-scroller. The pure Python engine powers both the command-line mode and the GTK4/libadwaita desktop UI.

## Requirements

- Python 3.12+
- GTK4 and libadwaita Python bindings

On Ubuntu:

```bash
sudo apt install python3 python3-gi gir1.2-gtk-4.0 gir1.2-adw-1
```

## Run

GTK desktop mode:

```bash
python3 main.py --gtk
```

CLI mode:

```bash
python3 main.py --cli
```

`--gtk` is the default when no mode is specified.

## Tests

Tests are written for pytest:

```bash
python3 -m pytest
```

## Current MVP

- 3 years, 4 seasons per year, 12 total turns
- up to 2 actions per season
- action buttons show exact current effects and lock reasons
- the UI/CLI show seasonal upkeep, random event chances, and event consequences before the turn ends
- deterministic random events using a stored seed and roll count
- JSON save/load
- CLI and GTK interfaces over the same core engine
- win by launching a successful Year 3 coastal expedition
- lose by population collapse, winter starvation, morale collapse, or a weakness spiral

## Limitations

- No artwork, audio, animation, or map
- Balance is first-pass and intentionally readable
- No character system, diplomacy, or multi-stage quest chains yet
- GTK save path is fixed for MVP

## Roadmap

- Add named settlers and faction pressures
- Expand event chains into branching storylets
- Add richer expedition outcomes and partial victories
- Add difficulty presets and better balance telemetry
- Add AppStream metadata and package-ready Snap files

## Snap Placeholder

A minimal `snap/snapcraft.yaml` is included as a future packaging starting point. It is not yet a store-ready package.
