# Data sources, assumptions and calculations

This folder is the main place to answer “where did this number come from?”

- `DATA_SOURCES.md` identifies publications, datasets, software lineages, and
  retained model evidence.
- `ASSUMPTIONS.csv` lists choices made by modellers.
- `CALCULATIONS.csv` records formulas and transformations.
- `MODEL_DATA_MAP.csv` links model entities and parameters to the relevant
  source, assumption, and calculation IDs.
- `calculation_notes/` holds explanations that do not fit in one CSV row.
- `evidence/` holds retained observations, input extracts, and calculation
  evidence.

The ledgers distinguish three roles:

- **Active input**: currently determines a raw model parameter.
- **Diagnostic only**: compared with results but not applied.
- **Calibration candidate**: evidence identified for a later, separately
  versioned calibration.

An empty source field is never meant to imply “common knowledge.” Missing
lineage is labelled as a documentation gap.
