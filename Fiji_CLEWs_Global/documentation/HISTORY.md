# Fiji CLEWs Global model history

This is the chronological index. Dated records preserve the wording and paths
used at the time. Use the current documents one level above for the active
model.

| Date | Stage | What happened | Record |
|---|---|---|---|
| Before 24 July 2026 | Initial Fiji country build | CLEWs Global and its pinned submodules were adapted for Fiji geography, crop taxonomy, antimeridian handling, land normalization, and technical workflow corrections | `history/raw_build/PATCH_NOTES_2026-07-24.md`; `../config/upstream_versions.json` |
| 24 July 2026 | Raw de-calibrated rebuild | Earlier capacity scaling, historical generation locks, hydro availability adjustment, and fitted crop-yield factors were removed; the model was rebuilt and solved without added historical forcing | `history/raw_build/MODEL_CARD_2026-07-24.md`; `../diagnostics/no_forcing_audit.json` |
| 24 July 2026 | Raw MUIO import | The raw model was imported, time-slice references were repaired, input/result parity was assessed, and an annual reserve-capacity proxy was installed because native reserve tags are unsupported | `history/raw_build/MUIO_IMPORT_2026-07-24.md`; `../muio/` |
| 24 July 2026 | Raw calibration assessment | The executable but historically weak case was classified Not assessable, with a preliminary Unacceptable-band score and explicit evidence gaps | `../diagnostics/calibration_assessment/2026-07-24_raw/scorecard.md` |
| 25 July 2026 | Provenance reorganization | The package and active-case navigation adopted the Philippines v12 source/assumption/calculation/model-map structure; current guidance was separated from dated evidence; immutable source and MUIO backups were created; no numerical model input or active parameter JSON was changed | `MOVED_FILES.md`; `../backups/`; `../../WebAPP/DataStorage/Fiji_CLEWs_Global/README.md` |
| 25 July 2026 | Calibration protocol established | A 2020–2022 calibration and 2023–2024 held-out validation boundary was documented, along with endogenous/exogenous/history-fixed classifications | `CALIBRATION_PROTOCOL.md` |

## Current versus historical

The active model remains the raw, uncalibrated `Fiji_CLEWs_Global` case. The
historical raw build and MUIO import records are still authoritative evidence
for how that case was produced, even when their internal relative paths show
the earlier folder layout.

No calibrated Fiji release exists yet. Future stages must be added here with
dated build, evidence, parameter-change, solver, and validation records.
