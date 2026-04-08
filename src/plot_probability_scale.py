from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter

from src.common import read_csv_rows

EVENTS_PATH = PROJECT_ROOT / "data" / "processed" / "events.csv"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

CATEGORY_COLORS = {
    "births": "#2A6F97",
    "population": "#6D9F71",
    "mortality": "#B56576",
    "marriages": "#E09F3E",
    "migration": "#6C5B7B",
    "traffic": "#3D405B",
}

ESTIMATE_MARKERS = {
    "exact_probability": "o",
    "annual_probability": "s",
    "rate_equivalent": "D",
}

ESTIMATE_LABELS = {
    "exact_probability": "Exact probability",
    "annual_probability": "Annual probability",
    "rate_equivalent": "Rate-equivalent",
}


def probability_tick_formatter(value: float, _pos: int) -> str:
    if value >= 0.01:
        return f"{value * 100:.0f}%"
    if value >= 0.001:
        return f"{value * 100:.1f}%"
    return f"{value * 100:.2f}%"


def build_plot(events_path: Path = EVENTS_PATH, output_dir: Path = OUTPUT_DIR) -> tuple[Path, Path]:
    rows = read_csv_rows(events_path)
    if not rows:
        raise ValueError("Events file is empty.")

    rows.sort(key=lambda row: float(row["probability"]), reverse=True)
    probabilities = [float(row["probability"]) for row in rows]
    labels = [row["event_label"] for row in rows]
    y_positions = list(range(len(rows), 0, -1))

    min_probability = min(probabilities)
    max_probability = max(probabilities)
    x_min = 10 ** math.floor(math.log10(min_probability / 2.0))
    x_max = min(1.0, 10 ** math.ceil(math.log10(max_probability * 1.5)))

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "axes.facecolor": "#FAF7F0",
            "figure.facecolor": "#FAF7F0",
            "axes.edgecolor": "#2F2F2F",
        }
    )

    fig, ax = plt.subplots(figsize=(15.5, 9))

    for row, y in zip(rows, y_positions, strict=False):
        probability = float(row["probability"])
        color = CATEGORY_COLORS.get(row["category"], "#2F2F2F")
        marker = ESTIMATE_MARKERS.get(row["estimate_type"], "o")
        ax.hlines(y, x_min, probability, color=color, alpha=0.25, linewidth=2)
        ax.scatter(
            probability,
            y,
            s=120,
            color=color,
            marker=marker,
            edgecolors="#FAF7F0",
            linewidth=1.5,
            zorder=3,
        )
        percent_label = f"{probability * 100:.2f}%"
        odds_label = f"1 in {row['odds_1_in']}"
        ax.text(
            probability * 1.12,
            y,
            f"{percent_label}  |  {odds_label}",
            va="center",
            ha="left",
            fontsize=10,
            color="#2F2F2F",
        )

    ax.set_xscale("log")
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(0.5, len(rows) + 0.8)
    ax.set_yticks(y_positions)
    ax.set_yticklabels(labels, fontsize=11)
    for tick, row in zip(ax.get_yticklabels(), rows, strict=False):
        tick.set_color(CATEGORY_COLORS.get(row["category"], "#2F2F2F"))
    ax.xaxis.set_major_formatter(FuncFormatter(probability_tick_formatter))
    ax.grid(axis="x", which="major", color="#2F2F2F", alpha=0.15, linewidth=1)
    ax.grid(axis="x", which="minor", color="#2F2F2F", alpha=0.06, linewidth=0.6)
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("Probability or annual rate-equivalent", fontsize=11, color="#2F2F2F")
    ax.set_title("Probability Scale of Selected Events in Estonia", fontsize=22, loc="left", color="#2F2F2F", pad=22)

    fig.text(
        0.125,
        0.93,
        "2024 event estimates from Statistics Estonia. Colors show topic; marker shapes show estimate type.",
        fontsize=10,
        color="#4F4F4F",
    )

    legend_handles = [
        Line2D(
            [0],
            [0],
            marker=ESTIMATE_MARKERS[key],
            color="#2F2F2F",
            markerfacecolor="#2F2F2F",
            markersize=7,
            linewidth=0,
            label=label,
        )
        for key, label in ESTIMATE_LABELS.items()
    ]
    ax.legend(
        handles=legend_handles,
        loc="lower right",
        frameon=False,
        fontsize=9,
        title="Estimate type",
        title_fontsize=9,
    )

    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)

    output_dir.mkdir(parents=True, exist_ok=True)
    svg_path = output_dir / "probability_scale.svg"
    png_path = output_dir / "probability_scale.png"
    fig.tight_layout(rect=(0.08, 0.06, 0.98, 0.91))
    fig.savefig(svg_path, bbox_inches="tight")
    fig.savefig(png_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return svg_path, png_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a log-scale probability chart from events.csv.")
    parser.add_argument(
        "--events",
        default=str(EVENTS_PATH),
        help="Path to data/processed/events.csv",
    )
    parser.add_argument(
        "--output-dir",
        default=str(OUTPUT_DIR),
        help="Directory where SVG and PNG outputs should be written.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    svg_path, png_path = build_plot(Path(args.events), Path(args.output_dir))
    print(f"[plot] saved {svg_path}")
    print(f"[plot] saved {png_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
