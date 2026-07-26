# Reproducing the uncalibrated Fiji model

## 1. Obtain the pinned source

```bash
git clone --recurse-submodules https://github.com/DeltaE/CLEWs_Global.git
cd CLEWs_Global
git checkout 8df78c66be104e446f84a7dbb0df1c0a4fda4080
git submodule update --init --recursive
```

Exact submodule revisions are recorded in `UPSTREAM.lock`.

## 2. Apply technical corrections and country adaptations

From this handoff directory:

```bash
./scripts/apply_overrides.sh /absolute/path/to/CLEWs_Global
./scripts/fetch_fiji_boundary.sh /absolute/path/to/CLEWs_Global
```

The overrides contain no historical capacity, generation, availability, or
fitted crop-yield calibration.

## 3. Create the environments

```bash
conda env create -f workflow/envs/clews_global.yaml
conda env create -f workflow/submodules/CLEWs_GAEZ/environment.yml
```

The compatibility override pins `setuptools<81` because the pinned
`osemosys_global` package still imports `pkg_resources`.

## 4. Build and solve

Ensure GLPK and CBC are available, then run:

```bash
conda run -n clews-global snakemake -s workflow/snakefile -j 6 --use-conda
```

The OSeMOSYS Global retrieval rules download their public inputs on the first
run. Generated files appear under `results/Fiji/`.

## 5. Validate

Run:

```bash
python3 scripts/validate_model.py
```

Expected CBC status: `Optimal`. The current raw objective is approximately
`-240.33220528`; small solver-version differences are possible.

The validation confirms technical integrity and absence of added historical
forcing. It does not claim historical calibration.
