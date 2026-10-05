#!/bin/bash
set -e
: "${RTU_DATA_DIR:?Set RTU_DATA_DIR to the LBNL data directory first (see README).}"
ROOT="$(cd "$(dirname "$0")" && pwd)"
echo "### PRIMARY (tau_S^day) ###"
for s in site1_split_audit_13day site1_split_audit_19day primary_day_far \
         minute_far_exact sens_consistency ornl_sensor_unavailability; do
  echo "=== $s.py ==="; python "$ROOT/code/$s.py"
done
echo "### SUPPLEMENTARY (tau_S^min) ###"
echo "=== supplementary_minute_detector.py ==="; python "$ROOT/code/supplementary_minute_detector.py"
