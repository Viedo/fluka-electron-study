#!/usr/bin/env bash
# Preparation only; works in Git Bash and Linux/WSL with standard GNU tools.
set -euo pipefail
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
(( $# >= 1 && $# <= 2 )) || die 'Usage: bash scripts/prepare-run.sh CASE [NOTE]'
case_name=$1
note=${2:-}
[[ $case_name =~ ^[A-Za-z][A-Za-z0-9_]{0,31}$ ]] || die 'Case name: 1-32 ASCII letters, digits or underscores, starting with a letter.'
project_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
case_dir="$project_root/cases/$case_name"
[[ -f "$case_dir/input.inp" ]] || die "Missing $case_dir/input.inp"
[[ ! -L "$case_dir" && -z $(find "$case_dir" ! -type f ! -type d -print -quit) ]] || die 'Case may contain only regular files and directories, not symbolic links or special files.'
mkdir -p -- "$project_root/runs"
run_dir=$(mktemp -d "$project_root/runs/$(date -u +%Y%m%dT%H%M%SZ)_${case_name}_XXXXXXXX")
state=preparation_failed
trap 'printf "%s\n" "$state" > "$run_dir/status.txt"' EXIT
printf 'preparing\n' > "$run_dir/status.txt"
mkdir -- "$run_dir/input" "$run_dir/work" "$run_dir/tooling"
cp -R -- "$case_dir/." "$run_dir/input/"
cp -R -- "$run_dir/input/." "$run_dir/work/"
cp -- "${BASH_SOURCE[0]}" "$run_dir/tooling/prepare-run.sh"
(
    cd -- "$run_dir"
    find input work -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum > inputs.sha256
    sha256sum tooling/prepare-run.sh > tooling.sha256
)
main_hash=$(sha256sum "$run_dir/input/input.inp")
main_hash=${main_hash%% *}
# Free text is a UTF-8 sidecar, avoiding unsafe hand-built JSON escaping.
printf '%s\n' "$note" > "$run_dir/note.txt"
cat > "$run_dir/manifest.json" <<EOF
{
  "schema_version": 2,
  "run_id": "${run_dir##*/}",
  "prepared_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "case_name": "$case_name",
  "source": "cases/$case_name",
  "input_file": "input.inp",
  "input_sha256": "$main_hash",
  "all_file_checksums": "inputs.sha256",
  "preparation_script_checksums": "tooling.sha256",
  "note_file": "note.txt",
  "validation": "not_validated"
}
EOF
state=prepared
printf '%s\n' "$run_dir"
