#!/usr/bin/env bash
# Read-only checks executed by fluka.cmd doctor inside the chosen WSL distro.
set -euo pipefail
printf 'Linux: %s\n' "$(uname -sr)"
[[ $(uname -s) == Linux ]] || { printf 'ERROR: FLUKA requires Linux/WSL in this project.\n' >&2; exit 1; }
missing=0
for utility in bash sha256sum find sort xargs tee; do
    if command -v "$utility" >/dev/null; then
        printf '%s: OK\n' "$utility"
    else
        printf '%s: MISSING\n' "$utility"
        missing=1
    fi
done
if [[ -n ${FLUKA_BIN:-} ]]; then
    candidate="$FLUKA_BIN/rfluka"
else
    candidate=$(command -v rfluka || true)
fi
if [[ -n $candidate && -x $candidate && -f $candidate ]]; then
    printf 'rfluka: %s\n' "$candidate"
    engine="$(dirname -- "$candidate")/fluka"
    if [[ -x $engine && -f $engine ]]; then
        printf 'fluka: %s\n' "$engine"
    else
        printf 'fluka: missing executable beside rfluka\n'
        missing=1
    fi
else
    printf 'rfluka: MISSING. Install FLUKA or set FLUKA_BIN in config/windows.local.conf.\n'
    missing=1
fi
for optional in flair gfortran; do
    if command -v "$optional" >/dev/null; then
        printf '%s: %s\n' "$optional" "$(command -v "$optional")"
    else
        printf '%s: not found (Flair: geometry GUI; gfortran: custom routines)\n' "$optional"
    fi
done
printf 'No simulation was started. Neutron libraries and physics must be verified after installation.\n'
exit "$missing"
