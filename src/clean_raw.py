from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.common import (
    age_group_sort_key,
    canonical_age_group,
    canonical_birth_weight,
    canonical_indicator,
    canonical_marriage_type,
    canonical_migration_type,
    canonical_month,
    canonical_place,
    canonical_sex,
    parse_int,
    place_sort_key,
    read_csv_rows,
    sex_sort_key,
    write_csv_rows,
)

RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "clean"


def clean_population(raw_dir: Path, output_dir: Path) -> Path:
    rows = read_csv_rows(raw_dir / "rv0282u_population_latest.csv")
    cleaned: list[dict[str, object]] = []
    for row in rows:
        sex = canonical_sex(row["Sex"])
        place = canonical_place(row["Place of residence"])
        for header, value in row.items():
            if header in {"Sex", "Place of residence"}:
                continue
            match = re.fullmatch(r"(\d{4}) (.+)", header)
            if not match:
                raise ValueError(f"Unexpected population column: {header}")
            year = int(match.group(1))
            age_group = canonical_age_group(match.group(2))
            cleaned.append(
                {
                    "year": year,
                    "sex": sex,
                    "place": place,
                    "age_group": age_group,
                    "population": parse_int(value),
                }
            )

    cleaned.sort(
        key=lambda row: (
            int(row["year"]),
            sex_sort_key(str(row["sex"])),
            place_sort_key(str(row["place"])),
            age_group_sort_key(str(row["age_group"])),
        )
    )
    path = output_dir / "rv0282u_population.csv"
    write_csv_rows(path, ["year", "sex", "place", "age_group", "population"], cleaned)
    return path


def clean_births(raw_dir: Path, output_dir: Path) -> Path:
    rows = read_csv_rows(raw_dir / "rv19_live_births_latest.csv")
    cleaned: list[dict[str, object]] = []
    for row in rows:
        year = int(row["Year"])
        birth_weight = canonical_birth_weight(row["Child's birth weight, grams"])
        for sex_label, value in row.items():
            if sex_label in {"Year", "Child's birth weight, grams"}:
                continue
            cleaned.append(
                {
                    "year": year,
                    "birth_weight": birth_weight,
                    "sex": canonical_sex(sex_label),
                    "births": parse_int(value),
                }
            )

    cleaned.sort(
        key=lambda row: (
            int(row["year"]),
            str(row["birth_weight"]),
            sex_sort_key(str(row["sex"])),
        )
    )
    path = output_dir / "rv19_births.csv"
    write_csv_rows(path, ["year", "birth_weight", "sex", "births"], cleaned)
    return path


def clean_marriages(raw_dir: Path, output_dir: Path) -> Path:
    rows = read_csv_rows(raw_dir / "rv271_marriages_latest.csv")
    cleaned: list[dict[str, object]] = []
    for row in rows:
        year = int(row["Year"])
        sex = canonical_sex(row["Sex"])
        marriage_type = canonical_marriage_type(row["Type of marriage"])
        for header, value in row.items():
            if header in {"Year", "Sex", "Type of marriage"}:
                continue
            cleaned.append(
                {
                    "year": year,
                    "sex": sex,
                    "marriage_type": marriage_type,
                    "age_group": canonical_age_group(header),
                    "marriages": parse_int(value),
                }
            )

    cleaned.sort(
        key=lambda row: (
            int(row["year"]),
            sex_sort_key(str(row["sex"])),
            str(row["marriage_type"]),
            age_group_sort_key(str(row["age_group"])),
        )
    )
    path = output_dir / "rv271_marriages.csv"
    write_csv_rows(path, ["year", "sex", "marriage_type", "age_group", "marriages"], cleaned)
    return path


def clean_deaths(raw_dir: Path, output_dir: Path) -> Path:
    rows = read_csv_rows(raw_dir / "rv59u_deaths_latest.csv")
    if not rows:
        raise ValueError("Deaths raw file is empty.")
    id_fields = {"Year", "County", "Age group"}
    value_fields = [field for field in rows[0].keys() if field not in id_fields]
    if len(value_fields) != 1:
        raise ValueError(f"Expected a single deaths value column, got: {value_fields}")
    value_field = value_fields[0]

    cleaned: list[dict[str, object]] = []
    for row in rows:
        cleaned.append(
            {
                "year": int(row["Year"]),
                "county": canonical_place(row["County"]),
                "age_group": canonical_age_group(row["Age group"]),
                "deaths": parse_int(row[value_field]),
            }
        )

    cleaned.sort(
        key=lambda row: (
            int(row["year"]),
            place_sort_key(str(row["county"])),
            age_group_sort_key(str(row["age_group"])),
        )
    )
    path = output_dir / "rv59u_deaths.csv"
    write_csv_rows(path, ["year", "county", "age_group", "deaths"], cleaned)
    return path


def _parse_metric_header(header: str) -> tuple[str, str | None]:
    for suffix in ("External migration", "Internal migration"):
        if header.endswith(suffix):
            metric_label = header[: -len(suffix)].strip()
            return canonical_indicator(metric_label), canonical_migration_type(suffix)
    return canonical_indicator(header), None


def clean_migration(raw_dir: Path, output_dir: Path) -> Path:
    rows = read_csv_rows(raw_dir / "rvr03_migration_latest.csv")
    cleaned: list[dict[str, object]] = []
    for row in rows:
        year = int(row["Year"])
        sex = canonical_sex(row["Sex"])
        age_group = canonical_age_group(row["Age group"])
        for header, value in row.items():
            if header in {"Year", "Sex", "Age group"}:
                continue
            metric, migration_type = _parse_metric_header(header)
            cleaned.append(
                {
                    "year": year,
                    "sex": sex,
                    "age_group": age_group,
                    "migration_type": migration_type or "",
                    "metric": metric,
                    "value": parse_int(value),
                }
            )

    cleaned.sort(
        key=lambda row: (
            int(row["year"]),
            sex_sort_key(str(row["sex"])),
            age_group_sort_key(str(row["age_group"])),
            str(row["migration_type"]),
            str(row["metric"]),
        )
    )
    path = output_dir / "rvr03_migration.csv"
    write_csv_rows(
        path,
        ["year", "sex", "age_group", "migration_type", "metric", "value"],
        cleaned,
    )
    return path


def clean_traffic(raw_dir: Path, output_dir: Path) -> Path:
    rows = read_csv_rows(raw_dir / "ts093_traffic_latest.csv")
    cleaned: list[dict[str, object]] = []
    for row in rows:
        indicator = canonical_indicator(row["Indicator"])
        month = canonical_month(row["Month"])
        for header, value in row.items():
            if header in {"Indicator", "Month"}:
                continue
            if not re.fullmatch(r"\d{4}", header):
                raise ValueError(f"Unexpected traffic column: {header}")
            cleaned.append(
                {
                    "year": int(header),
                    "indicator": indicator,
                    "month": month,
                    "value": parse_int(value),
                }
            )

    cleaned.sort(
        key=lambda row: (
            int(row["year"]),
            str(row["indicator"]),
            str(row["month"]),
        )
    )
    path = output_dir / "ts093_traffic.csv"
    write_csv_rows(path, ["year", "indicator", "month", "value"], cleaned)
    return path


def clean_all(raw_dir: Path = RAW_DIR, output_dir: Path = OUTPUT_DIR) -> list[Path]:
    return [
        clean_population(raw_dir, output_dir),
        clean_births(raw_dir, output_dir),
        clean_marriages(raw_dir, output_dir),
        clean_deaths(raw_dir, output_dir),
        clean_migration(raw_dir, output_dir),
        clean_traffic(raw_dir, output_dir),
    ]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Standardize raw Statistics Estonia CSV extracts.")
    parser.add_argument("--raw-dir", default=str(RAW_DIR), help="Directory with raw CSV files.")
    parser.add_argument(
        "--output-dir",
        default=str(OUTPUT_DIR),
        help="Directory where cleaned CSV files should be written.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    paths = clean_all(Path(args.raw_dir), Path(args.output_dir))
    for path in paths:
        print(f"[clean] saved {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
