# Windows PowerShell equivalent of run_all.sh
$ErrorActionPreference = "Stop"
if (-not $env:RTU_DATA_DIR) { throw "Set RTU_DATA_DIR to the LBNL data directory first (see README)." }
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
function Run($s) {
    Write-Host "=== $s.py ==="
    python (Join-Path $Root "code\$s.py")
    if ($LASTEXITCODE -ne 0) { throw "$s.py failed (exit $LASTEXITCODE)" }
}
Write-Host "### PRIMARY (tau_S^day) ###"
foreach ($s in @("site1_split_audit_13day","site1_split_audit_19day","primary_day_far",
                 "minute_far_exact","sens_consistency","ornl_sensor_unavailability")) { Run $s }
Write-Host "### SUPPLEMENTARY (tau_S^min) ###"
Run "supplementary_minute_detector"
