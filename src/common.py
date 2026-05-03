from __future__ import annotations

import csv
import re
import unicodedata
from pathlib import Path
from typing import Iterable

UTF8_SIG = "utf-8-sig"


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    without_marks = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    simplified = re.sub(r"[^a-z0-9]+", " ", without_marks.casefold())
    return re.sub(r"\s+", " ", simplified).strip()


def slugify(value: str) -> str:
    return normalize_text(value).replace(" ", "_")


def parse_int(value: str) -> int:
    text = str(value).strip().replace(",", "")
    if not text:
        return 0
    return int(text)


def format_probability(value: float, *, digits: int = 6) -> str:
    return f"{value:.{digits}f}".rstrip("0").rstrip(".")


def format_float(value: float, *, digits: int = 2) -> str:
    return f"{value:.{digits}f}".rstrip("0").rstrip(".")


def format_odds_label(value: float) -> str:
    """Turn a reciprocal probability into a label a person would actually read."""

    if value < 3:
        return f"about 1 in {value:.0f}"
    if value < 10:
        rounded = f"{value:.1f}".rstrip("0").rstrip(".")
        return f"about 1 in {rounded}"
    if value < 1000:
        return f"about 1 in {value:.0f}"
    return f"about 1 in {value:,.0f}"


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding=UTF8_SIG, newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv_rows(
    path: Path,
    fieldnames: list[str],
    rows: Iterable[dict[str, object]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


SEX_MAP = {
    "males and females": "total",
    "mehed ja naised": "total",
    "boys and girls": "total",
    "males": "male",
    "mehed": "male",
    "boys": "male",
    "females": "female",
    "naised": "female",
    "girls": "female",
}

PLACE_MAP = {
    "whole country": "whole_country",
    "kogu eesti": "whole_country",
    "harju county": "harju_county",
    "harju maakond": "harju_county",
}

MARRIAGE_TYPE_MAP = {
    "all marriages": "all_marriages",
    "opposite sex marriages": "opposite_sex_marriages",
    "same sex marriages": "same_sex_marriages",
}

MONTH_MAP = {
    "total": "total",
    "months total": "total",
    "ascending total": "total",
}

INDICATOR_MAP = {
    "persons injured": "persons_injured",
    "persons killed": "persons_killed",
    "traffic accidents": "traffic_accidents",
    "traffic accidents with fatalities": "traffic_accidents_with_fatalities",
    "traffic accidents with the participation of drunk drivers": "traffic_accidents_drunk_driver",
    "traffic accidents with fatalities with the participation of drunk drivers": "traffic_accidents_with_fatalities_drunk_driver",
    "immigration": "immigration",
    "emigration": "emigration",
    "net migration": "net_migration",
}

MIGRATION_TYPE_MAP = {
    "external migration": "external_migration",
    "internal migration": "internal_migration",
}

BIRTH_WEIGHT_MAP = {
    "total": "total",
    "birth weight unknown": "unknown",
}


def canonical_sex(label: str) -> str:
    return SEX_MAP.get(normalize_text(label), slugify(label))


def canonical_place(label: str) -> str:
    return PLACE_MAP.get(normalize_text(label), slugify(label))


def canonical_marriage_type(label: str) -> str:
    return MARRIAGE_TYPE_MAP.get(normalize_text(label), slugify(label))


def canonical_month(label: str) -> str:
    return MONTH_MAP.get(normalize_text(label), slugify(label))


def canonical_indicator(label: str) -> str:
    return INDICATOR_MAP.get(normalize_text(label), slugify(label))


def canonical_migration_type(label: str) -> str:
    return MIGRATION_TYPE_MAP.get(normalize_text(label), slugify(label))


def canonical_birth_weight(label: str) -> str:
    if match := re.fullmatch(r"\s*(\d+)\s*-\s*(\d+)\s*", label):
        return f"{match.group(1)}-{match.group(2)}"
    normalized = normalize_text(label)
    if normalized in BIRTH_WEIGHT_MAP:
        return BIRTH_WEIGHT_MAP[normalized]
    if match := re.fullmatch(r"under (\d+)", normalized):
        return f"under_{match.group(1)}"
    if match := re.fullmatch(r"(\d+) and over", normalized):
        return f"{match.group(1)}_plus"
    return slugify(label)


def canonical_age_group(label: str) -> str:
    if match := re.fullmatch(r"\s*(\d+)\s*-\s*(\d+)\s*", label):
        return f"{match.group(1)}-{match.group(2)}"
    normalized = normalize_text(label)
    if normalized in {"total", "age groups total"}:
        return "total"
    if "unknown" in normalized:
        return "unknown"
    if match := re.fullmatch(r"under (\d+)", normalized):
        return f"under_{match.group(1)}"
    if match := re.fullmatch(r"(\d+) and under", normalized):
        return f"under_or_equal_{match.group(1)}"
    if match := re.fullmatch(r"(\d+) and (older|over)", normalized):
        return f"{match.group(1)}_plus"
    return slugify(label)


def age_group_sort_key(value: str) -> tuple[int, int, str]:
    if value == "total":
        return (0, 0, value)
    if match := re.fullmatch(r"under_(\d+)", value):
        return (1, int(match.group(1)), value)
    if match := re.fullmatch(r"under_or_equal_(\d+)", value):
        return (2, int(match.group(1)), value)
    if match := re.fullmatch(r"(\d+)-(\d+)", value):
        return (3, int(match.group(1)), value)
    if match := re.fullmatch(r"(\d+)_plus", value):
        return (4, int(match.group(1)), value)
    if value == "unknown":
        return (5, 0, value)
    return (6, 0, value)


def sex_sort_key(value: str) -> int:
    return {"total": 0, "male": 1, "female": 2}.get(value, 9)


def place_sort_key(value: str) -> int:
    return {"whole_country": 0, "harju_county": 1}.get(value, 9)
