# Fiji override notes

These files target the source revisions in `UPSTREAM.lock`. They contain
technical corrections and structural Fiji adaptations only.

- `workflow/scripts/clewsy.py`
  - removes Guyana-specific time-slice and acronym assumptions;
  - supports Fiji crop taxonomy proxies and an aggregate other-crops demand;
  - sets all crop-yield factors to the upstream neutral value of one;
  - uses the unmodified OSeMOSYS Global energy values;
  - fixes country cost lookup and stale generated land parameters;
  - makes reruns idempotent through deterministic parameter-index handling; and
  - checks conversion, generation, solve, and result-export process status.
- `workflow/submodules/CLEWs_GAEZ/...`
  - represents Fiji's documented model-domain area;
  - handles Fiji's antimeridian-spanning multipolygon correctly;
  - avoids double-counting proxy crops in the aggregate group;
  - caches immutable rasters; and
  - renders the cluster map continuously across the date line.
- `workflow/submodules/clewsy/clewsy/src/build/clewsy.py`
  - corrects the operation-mode comparison so Fiji's generated mode set is
    retained.
- `workflow/envs/clews_global.yaml`
  - pins `setuptools<81` for compatibility with the pinned
    `osemosys_global`.

Explicitly absent:

- power-capacity scaling;
- historical capacity or generation locks;
- historical availability adjustments;
- fitted crop-yield factors; and
- policy constraints.
