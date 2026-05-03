from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.common import format_odds_label, format_probability, parse_int, read_csv_rows, write_csv_rows

CLEAN_DIR = PROJECT_ROOT / "data" / "processed" / "clean"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "events.csv"

EVENT_COLUMNS = [
    "event_id",
    "event_label",
    "category",
    "estimate_type",
    "year",
    "numerator",
    "denominator",
    "probability",
    "odds_1_in",
    "notes",
]


@dataclass(frozen=True)
class Event:
    """One row on the probability scale.

    The important part is not the formula. It is being honest about what the
    numerator and denominator actually mean.
    """

    event_id: str
    label: str
    category: str
    estimate_type: str
    numerator: int
    denominator: int
    year: int
    notes: str

    def as_row(self) -> dict[str, object]:
        probability = self.numerator / self.denominator
        return {
            "event_id": self.event_id,
            "event_label": self.label,
            "category": self.category,
            "estimate_type": self.estimate_type,
            "year": self.year,
            "numerator": self.numerator,
            "denominator": self.denominator,
            "probability": format_probability(probability),
            "odds_1_in": format_odds_label(1 / probability),
            "notes": self.notes,
        }


def matching_rows(rows: list[dict[str, str]], **criteria: object) -> list[dict[str, str]]:
    expected = {key: str(value) for key, value in criteria.items()}
    return [
        row
        for row in rows
        if all(str(row.get(key, "")) == value for key, value in expected.items())
    ]


def latest_common_year(*year_sets: set[int]) -> int:
    common = set.intersection(*year_sets)
    if not common:
        raise ValueError("No overlapping year across required datasets.")
    return max(common)


def years(rows: list[dict[str, str]], **criteria: object) -> set[int]:
    return {int(row["year"]) for row in matching_rows(rows, **criteria)}


def single_value(rows: list[dict[str, str]], value_field: str, **criteria: object) -> int:
    matches = matching_rows(rows, **criteria)
    if len(matches) != 1:
        raise ValueError(
            f"Expected exactly one row for {criteria}, found {len(matches)}."
        )
    return parse_int(matches[0][value_field])


def population_value(
    rows: list[dict[str, str]],
    *,
    year: int,
    sex: str = "total",
    place: str = "whole_country",
    age_group: str = "total",
) -> int:
    return single_value(
        rows,
        "population",
        year=year,
        sex=sex,
        place=place,
        age_group=age_group,
    )


def births_value(
    rows: list[dict[str, str]],
    *,
    year: int,
    sex: str,
    birth_weight: str = "total",
) -> int:
    return single_value(
        rows,
        "births",
        year=year,
        birth_weight=birth_weight,
        sex=sex,
    )


def deaths_value(
    rows: list[dict[str, str]],
    *,
    year: int,
    county: str = "whole_country",
    age_group: str = "total",
) -> int:
    return single_value(
        rows,
        "deaths",
        year=year,
        county=county,
        age_group=age_group,
    )


def marriages_value(
    rows: list[dict[str, str]],
    *,
    year: int,
    sex: str,
    age_group: str,
    marriage_type: str = "all_marriages",
) -> int:
    return single_value(
        rows,
        "marriages",
        year=year,
        sex=sex,
        marriage_type=marriage_type,
        age_group=age_group,
    )


def migration_value(
    rows: list[dict[str, str]],
    *,
    year: int,
    metric: str,
    age_group: str,
    sex: str = "total",
    migration_type: str = "external_migration",
) -> int:
    return single_value(
        rows,
        "value",
        year=year,
        sex=sex,
        age_group=age_group,
        migration_type=migration_type,
        metric=metric,
    )


def traffic_value(
    rows: list[dict[str, str]],
    *,
    year: int,
    indicator: str,
    month: str = "total",
) -> int:
    return single_value(
        rows,
        "value",
        year=year,
        indicator=indicator,
        month=month,
    )


def build_events(clean_dir: Path = CLEAN_DIR, output_path: Path = OUTPUT_PATH) -> Path:
    population = read_csv_rows(clean_dir / "rv0282u_population.csv")
    births = read_csv_rows(clean_dir / "rv19_births.csv")
    marriages = read_csv_rows(clean_dir / "rv271_marriages.csv")
    deaths = read_csv_rows(clean_dir / "rv59u_deaths.csv")
    migration = read_csv_rows(clean_dir / "rvr03_migration.csv")
    traffic = read_csv_rows(clean_dir / "ts093_traffic.csv")

    analysis_year = latest_common_year(
        years(births, birth_weight="total", sex="total"),
        years(population, sex="total", place="whole_country", age_group="total"),
        years(population, sex="total", place="harju_county", age_group="total"),
        years(deaths, county="whole_country", age_group="total"),
        years(marriages, sex="male", marriage_type="all_marriages", age_group="30-34"),
        years(
            migration,
            sex="total",
            age_group="20-24",
            migration_type="external_migration",
            metric="immigration",
        ),
        years(traffic, indicator="persons_injured", month="total"),
    )

    reference_population = population_value(population, year=analysis_year)

    # This list is deliberately hand-picked. A larger automatic catalogue would
    # be less useful if the reader cannot trust the meaning of each denominator.
    event_rows = [
        Event(
            event_id="birth_male",
            label="A birth is male",
            category="births",
            estimate_type="exact_probability",
            year=analysis_year,
            numerator=births_value(births, year=analysis_year, sex="male"),
            denominator=births_value(births, year=analysis_year, sex="total"),
            notes="RV19 male live births divided by all live births.",
        ),
        Event(
            event_id="resident_harju",
            label="A resident lives in Harju county",
            category="population",
            estimate_type="exact_probability",
            year=analysis_year,
            numerator=population_value(population, year=analysis_year, place="harju_county"),
            denominator=reference_population,
            notes="RV0282U Harju county population divided by total population.",
        ),
        Event(
            event_id="death_85_plus",
            label="A resident aged 85+ dies this year",
            category="mortality",
            estimate_type="annual_probability",
            year=analysis_year,
            numerator=deaths_value(deaths, year=analysis_year, age_group="85_plus"),
            denominator=population_value(population, year=analysis_year, age_group="85_plus"),
            notes="Approximation using RV59U annual deaths aged 85+ and same-year RV0282U population stock aged 85+.",
        ),
        Event(
            event_id="marriage_female_25_29",
            label="A woman aged 25-29 gets married this year",
            category="marriages",
            estimate_type="annual_probability",
            year=analysis_year,
            numerator=marriages_value(marriages, year=analysis_year, sex="female", age_group="25-29"),
            denominator=population_value(population, year=analysis_year, sex="female", age_group="25-29"),
            notes="RV271 newly married women divided by same-year RV0282U resident population; an annual rate approximation.",
        ),
        Event(
            event_id="immigration_20_24",
            label="External immigration per resident aged 20-24",
            category="migration",
            estimate_type="rate_equivalent",
            year=analysis_year,
            numerator=migration_value(migration, year=analysis_year, metric="immigration", age_group="20-24"),
            denominator=population_value(population, year=analysis_year, age_group="20-24"),
            notes="RVR03 external immigration divided by the resident population aged 20-24; an inflow rate, not a resident probability.",
        ),
        Event(
            event_id="immigration_25_29",
            label="External immigration per resident aged 25-29",
            category="migration",
            estimate_type="rate_equivalent",
            year=analysis_year,
            numerator=migration_value(migration, year=analysis_year, metric="immigration", age_group="25-29"),
            denominator=population_value(population, year=analysis_year, age_group="25-29"),
            notes="RVR03 external immigration divided by the resident population aged 25-29; an inflow rate, not a resident probability.",
        ),
        Event(
            event_id="marriage_male_30_34",
            label="A man aged 30-34 gets married this year",
            category="marriages",
            estimate_type="annual_probability",
            year=analysis_year,
            numerator=marriages_value(marriages, year=analysis_year, sex="male", age_group="30-34"),
            denominator=population_value(population, year=analysis_year, sex="male", age_group="30-34"),
            notes="RV271 newly married men divided by same-year RV0282U resident population; an annual rate approximation.",
        ),
        Event(
            event_id="emigration_35_39",
            label="A resident aged 35-39 emigrates this year",
            category="migration",
            estimate_type="annual_probability",
            year=analysis_year,
            numerator=migration_value(migration, year=analysis_year, metric="emigration", age_group="35-39"),
            denominator=population_value(population, year=analysis_year, age_group="35-39"),
            notes="External emigration from RVR03 divided by RV0282U population aged 35-39.",
        ),
        Event(
            event_id="death_any",
            label="A resident dies this year",
            category="mortality",
            estimate_type="annual_probability",
            year=analysis_year,
            numerator=deaths_value(deaths, year=analysis_year),
            denominator=reference_population,
            notes="Deaths from RV59U divided by total population from RV0282U.",
        ),
        Event(
            event_id="road_injury_equivalent",
            label="Road injuries per resident per year",
            category="traffic",
            estimate_type="rate_equivalent",
            year=analysis_year,
            numerator=traffic_value(traffic, year=analysis_year, indicator="persons_injured"),
            denominator=reference_population,
            notes="TS093 injured-person count per resident; a rate, not a unique-person probability.",
        ),
        Event(
            event_id="death_20_24",
            label="A resident aged 20-24 dies this year",
            category="mortality",
            estimate_type="annual_probability",
            year=analysis_year,
            numerator=deaths_value(deaths, year=analysis_year, age_group="20-24"),
            denominator=population_value(population, year=analysis_year, age_group="20-24"),
            notes="Approximation using RV59U annual deaths aged 20-24 and same-year RV0282U population stock aged 20-24.",
        ),
        Event(
            event_id="road_death_equivalent",
            label="Road deaths per resident per year",
            category="traffic",
            estimate_type="rate_equivalent",
            year=analysis_year,
            numerator=traffic_value(traffic, year=analysis_year, indicator="persons_killed"),
            denominator=reference_population,
            notes="TS093 road-death count per resident; a rate, not a unique-person probability.",
        ),
    ]

    events = [event.as_row() for event in event_rows]

    write_csv_rows(output_path, EVENT_COLUMNS, events)
    return output_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a tidy event table from cleaned Statistics Estonia data.")
    parser.add_argument(
        "--clean-dir",
        default=str(CLEAN_DIR),
        help="Directory with cleaned CSV files.",
    )
    parser.add_argument(
        "--output",
        default=str(OUTPUT_PATH),
        help="Path for the generated events CSV.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output = build_events(Path(args.clean_dir), Path(args.output))
    print(f"[events] saved {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
