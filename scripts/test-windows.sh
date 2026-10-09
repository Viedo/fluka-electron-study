#!/usr/bin/env bash
# Test the Windows-to-WSL argument boundary with a fake wsl.exe, no Linux needed.
set -euo pipefail
project_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
test_root=$(mktemp -d "$project_root/scratch/windows-test-XXXXXXXX")
fixture="$test_root/project with spaces"
mkdir -p "$fixture/scripts" "$fixture/cases" "$fixture/config" "$fixture/runs" "$test_root/fake bin"
cp "$project_root/scripts/fluka.sh" "$project_root/scripts/prepare-run.sh" "$fixture/scripts/"
cp -R "$project_root/cases/smoke_test" "$fixture/cases/"
cat > "$test_root/fake bin/wsl.exe" <<'MOCK'
#!/usr/bin/env bash
set -euo pipefail
if [[ ${1:-} == --list ]]; then
    case ${MOCK_WSL_MODE:-ready} in
        absent) printf 'WSL not installed\n' >&2; exit 1 ;;
        empty) exit 0 ;;
        other) printf 'D\0e\0b\0i\0a\0n\0\r\0\n\0' ;;
        *) printf 'U\0b\0u\0n\0t\0u\0\r\0\n\0' ;;
    esac
else
    printf '%s\n' "$@" > "$MOCK_WSL_TRACE"
    [[ ${MSYS_NO_PATHCONV:-} == 1 && ${MSYS2_ARG_CONV_EXCL:-} == '*' ]]
    exit "${MOCK_WSL_EXIT:-0}"
fi
MOCK
chmod +x "$test_root/fake bin/wsl.exe"
export PATH="$test_root/fake bin:$PATH"
export MOCK_WSL_TRACE="$test_root/wsl-arguments.txt"
cli() { bash "$fixture/scripts/fluka.sh" "$@"; }
fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }
expect_failure() {
    if "$@" > "$test_root/last-failure.log" 2>&1; then fail "expected failure: $*"; fi
}
cli help > "$test_root/help.txt"
cli status > "$test_root/status-empty.txt"
expect_failure cli prepare smoke_test 'note with spaces'
cli prepare smoke_test > "$test_root/prepared.txt"
shopt -s nullglob
manifests=("$fixture"/runs/*/manifest.json)
(( ${#manifests[@]} == 1 )) || fail 'prepare did not create exactly one run'
prepared_dir=${manifests[0]%/manifest.json}
run_id=${prepared_dir##*/}
[[ -f $prepared_dir/note.txt ]]
cli status "$run_id" > "$test_root/status-detail.txt"
expect_failure cli run '../escape' 1
expect_failure cli run "$run_id" 0
expect_failure cli run "$run_id" 01
export MOCK_WSL_MODE=absent
expect_failure cli doctor
expect_failure cli run "$run_id"
[[ $(< "$prepared_dir/status.txt") == prepared && ! -e $prepared_dir/.run-lock ]]
export MOCK_WSL_MODE=empty
expect_failure cli doctor
export MOCK_WSL_MODE=other
expect_failure cli run "$run_id"
export MOCK_WSL_MODE=ready
cli doctor > "$test_root/doctor.txt"
mapfile -t args < "$MOCK_WSL_TRACE"
[[ ${args[0]} == --distribution && ${args[1]} == Ubuntu ]]
[[ ${args[2]} == --cd && ${args[3]} == "$(cygpath -w "$fixture")" ]]
[[ ${args[4]} == --exec && ${args[5]} == env && ${args[6]} == bash && ${args[7]} == scripts/check-linux.sh ]]
# Windows editor conventions: UTF-8 BOM + CRLF; explicit Linux path with spaces.
printf '\357\273\277WSL_DISTRO=Ubuntu\r\nFLUKA_BIN=/opt/fluka with spaces/bin\r\n' > "$fixture/config/windows.local.conf"
cli run "$run_id" 3 > "$test_root/run.txt"
mapfile -t args < "$MOCK_WSL_TRACE"
[[ ${#args[@]} == 11 && ${args[6]} == 'FLUKA_BIN=/opt/fluka with spaces/bin' ]]
[[ ${args[7]} == bash && ${args[8]} == scripts/run-fluka.sh && ${args[9]} == "runs/$run_id" && ${args[10]} == 3 ]]
export MOCK_WSL_EXIT=17
set +e
cli run "$run_id" > "$test_root/run-error.txt" 2>&1
exit_code=$?
set -e
[[ $exit_code == 17 ]] || fail 'WSL exit code was lost'
export MOCK_WSL_EXIT=0
# Literal configuration must never be sourced as shell code.
printf 'WSL_DISTRO=\nFLUKA_BIN=/opt/$(touch SHOULD_NOT_EXIST)/bin\n' > "$fixture/config/windows.local.conf"
( cd "$test_root"; cli run "$run_id" > "$test_root/literal.txt" )
[[ ! -e "$test_root/SHOULD_NOT_EXIST" ]]
mapfile -t args < "$MOCK_WSL_TRACE"
[[ ${args[0]} == --cd && ${args[4]} == 'FLUKA_BIN=/opt/$(touch SHOULD_NOT_EXIST)/bin' ]]
printf 'INVALID_KEY=value\n' > "$fixture/config/windows.local.conf"
expect_failure cli doctor
printf 'running\n' > "$prepared_dir/status.txt"
expect_failure cli run "$run_id"
printf 'PASS: Windows dispatcher, UTF-16 WSL list, BOM/CRLF config, literal paths, missing WSL/distro, arguments and exit codes.\n'
printf 'No WSL or FLUKA physics ran. Technical fixtures: %s\n' "$test_root"
