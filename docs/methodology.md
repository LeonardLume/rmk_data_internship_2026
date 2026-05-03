# Methodology

The output is a probability scale: selected Estonian events placed on one
logarithmic axis. The point of the chart is not to make a perfect risk model.
It is to give the reader anchors such as "about one in 2", "about one in 30",
and "about one in 20,000".

## Execution Flow

1. `scripts/stat_ee.py fetch` downloads metadata, builds API payloads and saves
   raw CSV files.
2. `src/clean_raw.py` converts source-specific tables into tidy CSV files.
3. `src/build_events.py` joins numerators to denominators and creates
   `data/processed/events.csv`.
4. `src/plot_probability_scale.py` renders the chart to `outputs/`.

## Event Types

`exact_probability` means the numerator and denominator come from the same
finite population. Example: male births divided by all live births.

`annual_probability` means an annual count is divided by a relevant population
denominator. Example: deaths aged 85+ divided by population aged 85+.

`rate_equivalent` means the result is useful on a probability scale but should
not be read as a strict unique-person probability. Example: road-accident
injuries per resident.

## Denominator Choices

The project uses the latest year that is common to all selected sources. This
avoids mixing, for example, 2025 births with 2024 deaths or population.

For age-specific events, the denominator is the matching age group from
`RV0282U`. For sex-specific marriage events, the denominator also matches sex.

## Bayesian Note

The chart reports observed proportions because the challenge is about public
intuition, not forecasting. A Bayesian extension would be natural for rare
events: with a Jeffreys prior, the posterior mean for a binomial event is
`(count + 0.5) / (population + 1)`. For road deaths in the committed 2024 data,
that adjustment barely moves the estimate, but it would be useful if the scale
were expanded to very small county-age cells.

## What I Would Improve Next

I would add confidence or credible intervals for the annual probabilities, but
only after checking which source counts can safely be interpreted as individual
events. I would also add one environmental dataset from the Estonian Data Portal
to make the story less demographic.

