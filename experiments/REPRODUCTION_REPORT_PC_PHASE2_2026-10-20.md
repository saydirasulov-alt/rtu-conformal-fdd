# Second-computer reproduction of the full v1.1.0 analysis (2026-10-20)

**Machine.** Windows PC (`pc-lab`), Miniconda Python 3.12, NumPy 2.4.6, pandas 3.0.3, SciPy 1.18.0,
scikit-learn 1.9.0, matplotlib 3.11.0, CoolProp 8.0.0.
**Reference.** Linux cloud VM, Python 3.13.16, NumPy 2.5.3, pandas 3.0.5, SciPy 1.18.1, scikit-learn 1.9.1.
**Code.** Branch `exp/phase2` at commit 15102a9, transferred as a git bundle.
**Data.** LBNL FDD datasets in a local folder.

**Commands, in order:**
1. `algo_v2_develop.py`
2. `algo_v2_evaluate.py`
3. `run_phase_all.py` (E1–E6)
4. `run_phase2_all.py` (E13, E7/E8, E9, E9b, E10, E10b, E11, E12, E14, E12b, E10c, E15, E15b, E15c)

Phase 2 took about 4 minutes in total.

## Outcome
Every count, rate, p-value and selected configuration is identical. `git diff` over `experiments/results`
changed five files:

| File | Difference | Assessment |
|---|---|---|
| `SUMMARY.json` | Run times | Expected |
| `e7_e8_paired_operational.json` | Machine name, Python version, timing | Expected |
| `e1_baselines.json` | Threshold values differ at about the 13th significant digit (e.g. 916.394605834419 vs 916.3946058344283) | Floating-point (BLAS) noise; all day/minute counts and percentages identical |
| `e10b_ridge_sweep.json` | The two numerically zero eigenvalues (about 1e-16) of the joint covariance | Floating-point noise; non-zero eigenvalues and all counts identical |
| `algo_v2_EVALUATION.json` | Adds `best_dev_mean_sens_unconstrained: 91.7` to the embedded frozen config | **The committed file was stale.** It had been generated before commit 52a21ec added that key to `algo_v2_FROZEN.json`. It was regenerated on the reference machine as well (identical to the PC output) and committed. |

Consequence for `RESULTS_SHA256.txt`: checksums are exact only on the reference platform. On another
platform `e1_baselines.json` and `e10b_ridge_sweep.json` can differ in floating-point digits without
any difference in a reported result. On Windows, every file can also differ in line endings.
