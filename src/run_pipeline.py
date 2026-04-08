from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_step(label: str, command: list[str]) -> None:
    print(f"[run] {label}: {' '.join(command)}", flush=True)
    subprocess.run(command, check=True, cwd=PROJECT_ROOT)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the full Statistics Estonia probability-scale pipeline."
    )
    parser.add_argument(
        "--skip-fetch",
        action="store_true",
        help="Reuse existing raw files and skip the live API fetch step.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    python = [sys.executable]

    if not args.skip_fetch:
        run_step("fetch", python + ["scripts/stat_ee.py", "fetch"])
    run_step("clean", python + ["src/clean_raw.py"])
    run_step("events", python + ["src/build_events.py"])
    run_step("plot", python + ["src/plot_probability_scale.py"])
    print("[run] pipeline completed", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
