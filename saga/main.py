from __future__ import annotations

import argparse

from saga.ui.cli import run_cli
from saga.ui.gtk_app import run_gtk


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="saga-settlement",
        description="Saga Settlement: The First Winter",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--cli", action="store_true", help="Run the command-line UI.")
    mode.add_argument("--gtk", action="store_true", help="Run the GTK desktop UI.")
    parser.add_argument("--seed", type=int, default=8675309, help="Seed for new CLI games.")
    args = parser.parse_args(argv)

    if args.cli:
        return run_cli(args.seed)
    return run_gtk()


if __name__ == "__main__":
    raise SystemExit(main())
