#!/usr/bin/env bash
# Windows command dispatcher. Physical simulations run exclusively in WSL.
set -euo pipefail
project_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
help_text() {
    cat <<'HELP'
Projekt FLUKA - polecenia dla Windows (PowerShell / cmd.exe)

  .\fluka.cmd doctor                    Sprawdz Git Bash, WSL i instalacje FLUKA
  .\fluka.cmd prepare CASE               Przygotuj nowy katalog; bez obliczen
  .\fluka.cmd status [ID]                Wyswietl przebiegi lub szczegoly jednego
  .\fluka.cmd run ID [CYKLE=1]           Uruchom przygotowany przebieg w WSL
  .\fluka.cmd test                      Testy automatyzacji z atrapami programu
  .\fluka.cmd help                      Ta pomoc

Przypadek roboczy: electron_500mev (elektrony w olowiu).
ID jest nazwa katalogu wewnatrz runs/.
Konfiguracja: config/windows.local.conf (opcjonalna; wzor *.example.conf).
Instrukcje: docs/windows.md. Zaden z tych skryptow nie instaluje programow.
HELP
}

# Parse a small data format, never source or evaluate configuration as code.
load_config() {
    WSL_DISTRO=Ubuntu
    fluka_bin=
    local config_file="$project_root/config/windows.local.conf" line key value
    [[ -f $config_file ]] || return 0
    while IFS= read -r line || [[ -n $line ]]; do
        line=${line%$'\r'}
        line=${line#$'\xef\xbb\xbf'}
        [[ -z $line || $line == \#* ]] && continue
        [[ $line == *=* ]] || die 'Configuration requires KEY=value lines.'
        key=${line%%=*}
        value=${line#*=}
        case "$key" in
            WSL_DISTRO)
                [[ $value =~ ^[A-Za-z0-9._-]*$ ]] || die 'WSL_DISTRO requires an ASCII distribution name, e.g. Ubuntu-24.04.'
                WSL_DISTRO=$value ;;
            FLUKA_BIN)
                [[ -z $value || $value == /* ]] || die 'FLUKA_BIN must be an absolute Linux directory, without quotes.'
                fluka_bin=$value ;;
            *) die "Unknown configuration key: $key" ;;
        esac
    done < "$config_file"
}

wsl_call() {
    # Prevent Git Bash from rewriting Linux arguments into Windows paths.
    MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' command wsl.exe "$@"
}

check_wsl() {
    command -v wsl.exe >/dev/null || { printf 'WSL: brak polecenia wsl.exe\n'; return 1; }
    local listed distro found=0
    # Native WSL listings can be UTF-16LE; distribution names here are ASCII.
    if ! listed=$(MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' timeout 20s wsl.exe --list --quiet 2>&1 | tr -d '\000\r'); then
        printf 'WSL: niedostepny lub nie odpowiada. Sprawdz w PowerShell: wsl --list --verbose\n'
        printf 'Instalacja po przeczytaniu docs/windows.md: wsl --install -d Ubuntu\n'
        return 1
    fi
    [[ -n $listed ]] || { printf 'WSL: brak dystrybucji. Zainstaluj i uruchom Ubuntu.\n'; return 1; }
    if [[ -n $WSL_DISTRO ]]; then
        while IFS= read -r distro; do
            [[ $distro == "$WSL_DISTRO" ]] && found=1
        done <<< "$listed"
        (( found == 1 )) || {
            printf 'WSL: brak wybranej dystrybucji %s. Dostepne:\n%s\n' "$WSL_DISTRO" "$listed"
            printf 'Dostosuj config/windows.local.conf.\n'
            return 1
        }
    fi
    printf 'WSL: wybrano %s\n' "${WSL_DISTRO:-dystrybucje domyslna}"
}

linux_script() {
    local script=$1
    shift
    command -v cygpath >/dev/null || die 'Use fluka.cmd on Windows; in Linux use the individual .sh scripts.'
    local windows_root
    windows_root=$(cygpath -w "$project_root")
    local -a args=()
    [[ -z $WSL_DISTRO ]] || args+=(--distribution "$WSL_DISTRO")
    args+=(--cd "$windows_root" --exec env)
    # Supply a literal Linux path, independent of interactive shell startup.
    [[ -z $fluka_bin ]] || args+=("FLUKA_BIN=$fluka_bin")
    args+=(bash "$script" "$@")
    wsl_call "${args[@]}"
}

resolve_run() {
    [[ $1 =~ ^[A-Za-z0-9][A-Za-z0-9_-]*$ ]] || die 'Use a run ID, not a path. See fluka.cmd status.'
    selected_run="$project_root/runs/$1"
    [[ -d $selected_run && ! -L $selected_run && -f $selected_run/manifest.json ]] || die "Unknown run: $1"
}

action=${1:-help}
(( $# == 0 )) || shift
case "$action" in
    help|--help|-h)
        help_text ;;
    prepare)
        (( $# == 1 )) || die 'Usage: fluka.cmd prepare CASE; write notes in the prepared note.txt file.'
        new_run=$(bash "$project_root/scripts/prepare-run.sh" "$@")
        run_id=${new_run##*/}
        printf 'Przygotowano: %s\nID: %s\nNie uruchomiono obliczen.\n' "$(cygpath -w "$new_run")" "$run_id"
        printf 'Po instalacji: .\\fluka.cmd run %s 1\n' "$run_id" ;;
    status)
        (( $# <= 1 )) || die 'Usage: fluka.cmd status [ID]'
        if (( $# == 1 )); then
            resolve_run "$1"
            printf 'ID: %s\nStatus: ' "$1"
            if [[ -f $selected_run/status.txt ]]; then cat "$selected_run/status.txt"; else printf 'unknown\n'; fi
            printf 'Manifest:\n'; cat "$selected_run/manifest.json"
            if [[ -f $selected_run/execution.txt ]]; then printf '\nExecution:\n'; cat "$selected_run/execution.txt"; fi
        else
            shopt -s nullglob
            manifests=("$project_root"/runs/*/manifest.json)
            if (( ${#manifests[@]} == 0 )); then
                printf 'Brak przebiegow. Przygotuj pierwszy: .\\fluka.cmd prepare electron_500mev\n'
            else
                printf '%-65s %s\n' 'ID' 'STATUS'
                for manifest in "${manifests[@]}"; do
                    run_path=${manifest%/manifest.json}
                    state=unknown
                    if [[ -f $run_path/status.txt ]]; then state=$(< "$run_path/status.txt"); fi
                    printf '%-65s %s\n' "${run_path##*/}" "$state"
                done
            fi
        fi ;;
    doctor)
        (( $# == 0 )) || die 'Usage: fluka.cmd doctor'
        printf 'Projekt: %s\nGit Bash: %s\n' "$(cygpath -w "$project_root")" "$BASH_VERSION"
        load_config
        printf 'WSL_DISTRO: %s\nFLUKA_BIN: %s\n' "${WSL_DISTRO:-default}" "${fluka_bin:-PATH w Linux}"
        check_wsl || exit 1
        # Starting an installed distribution is allowed; an initial account setup is manual.
        linux_script scripts/check-linux.sh ;;
    run)
        (( $# >= 1 && $# <= 2 )) || die 'Usage: fluka.cmd run ID [CYCLES=1]'
        resolve_run "$1"
        cycles=${2:-1}
        [[ $cycles =~ ^[1-9][0-9]{0,2}$ ]] || die 'CYCLES must be an integer from 1 to 999.'
        [[ -f $selected_run/status.txt && $(< "$selected_run/status.txt") == prepared ]] || die 'Run is not prepared. Existing results will be preserved.'
        load_config
        check_wsl || exit 1
        linux_script scripts/run-fluka.sh "runs/$1" "$cycles" ;;
    test)
        (( $# == 0 )) || die 'Usage: fluka.cmd test'
        bash "$project_root/scripts/test-workflow.sh"
        bash "$project_root/scripts/test-windows.sh" ;;
    *) die "Unknown command: $action. Use fluka.cmd help." ;;
esac
