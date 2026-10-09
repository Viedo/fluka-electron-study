#!/usr/bin/env bash
# Run a prepared directory under Linux/WSL. No automatic resume or overwrite.
set -euo pipefail
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
if (( $# < 1 || $# > 2 )); then
    die 'Usage: bash scripts/run-fluka.sh RUN_DIRECTORY [CYCLES=1]'
fi
cycles=${2:-1}
[[ $cycles =~ ^[1-9][0-9]{0,2}$ ]] || die 'CYCLES must be an integer from 1 to 999.'
runner_source=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && printf '%s/%s' "$PWD" "${BASH_SOURCE[0]##*/}")
project_root=$(cd -- "$(dirname -- "$runner_source")/.." && pwd -P)
run_dir=$(cd -- "$1" && pwd -P) || die 'Run directory does not exist.'
[[ -f "$run_dir/manifest.json" && -f "$run_dir/input/input.inp" && -f "$run_dir/work/input.inp" && -f "$run_dir/inputs.sha256" && -f "$run_dir/tooling.sha256" ]] || die 'Use the current prepare-run.sh to prepare a new run first.'
[[ -f "$run_dir/status.txt" && $(< "$run_dir/status.txt") == prepared ]] || die 'Run is not prepared. Create a new run; existing results are preserved.'
for tree in input work tooling; do
    [[ -d "$run_dir/$tree" && ! -L "$run_dir/$tree" && -z $(find "$run_dir/$tree" ! -type f ! -type d -print -quit) ]] || die "Unexpected symbolic link or special file in $tree/. Prepare a new run."
done
[[ ! -e "$run_dir/tooling/run-fluka.sh" && ! -e "$run_dir/execution.txt" && ! -e "$run_dir/console.log" ]] || die 'Existing execution records found. Prepare a new run; previous records are preserved.'
shopt -s nullglob
previous_results=("$run_dir"/work/input[0-9][0-9][0-9]* "$run_dir"/work/raninput* "$run_dir"/work/fluka_*)
(( ${#previous_results[@]} == 0 )) || die 'Old FLUKA outputs found in work/. Keep only source inputs in the case and prepare a new run.'
if [[ -n ${FLUKA_BIN:-} ]]; then
    rfluka="$FLUKA_BIN/rfluka"
else
    rfluka=$(command -v rfluka) || die 'rfluka not found. Set FLUKA_BIN to its bin directory or add it to PATH.'
fi
[[ -f $rfluka && -x $rfluka ]] || die "rfluka is not executable: $rfluka"
rfluka=$(cd -- "$(dirname -- "$rfluka")" && printf '%s/rfluka' "$PWD")
command -v sha256sum >/dev/null || die 'sha256sum is required.'
cd -- "$run_dir"
# Rebuild the complete list as well as the hashes: --check alone ignores extra
# files. Check the immutable snapshot and the working copy before rfluka starts.
current_hashes=$(find input work -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum) || die 'Could not read all prepared inputs.'
[[ $current_hashes == "$(< inputs.sha256)" ]] || die 'Prepared input/ or work/ files changed, are missing or were added, or the manifest is obsolete. Edit the case and prepare a new run.'
sha256sum --check --quiet tooling.sha256 || die 'Archived preparation script changed. Prepare a new run.'
# Keep this lock after completion/interruption to prevent accidental reuse.
mkdir .run-lock 2>/dev/null || die 'This directory has already been started or locked.'
state=failed
finish() {
    local rc=$?
    printf '%s\n' "$state" > "$run_dir/status.txt"
    printf 'finished_utc=%s\nexit_code=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$rc" >> "$run_dir/execution.txt"
    if [[ $state == finished_needs_review && -f "$project_root/analysis/write_wall_summary.py" ]] &&
       [[ -s "$run_dir/work/input001_fort.22" || -s "$run_dir/work/input_multicycle_fort.22.trk" ]]; then
        if ! python3 "$project_root/analysis/write_wall_summary.py" "$run_dir"; then
            printf 'failed\n' > "$run_dir/status.txt"
            printf 'summary_status=failed\n' >> "$run_dir/execution.txt"
            printf 'ERROR: FLUKA run completed, but summary generation failed.\n' >&2
        fi
    fi
}
trap finish EXIT
trap 'state=interrupted; exit 130' INT
trap 'state=interrupted; exit 143' TERM
printf 'running\n' > status.txt
cp -- "$runner_source" tooling/run-fluka.sh
{
    printf 'started_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    printf 'rfluka=%s\ncycles=%s\n' "$rfluka" "$cycles"
    printf 'command='; printf '%q ' "$rfluka" -N 0 -M "$cycles" input.inp; printf '\n'
    printf 'system='; uname -a
    printf 'rfluka_sha256='; sha256sum "$rfluka"
    printf 'prepare_run_sha256='; sha256sum tooling/prepare-run.sh
    printf 'run_fluka_sha256='; sha256sum tooling/run-fluka.sh
    if [[ -f $(dirname -- "$rfluka")/fluka ]]; then
        printf 'fluka_sha256='; sha256sum "$(dirname -- "$rfluka")/fluka"
    fi
    printf 'fluka_version=read_from_FLUKA_output_header_after_run\n'
} > execution.txt
cd work
# PIPESTATUS preserves the real runner exit code even though output goes to tee.
set +e
"$rfluka" -N 0 -M "$cycles" input.inp 2>&1 | tee "$run_dir/console.log"
pipe_codes=("${PIPESTATUS[@]}")
set -e
(( pipe_codes[0] == 0 )) || exit "${pipe_codes[0]}"
(( pipe_codes[1] == 0 )) || die 'Could not save console.log.'
for (( cycle=1; cycle<=cycles; cycle++ )); do
    printf -v output_file 'input%03d.out' "$cycle"
    [[ -s $output_file ]] || { state=incomplete; die "Missing or empty $output_file; inspect console.log and work/."; }
done
state=finished_needs_review
if (( cycles > 1 )); then
    command -v python3 >/dev/null || die 'FLUKA finished, but python3 is required to merge cycle statistics.'
    python3 "$project_root/analysis/merge_fluka_cycles.py" "$run_dir" "$cycles" \
        --fluka-bin "$(dirname -- "$rfluka")" || die 'FLUKA finished, but scoring cycle merge failed.'
fi
if [[ -s "$run_dir/work/input001_fort.21" || -s "$run_dir/work/input_multicycle_fort.21.bnn" ]]; then
    command -v python3 >/dev/null || die 'FLUKA finished, but python3 is required to generate and copy EDEP plots.'
    python3 "$project_root/analysis/plot_usrbin.py" "$run_dir" || die 'FLUKA finished, but plot generation or Desktop copy failed.'
else
    printf 'No input001_fort.21 found; EDEP plots were not generated.\n'
fi
if [[ -s "$run_dir/work/input001_fort.22" || -s "$run_dir/work/input_multicycle_fort.22.trk" ]]; then
    command -v python3 >/dev/null || die 'FLUKA finished, but python3 is required to process the photon spectrum.'
    python3 "$project_root/analysis/plot_wall_radiation.py" "$run_dir" || die 'FLUKA finished, but wall-radiation analysis or Desktop copy failed.'
fi
if grep -Eq '^[[:space:]]*USRBIN[[:space:]].*[[:space:]]WATEM[[:space:]]*$' "$run_dir/input/input.inp"; then
    command -v python3 >/dev/null || die 'FLUKA finished, but python3 is required to process water-phantom dose.'
    python3 "$project_root/analysis/plot_water_phantom.py" "$run_dir" || die 'FLUKA finished, but water-phantom analysis or Desktop copy failed.'
fi
printf 'Execution finished. Review all .out/.err/.log files and scoring before using results.\nRun: %s\n' "$run_dir"
