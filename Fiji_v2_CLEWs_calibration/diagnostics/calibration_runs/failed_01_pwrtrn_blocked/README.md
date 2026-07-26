# Diagnostic failure 01 — structural conduit blocked

The first Fiji v2 diagnostic solve was infeasible:

- solver status: `PrimalInfeasible`;
- reported primal infeasibility: `6.3961781` across 15 constraints;
- cause: the historical power-investment screen incorrectly included
  `PWRTRNFJIXX`;
- resolution: exclude this structural lossless grid conduit while retaining
  the 2020–2024 investment block for all generation technologies.

The raw imported case assigns `PWRTRNFJIXX` 999,999 GW of dummy new capacity
each year. It is an implementation conduit, not historical generation
investment. Blocking it removes the only path from generated electricity
`ELCFJIXX01` to the annual requirement `ELCFJIXX02`.

The corrected `Historical_Backcast` solve is Optimal. The generated 97 MB
failed LP/solution bundle and the final 56 MB LP were moved out of the tracked
package after diagnosis because both are deterministically regenerable. This
record retains the cause and resolution without duplicating large solver
artifacts.
