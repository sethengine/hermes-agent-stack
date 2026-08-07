#!/bin/bash
# resume_check.sh — Step 0 of a resumed audit. Reads ONLY disk state
# (AUDIT_PLAN.md + batch files) to report what is DONE vs MISSING.
# Does NOT rely on conversation context. Run from the audit working dir.
set -u
PLAN=AUDIT_PLAN.md
echo "=== AUDIT RESUME CHECK (disk state only) ==="
if [ ! -f "$PLAN" ]; then
  echo "NO $PLAN found. This is a FRESH run — run extract_keys.sh first, then build the plan."
  echo "Missing batch files:"
  for b in batchA_kernel batchB_vm batchC_fs batchC_netcore batchC_misc batchD_cmdline batchD_sysfs batchD_configs recommendations; do
    [ -f "$b.md" ] || echo "  $b.md MISSING"
  done
  exit 0
fi
echo "Plan exists. Status per batch:"
grep -E "^\| [A-Z]" "$PLAN" | while IFS='|' read -r _ batch surface keys status outfile _; do
  batch=$(echo $batch | xargs); outfile=$(echo $outfile | xargs)
  if [ -f "$outfile" ]; then fstat="FILE PRESENT"; else fstat="FILE MISSING"; fi
  echo "  [$status] $batch -> $outfile ($fstat)"
done
echo ""
echo "=== Batch files on disk ==="
ls -1 batch*.md 2>/dev/null || echo "  (none)"
echo ""
echo "=== Next action ==="
NEXT=$(grep -E "^\| [A-Z].*PENDING|IN_PROGRESS" "$PLAN" | head -1 | cut -d'|' -f2 | xargs)
if [ -n "$NEXT" ]; then
  echo "  Continue with batch: $NEXT"
else
  echo "  All batches DONE or none pending. If recommendations.md missing, compile it."
  [ -f recommendations.md ] && echo "  recommendations.md PRESENT" || echo "  recommendations.md MISSING — compile from batch files"
fi
