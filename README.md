# Estonian Probability Scale

RMK data team internship challenge project.

The project builds a probability scale for selected everyday events in Estonia.
It downloads public data from Statistics Estonia, cleans the tables, calculates
probabilities or rate-equivalents, and renders a log-scale chart.

![Probability scale preview](outputs/probability_scale.png)

## Idea

People have intuition for distances, but not for probabilities. This chart gives
anchors such as "about 1 in 2", "about 1 in 30", and "about 1 in 20,000" using
real Estonian data.

Examples in the final table:

- a randomly selected birth is male
- a randomly selected resident lives in Harju county
- a resident aged 85+ dies within one year
- a female aged 25-29 gets married within one year
- annual road-accident deaths per resident

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

Traffic and immigration rows are marked as `rate_equivalent`, because they are
counts divided by population, not strict person-level probabilities.

## Run

```powershell
py -3 -m pip install -r requirements.txt
py -3 src/run_pipeline.py
```

Use local raw files without calling the API:

```powershell
py -3 src/run_pipeline.py --skip-fetch
```

Run tests:

```powershell
py -3 -m unittest discover -v
```

## Main Files

- `data/raw/` - downloaded metadata, API queries and raw CSV files
- `data/processed/events.csv` - final event table
- `outputs/probability_scale.png` - final chart preview
- `src/` - cleaning, calculation and plotting code
- `tests/` - small tests for query building and formatting

## AI Use

AI was used for coding and wording assistance. Event definitions, denominators
and final outputs were manually reviewed.

## License

MIT. See [LICENSE](LICENSE).
