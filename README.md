# Conformal Fault Detection for Rooftop HVAC Units with Incomplete Sensing — Analysis Code

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23489886.svg)](https://doi.org/10.5281/zenodo.23489886)
v1.1.1 (this manuscript): [10.5281/zenodo.23489886](https://doi.org/10.5281/zenodo.23489886) · all versions: [10.5281/zenodo.23155498](https://doi.org/10.5281/zenodo.23155498)

> **Release v1.1.1 (code for the manuscript "Conformal fault detection for rooftop HVAC units with incomplete sensing").** v1.1.1 = v1.1.0 plus an input-data SHA-256 manifest; no code or result changed. This README describes
> the code and results of the manuscript *"Conformal fault detection for rooftop HVAC units with incomplete
> sensing"*. Versions v1.0.0/v1.0.1 belong to an earlier, single-statistic version of the method; their
> scripts are kept in `code/` and their outputs in `results/` (see the historical section at the end).

## Quick start (v1.1.0 results)
```bash
pip install -r requirements-v1.1.txt
export RTU_DATA_DIR="/path/to/<DATA_DIR>"            # LBNL data, layout below
export RTU_SIM_DIR="/path/to/<DATA_DIR>/Simulated RTU"
python experiments/run_phase_all.py      # E1-E6 (first version, ablations, ORNL, stability)
python experiments/algo_v2_develop.py    # configuration selection on simulated development faults -> algo_v2_FROZEN.json
python experiments/algo_v2_evaluate.py   # single frozen evaluation (simulated holdout, field units)
python experiments/run_phase2_all.py     # all supporting analyses E7-E15 (Phase 2 plan, amendments A1-A10)
python experiments/make_figures_phase2.py
python experiments/make_supplementary_tables.py
(cd experiments && sha256sum -c RESULTS_SHA256.txt)          # compare with the expected outputs
```
Windows PowerShell: replace `export X=...` with `$env:X = "..."`. Phase 2 additionally needs SciPy,
scikit-learn, matplotlib and CoolProp (`requirements-v1.1.txt`).

## Where each manuscript result comes from
| Manuscript item | Script(s) | Result file(s) in `experiments/results/` |
|---|---|---|
| Configuration selection, Supplementary Table S1 | `algo_v2_develop.py` | `algo_v2_dev_grid.json`, `algo_v2_FROZEN.json` |
| Table 2 (simulated faults), frozen field results, Tables S3–S4 | `algo_v2_evaluate.py` | `algo_v2_EVALUATION.json` |
| Table 3, Max column; conventional thresholds; McNemar/Holm; TTFA; Figure 3 | `e1_baselines.py`, `e7_e8_paired_operational.py`, `e13_physics.py` | `e1_baselines.json`, `e7_e8_paired_operational.json`, `e13_physics.json` |
| Table 3, Max+mean column; Figure 4 | `e14_equal_budget.py` (amendments A5, A6) | `e14_equal_budget.json` |
| Attribution (Section 5.3) | `e9_attribution.py` | `e9_attribution.json` |
| Weather check | `e9b_weather_confound.py` (A3) | `e9b_weather_confound.json` |
| Robustness, ridge, Figure 5, Tables S7, S8, S13 | `e10_robustness.py`, `e10b_ridge_sweep.py` (A2), `e10c_ridge_spectrum.py` (A8) | `e10*.json` |
| Table 5 (field sensor loss) | `e11_field_eligibility.py` (A4) | `e11_field_eligibility.json` |
| Table 4, Figure S1, Table S12 (injected sensor faults) | `e12_injection.py`, `e12b_injection_equal_budget.py` (A7) | `e12*.json` |
| Table 7, Section 5.8, Tables S14–S16 | `e15_audit_response.py` (A10), `e15b_alternative_selection.py`, `e15c_minimum_minutes.py` (both not pre-specified) | `e15*.json` |
| Table 6, Table S9 (ORNL) | `code/ornl_sensor_unavailability.py`, `experiments/e4_missingness.py` | `results/ornl_sensor_unavailability.json`, `e4_missingness.json` |
| Table S2 (ablation), Table S11 (Site 1 split audit) | `e3_ablation.py`; `code/site1_split_audit_*.py` | `e3_ablation.json`; `results/site1_split_audit_*.json` |
| Tables S5, S6 (refrigerant identification, physics) | `e13_physics.py` (A1) | `e13_physics.json` |
| Table S10 (post-hoc separability) | `roc_dominance_posthoc.py` | `roc_dominance_POSTHOC.json` |

Analysis plans: `experiments/ALGO_PLAN_V2.md` (selection, Amendment 1) and `experiments/ANALYSIS_PLAN_PHASE2.md`
(supporting analyses and amendments A1–A10, each committed before its results were computed; check the git
history). `e15b_alternative_selection.py` and `e15c_minimum_minutes.py` are the only analyses not covered by a plan and are labelled as such.

**Reproduction status.** The complete analysis (selection, evaluation, E1–E6 and E7–E15) was run on a Linux
reference machine (Python 3.13, NumPy 2.5.3, pandas 3.0.5, SciPy 1.18.1, scikit-learn 1.9.1, CoolProp 8.0.0) and
re-run on a second computer (Windows, Python 3.12) with identical counts, rates, p-values and selected
configuration (`experiments/REPRODUCTION_REPORT_PC_2026-10-14.md`, `experiments/REPRODUCTION_REPORT_PC_PHASE2_2026-10-20.md`). Checksums are exact on the reference machine. On other platforms `e1_baselines.json` and `e10b_ridge_sweep.json` differ in
floating-point digits (thresholds at about the 13th digit, numerically zero eigenvalues), and on Windows line
endings differ, without any change in a reported result. `SUMMARY.json` and `e7_e8_paired_operational.json` contain run times and machine
information and are excluded from the checksum list.

## Input-data provenance
`experiments/DATA_SHA256.txt` lists the SHA-256 of all 81 LBNL input files the analyses read (4 field, 52 ORNL,
25 simulated). Check a local copy before reproducing:
```bash
python experiments/data_manifest.py check   # prints "81 files in manifest; 81 match; ..."
```

## 1. Data
Publicly available **LBNL Fault Detection and Diagnostics Datasets** (DOI: **10.25984/1881324**).
Data are not redistributed here. Download them and arrange as:
```
<DATA_DIR>/
  Field RTU/   Site1_Unfaulted.csv  Site1_Staging_Fault.csv  Site2_Unfaulted.csv  Site2_Undercharged40.csv
  ORNL_RTU/    <ORNL experimental CSV files>
```
Then set `RTU_DATA_DIR` (scripts exit with an error if it is unset):

- Linux / macOS: `export RTU_DATA_DIR="/path/to/<DATA_DIR>"`
- Windows PowerShell: `$env:RTU_DATA_DIR = "D:\path\to\<DATA_DIR>"`

**Compressor-on gate.** Only compressor-on minutes are used: rows with compressor power <= 200 W are
removed first (field: `RTU_COMP_WATT`; ORNL: `RTU_COMP_WATT_1 + RTU_COMP_WATT_2`), then rows with
missing values in the retained channels are dropped. All masking, training, calibration and evaluation
operate on these records. In the ORNL pattern **"no power inputs"** the power channels are withheld from
the diagnostic branches, but compressor power is still used by this gate to select compressor-on minutes.

Simulated RTU files go in `<DATA_DIR>/Simulated RTU/` (`RTU_sim_baseline.csv`, `RTU_sim_<fault>.csv`).


## Environment
Linux / macOS:
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt   # or, for the exact tested versions:
pip install -r requirements-lock.txt
```
Windows PowerShell:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements-lock.txt
```
(If activation is blocked, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first.)

## Historical first version
Scripts in `code/` and results in `results/` belong to the first (single-statistic) version, v1.0.x; their documentation and numbers are in `HISTORY_v1.0.md`.

## License and citation
MIT License (see `LICENSE`). Citation metadata: `CITATION.cff`.
Archived on Zenodo: v1.1.1 = [10.5281/zenodo.23489886](https://doi.org/10.5281/zenodo.23489886); v1.0.0 = [10.5281/zenodo.23155499](https://doi.org/10.5281/zenodo.23155499); all versions = [10.5281/zenodo.23155498](https://doi.org/10.5281/zenodo.23155498).
Later releases receive their own version DOI on Zenodo (use "Cite all versions" there for the concept DOI).

## Changelog
- **v1.0.1** — ORNL pattern labels renamed to `no power inputs` / `none (no diagnostic sensors)`
  (compressor-on gate is applied before masking); `minute_far_exact.py` now processes Site 1 before
  Site 2 so its randomized splits match `primary_day_far.py` (randomized-reference minute exceedance
  changes from 0.004%/0.001% to 0.026%/0.006%; all temporal/primary numbers unchanged); global warning
  suppression removed and result files closed explicitly; Windows instructions and `run_all.ps1` added.
- **v1.0.0** — initial release.
