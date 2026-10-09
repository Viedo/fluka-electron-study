#!/usr/bin/env bash
# Automation contract tests with a fake rfluka, never a physics simulation.
set -euo pipefail
project_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
test_root=$(mktemp -d "$project_root/scratch/workflow-test-XXXXXXXX")
# A space in the fixture path exercises shell quoting.
fixture="$test_root/project with spaces"
mkdir -p "$fixture/scripts" "$fixture/analysis" "$fixture/cases" "$test_root/fake bin"
cp "$project_root/scripts/prepare-run.sh" "$project_root/scripts/run-fluka.sh" "$fixture/scripts/"
cp "$project_root/analysis/merge_fluka_cycles.py" "$project_root/analysis/write_wall_summary.py" "$fixture/analysis/"
cp -R "$project_root/cases/smoke_test" "$fixture/cases/"
mkdir -p "$fixture/cases/smoke_test/auxiliary data"
printf 'TECHNICAL FIXTURE ONLY\n' > "$fixture/cases/smoke_test/auxiliary data/reference table.txt"
cat > "$test_root/fake bin/rfluka" <<'MOCK'
#!/usr/bin/env bash
set -eu
[[ $1 == -N && $2 == 0 && $3 == -M && $5 == input.inp ]]
case ${MOCK_MODE:-success} in
    failure) echo 'MOCK ERROR'; exit 7 ;;
    no_output) echo 'MOCK: no outputs'; exit 0 ;;
    success)
        for (( i=1; i<=$4; i++ )); do
            printf -v name 'input%03d.out' "$i"
            printf 'MOCK OUTPUT - NOT A FLUKA SIMULATION\n' > "$name"
        done
        ;;
esac
MOCK
chmod +x "$test_root/fake bin/rfluka"
export FLUKA_BIN="$test_root/fake bin"
prepare() { bash "$fixture/scripts/prepare-run.sh" smoke_test 'AUTOMATION TEST ONLY'; }
runner() { bash "$fixture/scripts/run-fluka.sh" "$@"; }
expect_failure() {
    if "$@" > "$test_root/last-failure.log" 2>&1; then
        printf 'FAIL: expected failure: %s\n' "$*" >&2
        exit 1
    fi
}
expect_failure bash "$fixture/scripts/prepare-run.sh" '../escape'
expect_failure bash "$fixture/scripts/prepare-run.sh" missing_case
run_a=$(prepare)
run_b=$(prepare)
[[ $run_a != "$run_b" && $(< "$run_a/status.txt") == prepared ]]
cmp "$fixture/cases/smoke_test/input.inp" "$run_a/input/input.inp"
( cd "$run_a"; sha256sum --check --quiet inputs.sha256 )
cmp "$fixture/scripts/prepare-run.sh" "$run_a/tooling/prepare-run.sh"
( cd "$run_a"; sha256sum --check --quiet tooling.sha256 )
expect_failure runner "$run_a" 0
expect_failure runner "$run_a" 01
[[ $(< "$run_a/status.txt") == prepared && ! -e "$run_a/.run-lock" ]]
export FLUKA_BIN="$test_root/no installation"
expect_failure runner "$run_a" 1
[[ $(< "$run_a/status.txt") == prepared && ! -e "$run_a/.run-lock" ]]
export FLUKA_BIN="$test_root/fake bin"
printf '\n* Changed input\n' >> "$run_b/work/input.inp"
expect_failure runner "$run_b" 1
[[ $(< "$run_b/status.txt") == prepared && ! -e "$run_b/.run-lock" ]]
snapshot_run=$(prepare)
printf '\n* Changed snapshot\n' >> "$snapshot_run/input/input.inp"
expect_failure runner "$snapshot_run" 1
[[ $(< "$snapshot_run/status.txt") == prepared && ! -e "$snapshot_run/.run-lock" ]]
# A checksum check alone would miss newly added files in either tree.
for tree in input work; do
    extra_run=$(prepare)
    printf 'UNTRACKED DEPENDENCY\n' > "$extra_run/$tree/auxiliary data/extra table.txt"
    expect_failure runner "$extra_run" 1
    [[ $(< "$extra_run/status.txt") == prepared && ! -e "$extra_run/.run-lock" ]]
    missing_run=$(prepare)
    mv "$missing_run/$tree/auxiliary data/reference table.txt" "$missing_run/removed-reference.txt"
    expect_failure runner "$missing_run" 1
    [[ $(< "$missing_run/status.txt") == prepared && ! -e "$missing_run/.run-lock" ]]
done
tooling_run=$(prepare)
printf '\n# Changed archive\n' >> "$tooling_run/tooling/prepare-run.sh"
expect_failure runner "$tooling_run" 1
[[ $(< "$tooling_run/status.txt") == prepared && ! -e "$tooling_run/.run-lock" ]]
# Git Bash may emulate ln -s with a copy; only count real symlinks here.
link_run=$(prepare)
symlink_check=unavailable
if ln -s input.inp "$link_run/work/linked-input.inp" 2>/dev/null && [[ -L "$link_run/work/linked-input.inp" ]]; then
    expect_failure runner "$link_run" 1
    [[ $(< "$link_run/status.txt") == prepared && ! -e "$link_run/.run-lock" ]]
    symlink_check=passed
fi
# A copied old output must never be accepted as evidence of a fresh run.
old_run=$(prepare)
printf 'OLD OUTPUT\n' > "$old_run/work/input001.out"
expect_failure runner "$old_run" 1
[[ $(< "$old_run/status.txt") == prepared && ! -e "$old_run/.run-lock" ]]
export MOCK_MODE=failure
failure_run=$(prepare)
set +e
runner "$failure_run" 1 > "$test_root/failure.log" 2>&1
code=$?
set -e
[[ $code == 7 && $(< "$failure_run/status.txt") == failed ]]
export MOCK_MODE=no_output
empty_run=$(prepare)
expect_failure runner "$empty_run" 1
[[ $(< "$empty_run/status.txt") == incomplete ]]
export MOCK_MODE=success
runner "$run_a" 2 > "$test_root/success.log" 2>&1
[[ $(< "$run_a/status.txt") == finished_needs_review ]]
[[ -s "$run_a/work/input001.out" && -s "$run_a/work/input002.out" ]]
[[ -s "$run_a/execution.txt" && -f "$run_a/console.log" ]]
cmp "$fixture/scripts/run-fluka.sh" "$run_a/tooling/run-fluka.sh"
grep -F "prepare_run_sha256=$(sha256sum "$run_a/tooling/prepare-run.sh" | cut -d ' ' -f 1)" "$run_a/execution.txt" >/dev/null
grep -F "run_fluka_sha256=$(sha256sum "$run_a/tooling/run-fluka.sh" | cut -d ' ' -f 1)" "$run_a/execution.txt" >/dev/null
before=$(sha256sum "$run_a/work/input001.out")
expect_failure runner "$run_a" 2
[[ $(sha256sum "$run_a/work/input001.out") == "$before" ]]
printf 'PASS: preparation, input/work hashes and completeness, tooling archives, path quoting, invalid inputs, missing installation, stale outputs, runner failures, missing outputs, cycles, no overwrite.\n'
printf 'Real symbolic-link test: %s.\n' "$symlink_check"
printf 'No FLUKA physics ran. Technical fixtures retained at: %s\n' "$test_root"
