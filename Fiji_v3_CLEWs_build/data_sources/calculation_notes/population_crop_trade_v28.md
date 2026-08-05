# Fiji v2.8 population-driven crop demand and trade

## Classification

- Initial stock: inherited crop/land capacities only.
- Final demand: resident food plus exports for CRPCAS, CRPYAM, CRPCON,
  CRPOTH and SGCPROCFJI.
- Continuing constraints: population-scaled 2025 import floors and existing
  land/water/technology constraints.
- Benchmark only: 2020-2024 observed crop production.
- Accounting backstops: IMPCRPCAS, IMPCRPYAM, IMPCRPCON, IMPCRPOTH and
  IMPSUGFJI. They are not physical domestic stocks.

No new crop commodity was introduced. Resident food is the 2021-2023 average
availability per resident. Exports are added directly to final demand. Import
technologies supply the existing commodities and are open above their 2025
population-scaled floors. Tourism is excluded.

The exact 2025 crop-equivalent imports are
`{"CAS":0.0,"CON":0.00015758559399999997,"OTH":0.07019173122661765,"SGC":0.11192319706428569,"YAM":0.0}` Mt and exports are
`{"CAS":0.00105234666,"CON":7.094920999999999e-05,"OTH":0.0045967370508235295,"SGC":0.37738315521428567,"YAM":0.00540519508}` Mt. The full 2020-2050
series is in `CALCULATIONS.csv` and the retained snapshot.

Validation passed: 25,930 source checks, 25,935 generated checks, GLPK matrix
check, optimal normal candidate/live CBC solves and an optimal 95% domestic
production-loss diagnostic. Live objective is 4158.92072593;
the change from v2.7 is 0.680179370%.
