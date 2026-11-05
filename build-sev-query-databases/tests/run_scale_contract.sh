#!/bin/sh
set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

grep -q '500 MB' "$root/references/scale-contract.md"
grep -q '500_000_000' "$root/references/scale-contract.md"
grep -q 'no fixed row-count target' "$root/references/scale-contract.md"
grep -q 'production_scale' "$root/references/scale-contract.md"
grep -q 'contract_fixture' "$root/references/scale-contract.md"
grep -q 'scale_profile' "$root/references/output-contract.md"
grep -q 'volume' "$root/references/staging-contract.md"
grep -q 'references/scale-contract.md' "$root/SKILL.md"

echo "production-scale schema contract test passed"
