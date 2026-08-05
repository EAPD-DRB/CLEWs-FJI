# Fiji v2.9 population-driven Fisheries demand and trade

## Classification and equation path

- Existing fleet, aquaculture and post-harvest service technologies remain
  physical conversions/stocks.
- FSHCAPHARV, FSHAQHARV and FSHPOSTPRC are mass-balance conversions with
  one-year accounting capacity envelopes.
- IMPFSHFOOD is an accounting import backstop.
- FSHRAW is intermediate; FSHFOOD is final demand.
- 2020 landings and service observations calibrate PJ/Mt coefficients and are
  not activity pins.

`RYC/AAD(FSHFOOD)` enters the annual EBb4 commodity balance. `RYT/TAL` on
IMPFSHFOOD enters AAC3. IAR/OAR coefficients connect useful services, FSHRAW
and FSHFOOD. Import VC enters operating cost and the objective. Existing fixed
Fisheries SAD values are zero, so required fish tonnage pulls services
endogenously.

The 2025 balance is 0.026199853807 Mt resident food
plus 0.005525044390 Mt domestic exports. The retained
import floor is 0.004035732268 Mt. Full annual series
and every HS input are in the ledger calculation output and retained snapshot.

Validation passed: 24,373 source checks, 24,382 generated checks, GLPK at
178,353 rows / 137,090 columns / 743,918 nonzeros, bounded/full candidate CBC,
live CBC and a 95% production-loss diagnostic. Live objective is
4170.87205658; the change from v2.8 is
0.287366157%.

The normal solution chooses zero capture harvest and all domestic raw fish via
aquaculture. This is disclosed as an uncalibrated result caused by missing
feed, water, land, stock and catch constraints—not interpreted as a forecast.
