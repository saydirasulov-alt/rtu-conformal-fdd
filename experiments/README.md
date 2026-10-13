# Phase experiments (E1-E6)
Pre-registered plan: ANALYSIS_PLAN_PHASE1.md (+ addendum). Findings: PHASE1_REPORT.md.
Run everything (about 20 s on a laptop CPU; no GPU needed):
- Linux/macOS: `RTU_DATA_DIR=/path/to/data python experiments/run_phase_all.py`
- Windows PowerShell: `$env:RTU_DATA_DIR="D:\path\to\data"; python experiments\run_phase_all.py`
Outputs: experiments/results/*.json and SUMMARY.json (sha256 of each output). Extra dependency: scikit-learn, scipy.
E6 runs only when $RTU_DATA_DIR/Independent/manifest.json exists.
