# Calculation notes

Put detailed derivations here when a formula cannot be understood and audited
from one row in `../CALCULATIONS.csv`.

Each note should identify:

- the corresponding calculation ID;
- every source and assumption ID;
- the exact input fields and units;
- the transformation and any code used;
- checks, tolerances, and unresolved conflicts;
- the model parameters affected;
- the date and model version in which it became active.

Do not place exploratory work here until it affects an active parameter.
Exploratory extracts belong under `../evidence/` or `../../diagnostics/`.

Active detailed notes:

- `PHASE_1C_BOTTOM_UP_ELECTRICITY.md` — historical sector reconciliation,
  commercial and industrial growth, residential household/appliance stock,
  direct overhead, demand profiles and the aggregate reserve proxy.
