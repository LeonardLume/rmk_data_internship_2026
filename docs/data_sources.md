# Data Sources

This project uses the public Statistics Estonia statistical database through
the PxWeb-style API at `https://andmed.stat.ee/api/v1`.

The challenge encourages the Estonian Data Portal. I chose Statistics Estonia
for this version because the tables are official, structured, documented by
metadata, and easy to refresh programmatically. That made it possible to spend
more effort on definitions and reproducibility instead of manual data cleaning.

The committed raw layer was refreshed on 2026-05-03. At that point the latest
common year available across the selected tables was 2024.

## Tables Used

| Table | Used for | Human page |
|---|---|---|
| `RV0282U` | population denominators by age, sex and county | `https://andmed.stat.ee/en/stat/rahvastik__rahvastikunaitajad-ja-koosseis__rahvaarv-ja-rahvastiku-koosseis/RV0282U` |
| `RV19` | live births by child's sex | `https://andmed.stat.ee/en/stat/rahvastik__rahvastikusundmused__sunnid/RV19` |
| `RV59U` | deaths by age group and county | `https://andmed.stat.ee/en/stat/rahvastik__rahvastikusundmused__surmad/RV59U` |
| `RV271` | newly married persons by age group and sex | `https://andmed.stat.ee/en/stat/rahvastik__rahvastikusundmused__abielud/RV271` |
| `RVR03` | external migration by age group | `https://andmed.stat.ee/en/stat/RVR03` |
| `TS093` | road accidents with casualties | `https://andmed.stat.ee/en/stat/TS093` |

## Trust And Caveats

Statistics Estonia is the official statistical authority, so the data is a good
fit for an exploratory probability scale. The main risk is not data quality, but
event definition quality: some counts describe people, some describe events,
and some describe rates. The pipeline keeps those estimate types separate.

The source metadata can contain a mix of English labels, Estonian codes and
translated value texts. The fetcher therefore resolves table dimensions by
aliases and saves the exact query payloads under `data/raw/queries/`.

Road-accident injuries and deaths are counts divided by population. They are
useful for intuition, but they are not unique-person probabilities.

Immigration is also shown as an inflow rate. A current resident cannot
"immigrate" into Estonia, so the label says "per resident" rather than "a
resident immigrates".

