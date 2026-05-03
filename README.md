# Estonian Probability Scale

RMK data team internship challenge project.

## Result

This project creates a reproducible probability scale for selected events in Estonia using public Statistics Estonia data.

Main output:

- `outputs/probability_scale.png`
- `outputs/probability_scale.svg`
- `data/processed/events.csv`

The scale compares events from about 1 in 2 to about 1 in 20,000.

| Event | Probability | Odds |
|---|---:|---:|
| A birth is male | 50.91% | about 1 in 2 |
| A resident lives in Harju county | 47.02% | about 1 in 2 |
| A resident aged 85+ dies this year | 14.31% | about 1 in 7 |
| Road deaths per resident per year | 0.005% | about 1 in 19,923 |

![Probability scale preview](outputs/probability_scale.png)

## Why this project

Raw probabilities are hard to interpret. A value like `0.00005` does not mean
much by itself. A log-scale probability chart makes common and rare events
comparable on one visual scale.

The project is not only a chart: it demonstrates reproducible data fetching,
metadata-aware API queries, cleaning, transparent assumptions and final
visualization.

## Data

Data is fetched programmatically from the Statistics Estonia API:

`https://andmed.stat.ee/api/v1/en/stat/<TABLE_ID>`

Used tables:

- `RV0282U` - population by age, sex and place of residence
- `RV19` - live births by child's sex
- `RV59U` - deaths by age group
- `RV271` - newly married persons by age group and sex
- `RVR03` - external migration by age group
- `TS093` - road accidents with casualties

The committed data was refreshed on 2026-05-03. The latest common analysis year
across the selected tables is 2024.

## Approach

1. `scripts/stat_ee.py` downloads metadata and raw CSV files.
2. `src/clean_raw.py` cleans labels and reshapes source tables.
3. `src/build_events.py` creates `data/processed/events.csv`.
4. `src/plot_probability_scale.py` renders the chart in `outputs/`.

Use `--skip-fetch` for deterministic local reproduction from committed raw
files.

## Run

### Windows

```powershell
py -3 -m pip install -r requirements.txt
py -3 src/run_pipeline.py --skip-fetch
```

### Linux / macOS

```bash
python3 -m pip install -r requirements.txt
python3 src/run_pipeline.py --skip-fetch
```

Run tests on Windows:

```powershell
py -3 -m unittest discover -v
```

Run tests on Linux / macOS:

```bash
python3 -m unittest discover -v
```

## Assumptions and limitations

Not all rows are the same kind of probability.

- `exact_probability`: a true share within a clearly defined group.
- `annual_probability`: annual event count divided by population. This is an approximation.
- `rate_equivalent`: event count divided by population, but not a strict probability for one person.

For example, traffic injuries are counted as injured persons per resident. This
is useful as a rate, but the same person-level interpretation should not be
overclaimed.

Marriage estimates use newly married persons from Statistics Estonia divided by
the same-year resident population. Mortality estimates use annual deaths and a
same-year population stock. Both are practical annual approximations, not
lifetime risks.

## Output schema

| Column | Meaning |
|---|---|
| `event_id` | Stable machine-readable event name |
| `event_label` | readable event description |
| `category` | Topic group |
| `estimate_type` | How the estimate should be interpreted |
| `year` | Analysis year |
| `numerator` | Event count or subgroup count |
| `denominator` | Reference population/group |
| `probability` | Numerator divided by denominator |
| `odds_1_in` | readable reciprocal of probability |
| `notes` | Source and interpretation notes |

## Main files

- `data/raw/` - downloaded metadata, API queries and raw CSV files
- `data/processed/events.csv` - final event table
- `outputs/probability_scale.png` - PNG preview
- `outputs/probability_scale.svg` - SVG version
- `src/` - cleaning, calculation and plotting code
- `tests/` - unit tests for query building, event logic and formatting

## License

MIT. See [LICENSE](LICENSE).
