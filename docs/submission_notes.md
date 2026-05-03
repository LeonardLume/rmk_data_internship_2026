# Submission Notes

This repository is intentionally small. I wanted the reviewer to be able to
find the data source, rerun the pipeline, inspect the event definitions and see
the final chart without digging through a large generated project.

## Design Choices

I used a log-scale lollipop chart because the selected events span several
orders of magnitude. A linear scale would make the rare events visually
invisible.

I kept the frontend surface to a static image. The RMK task text says the data
team does not do much frontend work, so I treated the chart as the deliverable
and the code plus documentation as the real work sample.

The event list is curated rather than exhaustive. I preferred a smaller set of
events with defensible denominators over a bigger list with unclear meanings.

## Known Limitations

The project currently uses official Statistics Estonia tables, not a custom mix
of sources from the Estonian Data Portal. That is a deliberate tradeoff for
programmatic reproducibility and stable metadata.

The chart does not show uncertainty intervals. The next version should add them
for annual probabilities, especially if more sparse subgroups are added.

The event labels are in English. A bilingual version would be more natural for
an Estonian public-facing artifact.

## AI Use

AI assistance was used for implementation support, refactoring and wording.
The data-source choices, event definitions, probability/rate distinction and
final repository structure were reviewed as part of the submission work.

