from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence
from urllib import error, parse, request

DEFAULT_BASE_URL = "https://andmed.stat.ee/api/v1"
DEFAULT_LANGUAGE = "en"
DEFAULT_FORMAT = "csv"
DEFAULT_TIMEOUT_SECONDS = 60
DEFAULT_RETRY_ATTEMPTS = 4
DEFAULT_RETRY_BACKOFF_SECONDS = 2.0


class ResolutionError(RuntimeError):
    pass


@dataclass(frozen=True)
class DimensionRequest:
    dimension_aliases: tuple[str, ...]
    filter_name: str
    raw_values: tuple[str, ...] = ()
    value_alias_groups: tuple[tuple[str, ...], ...] = ()


@dataclass(frozen=True)
class TableRequest:
    table_id: str
    output_name: str
    description: str
    selections: tuple[DimensionRequest, ...]


def dimension(
    dimension_aliases: Sequence[str],
    filter_name: str,
    *,
    raw_values: Sequence[str] = (),
    value_alias_groups: Sequence[Sequence[str]] = (),
) -> DimensionRequest:
    return DimensionRequest(
        dimension_aliases=tuple(dimension_aliases),
        filter_name=filter_name,
        raw_values=tuple(raw_values),
        value_alias_groups=tuple(tuple(group) for group in value_alias_groups),
    )


CURATED_TABLES: dict[str, TableRequest] = {
    "RV0282U": TableRequest(
        table_id="RV0282U",
        output_name="rv0282u_population_latest.csv",
        description="Population by sex, age group and place of residence.",
        selections=(
            dimension(
                ["Sex", "Gender", "Sugu"],
                "item",
                value_alias_groups=[
                    ["Males and females", "Both sexes", "Total", "Mehed ja naised", "Boys and girls"],
                    ["Males", "Male", "Mehed", "Boys"],
                    ["Females", "Female", "Naised", "Girls"],
                ],
            ),
            dimension(
                ["Place of residence", "County", "Region", "Residence", "Elukoht"],
                "item",
                value_alias_groups=[
                    ["Whole country", "Estonia", "Total", "Kogu Eesti"],
                    ["Harju county", "Harju", "Harju maakond"],
                ],
            ),
            dimension(["Age group", "Age groups", "Age", "Vanuseruhm"], "all", raw_values=["*"]),
            dimension(["Year", "Aasta"], "top", raw_values=["2"]),
        ),
    ),
    "RV19": TableRequest(
        table_id="RV19",
        output_name="rv19_live_births_latest.csv",
        description="Live births by child's sex and birth weight.",
        selections=(
            dimension(["Year", "Aasta"], "top", raw_values=["1"]),
            dimension(
                [
                    "Child's birth weight, grams",
                    "Birth weight, grams",
                    "Birth weight",
                    "Sunnikaal",
                ],
                "item",
                value_alias_groups=[["Total"]],
            ),
            dimension(["Sex", "Gender", "Sugu"], "all", raw_values=["*"]),
        ),
    ),
    "RV59U": TableRequest(
        table_id="RV59U",
        output_name="rv59u_deaths_latest.csv",
        description="Deaths by county, age group, sex and marital status.",
        selections=(
            dimension(["Year", "Aasta"], "top", raw_values=["1"]),
            dimension(
                ["County", "Place of residence", "Region", "Maakond"],
                "item",
                value_alias_groups=[
                    ["Whole country", "Estonia", "Total", "Kogu Eesti"],
                    ["Harju county", "Harju", "Harju maakond"],
                ],
            ),
            dimension(["Age group", "Age groups", "Age", "Vanuseruhm"], "all", raw_values=["*"]),
            dimension(
                ["Sex", "Gender", "Sugu"],
                "item",
                value_alias_groups=[
                    ["Males and females", "Both sexes", "Total", "Mehed ja naised", "Boys and girls"]
                ],
            ),
            dimension(
                ["Marital status", "Marital status of deceased", "Perekonnaseis"],
                "item",
                value_alias_groups=[["Total"]],
            ),
        ),
    ),
    "RV271": TableRequest(
        table_id="RV271",
        output_name="rv271_marriages_latest.csv",
        description="Newly married persons by sex and age group.",
        selections=(
            dimension(["Year", "Aasta"], "top", raw_values=["1"]),
            dimension(
                ["Type of marriage", "Marriage type", "Abielu tuup"],
                "item",
                value_alias_groups=[["All marriages"]],
            ),
            dimension(["Age group", "Age groups", "Age", "Vanuseruhm"], "all", raw_values=["*"]),
            dimension(["Sex", "Gender", "Sugu"], "all", raw_values=["*"]),
        ),
    ),
    "RVR03": TableRequest(
        table_id="RVR03",
        output_name="rvr03_migration_latest.csv",
        description="Migration by sex, age group and type of migration.",
        selections=(
            dimension(["Year", "Aasta"], "top", raw_values=["1"]),
            dimension(["Age group", "Age groups", "Age", "Vanuseruhm"], "all", raw_values=["*"]),
            dimension(
                ["Sex", "Gender", "Sugu"],
                "item",
                value_alias_groups=[
                    ["Males and females", "Both sexes", "Total", "Mehed ja naised", "Boys and girls"]
                ],
            ),
            dimension(["Indicator", "Naitaja"], "all", raw_values=["*"]),
            dimension(
                ["Type of migration", "Migration type", "Migration", "Rande liik"],
                "item",
                value_alias_groups=[["External migration"]],
            ),
        ),
    ),
    "TS093": TableRequest(
        table_id="TS093",
        output_name="ts093_traffic_latest.csv",
        description="Traffic accidents with casualties on the roads.",
        selections=(
            dimension(["Year", "Aasta"], "top", raw_values=["1"]),
            dimension(
                ["Month", "Months", "Kuu"],
                "item",
                value_alias_groups=[["Total", "Months total", "Ascending total"]],
            ),
            dimension(
                ["Indicator", "Naitaja"],
                "item",
                value_alias_groups=[
                    ["Persons injured", "Injured persons"],
                    ["Persons killed", "Killed persons"],
                ],
            ),
        ),
    ),
}

DEFAULT_TABLE_IDS = tuple(CURATED_TABLES.keys())


def normalize_label(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    without_marks = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    simplified = re.sub(r"[^a-z0-9]+", " ", without_marks.casefold())
    return re.sub(r"\s+", " ", simplified).strip()


def _unique_preserving_order(items: Iterable[Any]) -> list[Any]:
    seen: set[int] = set()
    result: list[Any] = []
    for item in items:
        marker = id(item)
        if marker in seen:
            continue
        seen.add(marker)
        result.append(item)
    return result


def _stringify_options(options: Sequence[str], *, limit: int = 12) -> str:
    preview = ", ".join(options[:limit])
    if len(options) > limit:
        preview += ", ..."
    return preview


def _collect_labels(entry: dict[str, Any]) -> tuple[str, ...]:
    labels: list[str] = []
    for key in ("text", "code"):
        raw = str(entry.get(key, "")).strip()
        if raw:
            labels.append(raw)
    return tuple(labels)


def _resolve_single_entry(
    entries: Sequence[dict[str, Any]],
    aliases: Sequence[str],
    *,
    description: str,
) -> dict[str, Any]:
    normalized_aliases = [normalize_label(alias) for alias in aliases if alias]
    exact_matches: list[dict[str, Any]] = []
    contains_matches: list[dict[str, Any]] = []

    for entry in entries:
        labels = _collect_labels(entry)
        normalized_labels = [normalize_label(label) for label in labels]
        if any(alias == label for alias in normalized_aliases for label in normalized_labels):
            exact_matches.append(entry)
            continue
        if any(
            alias and (alias in label or label in alias)
            for alias in normalized_aliases
            for label in normalized_labels
        ):
            contains_matches.append(entry)

    exact_unique = _unique_preserving_order(exact_matches)
    if len(exact_unique) == 1:
        return exact_unique[0]
    if len(exact_unique) > 1:
        options = [labels[0] for labels in (_collect_labels(entry) for entry in exact_unique) if labels]
        raise ResolutionError(
            f"Ambiguous exact match for {description} aliases {aliases!r}: "
            f"{_stringify_options(options)}"
        )

    contains_unique = _unique_preserving_order(contains_matches)
    if len(contains_unique) == 1:
        return contains_unique[0]
    if len(contains_unique) > 1:
        options = [labels[0] for labels in (_collect_labels(entry) for entry in contains_unique) if labels]
        raise ResolutionError(
            f"Ambiguous fuzzy match for {description} aliases {aliases!r}: "
            f"{_stringify_options(options)}"
        )

    available = [labels[0] for labels in (_collect_labels(entry) for entry in entries) if labels]
    raise ResolutionError(
        f"Could not resolve {description} aliases {aliases!r}. "
        f"Available options: {_stringify_options(available)}"
    )


def resolve_variable(metadata: dict[str, Any], aliases: Sequence[str]) -> dict[str, Any]:
    variables = list(metadata.get("variables", []))
    return _resolve_single_entry(variables, aliases, description="variable")


def resolve_value_code(variable: dict[str, Any], aliases: Sequence[str]) -> str:
    values = list(variable.get("values", []))
    value_texts = list(variable.get("valueTexts", []))
    entries = [
        {"code": value_code, "text": value_text}
        for value_code, value_text in zip(values, value_texts, strict=False)
    ]
    if not entries:
        raise ResolutionError(
            f"Variable {variable.get('code')} has no values to resolve."
        )
    match = _resolve_single_entry(
        entries,
        aliases,
        description=f"value for variable {variable.get('code')}",
    )
    return str(match["code"])


def build_query_payload(metadata: dict[str, Any], table_request: TableRequest) -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    resolved_codes: set[str] = set()

    for selection in table_request.selections:
        variable = resolve_variable(metadata, selection.dimension_aliases)
        code = str(variable["code"])
        if code in resolved_codes:
            raise ResolutionError(f"Variable {code} was selected more than once.")

        if selection.filter_name == "item":
            values = [
                resolve_value_code(variable, alias_group)
                for alias_group in selection.value_alias_groups
            ]
        else:
            values = list(selection.raw_values)

        payload.append(
            {
                "code": code,
                "selection": {
                    "filter": selection.filter_name,
                    "values": values,
                },
            }
        )
        resolved_codes.add(code)

    return payload


class StatisticsEstoniaClient:
    def __init__(
        self,
        *,
        base_url: str = DEFAULT_BASE_URL,
        language: str = DEFAULT_LANGUAGE,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        retry_attempts: int = DEFAULT_RETRY_ATTEMPTS,
        retry_backoff_seconds: float = DEFAULT_RETRY_BACKOFF_SECONDS,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.language = language
        self.timeout_seconds = timeout_seconds
        self.retry_attempts = retry_attempts
        self.retry_backoff_seconds = retry_backoff_seconds

    def table_url(self, table_id: str) -> str:
        return f"{self.base_url}/{self.language}/stat/{table_id}"

    def search_url(self, query: str) -> str:
        encoded = parse.quote(query)
        return f"{self.base_url}/{self.language}/stat?query={encoded}"

    def get_json(self, url: str) -> Any:
        raw = self._request("GET", url)
        return json.loads(raw.decode("utf-8"))

    def post(self, url: str, payload: dict[str, Any]) -> bytes:
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Accept": "*/*",
        }
        return self._request("POST", url, body=body, headers=headers)

    def get_table_metadata(self, table_id: str) -> dict[str, Any]:
        return self.get_json(self.table_url(table_id))

    def search_tables(self, query: str) -> list[dict[str, Any]]:
        result = self.get_json(self.search_url(query))
        if not isinstance(result, list):
            raise RuntimeError(f"Unexpected search response for query {query!r}: {result!r}")
        return result

    def fetch_table(
        self,
        table_id: str,
        query_payload: list[dict[str, Any]],
        *,
        response_format: str = DEFAULT_FORMAT,
    ) -> tuple[dict[str, Any], bytes]:
        payload = {
            "query": query_payload,
            "response": {"format": response_format},
        }
        raw = self.post(self.table_url(table_id), payload)
        return payload, raw

    def _request(
        self,
        method: str,
        url: str,
        *,
        body: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> bytes:
        request_headers = {
            "User-Agent": "rmk-stat-ee-fetcher/0.1",
            **(headers or {}),
        }
        req = request.Request(url, data=body, method=method, headers=request_headers)

        for attempt in range(self.retry_attempts + 1):
            try:
                with request.urlopen(req, timeout=self.timeout_seconds) as response:
                    return response.read()
            except error.HTTPError as exc:
                should_retry = exc.code in {429, 500, 502, 503, 504}
                if not should_retry or attempt >= self.retry_attempts:
                    detail = exc.read().decode("utf-8", errors="replace")
                    raise RuntimeError(
                        f"{method} {url} failed with HTTP {exc.code}: {detail}"
                    ) from exc
                delay = self._retry_delay(exc.headers, attempt)
                time.sleep(delay)
            except error.URLError as exc:
                if attempt >= self.retry_attempts:
                    raise RuntimeError(f"{method} {url} failed: {exc}") from exc
                time.sleep(self.retry_backoff_seconds * (2**attempt))

        raise RuntimeError(f"{method} {url} failed after retries.")

    def _retry_delay(self, headers: Any, attempt: int) -> float:
        retry_after = None
        if headers is not None:
            retry_after = headers.get("Retry-After")
        if retry_after:
            try:
                return max(float(retry_after), 0.0)
            except ValueError:
                pass
        return self.retry_backoff_seconds * (2**attempt)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def metadata_path(output_root: Path, table_id: str) -> Path:
    return output_root / "metadata" / f"{table_id}.json"


def query_path(output_root: Path, table_id: str) -> Path:
    return output_root / "queries" / f"{table_id}.json"


def curated_output_path(output_root: Path, table_request: TableRequest, response_format: str) -> Path:
    suffix = response_format.lower()
    if "." not in table_request.output_name:
        return output_root / f"{table_request.output_name}.{suffix}"
    stem = Path(table_request.output_name).stem
    return output_root / f"{stem}.{suffix}"


def dump_metadata(
    client: StatisticsEstoniaClient,
    *,
    table_ids: Sequence[str],
    output_root: Path,
) -> None:
    for table_id in table_ids:
        metadata = client.get_table_metadata(table_id)
        path = metadata_path(output_root, table_id)
        write_json(path, metadata)
        print(f"[metadata] saved {table_id} -> {path}")


def fetch_curated_tables(
    client: StatisticsEstoniaClient,
    *,
    table_ids: Sequence[str],
    output_root: Path,
    response_format: str,
) -> None:
    for table_id in table_ids:
        if table_id not in CURATED_TABLES:
            known = ", ".join(DEFAULT_TABLE_IDS)
            raise SystemExit(
                f"Curated fetch is only available for known tables. "
                f"Unknown table: {table_id}. Known tables: {known}"
            )

        table_request = CURATED_TABLES[table_id]
        metadata = client.get_table_metadata(table_id)
        write_json(metadata_path(output_root, table_id), metadata)

        query_payload = build_query_payload(metadata, table_request)
        full_payload, raw = client.fetch_table(
            table_id,
            query_payload,
            response_format=response_format,
        )

        write_json(query_path(output_root, table_id), full_payload)
        output_path = curated_output_path(output_root, table_request, response_format)
        write_bytes(output_path, raw)

        print(f"[fetch] {table_id} -> {output_path}")


def run_search(client: StatisticsEstoniaClient, *, query_string: str) -> None:
    results = client.search_tables(query_string)
    print(json.dumps(results, ensure_ascii=False, indent=2))


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch metadata and curated raw extracts from the Statistics Estonia PxWeb API."
    )
    parser.add_argument("--language", default=DEFAULT_LANGUAGE, help="API language, for example en or et.")
    parser.add_argument(
        "--output-root",
        default="data/raw",
        help="Directory where metadata, queries and raw responses are saved.",
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help="Base API URL. Defaults to the Statistics Estonia v1 API.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="HTTP timeout in seconds.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    metadata_parser = subparsers.add_parser("metadata", help="Download metadata JSON for one or more tables.")
    metadata_parser.add_argument("table_ids", nargs="*", default=DEFAULT_TABLE_IDS)

    fetch_parser = subparsers.add_parser("fetch", help="Download curated raw extracts for supported tables.")
    fetch_parser.add_argument("table_ids", nargs="*", default=DEFAULT_TABLE_IDS)
    fetch_parser.add_argument(
        "--format",
        default=DEFAULT_FORMAT,
        help="Response format such as csv, json, json-stat2 or xlsx.",
    )

    search_parser = subparsers.add_parser("search", help="Search the statistical database.")
    search_parser.add_argument("query")

    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    client = StatisticsEstoniaClient(
        base_url=args.base_url,
        language=args.language,
        timeout_seconds=args.timeout,
    )
    output_root = Path(args.output_root)

    if args.command == "metadata":
        dump_metadata(client, table_ids=args.table_ids, output_root=output_root)
        return 0

    if args.command == "fetch":
        fetch_curated_tables(
            client,
            table_ids=args.table_ids,
            output_root=output_root,
            response_format=args.format,
        )
        return 0

    if args.command == "search":
        run_search(client, query_string=args.query)
        return 0

    raise SystemExit(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
