# Retained evidence

This folder contains source extracts and calculation evidence, not arbitrary
downloads.

`raw_baseline/` preserves the observations and crop mapping used in the
original raw-build diagnostics. Future folders should be organized by subject
and dated when the source can change, for example:

- `energy/2020_2024/`
- `hydrology/2020_2024/`
- `water/2020_2024/`
- `agriculture/2020_2024/`

Every retained file must be referenced by a source, assumption, calculation,
or model-map record. Copyrighted reports may be represented by a citation,
page/table locator, checksum, and extracted non-copyrightable facts rather
than a copied publication.

The active Phase 1B public-water extract is:

- `water/fiji_water_account_2024_public_supply_2020_2024.csv` — annual
  2020–2024 Water Authority of Fiji surface abstraction, losses, billed/carted
  delivery, `ML -> km3` conversion and abstraction/delivery ratios from the
  Fiji Bureau of Statistics water account.

The active Phase 1C electricity records are:

- `energy/PHASE_1C_PROJECTION_SOURCE_EXTRACTS_2026-07-27.md` — publication
  identities, official links, page/table locators, checksums, extracted facts
  and the full calculation-to-model chain;
- `energy/fiji_energy_account_2024_electricity_boundary_2020_2024.csv` —
  observed sector use and the reconciled gross-grid boundary; and
- `energy/fiji_phase1c_bottom_up_electricity_projection_2020_2050.csv` —
  frozen annual projection components, calculation drivers and comparison
  with the validated Phase 1B accounting control.
