#!/usr/bin/env python3
"""Write a Polish run summary for a completed electron-wall FLUKA run."""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
from datetime import datetime
from pathlib import Path


def read_field(text: str, name: str) -> str | None:
    match = re.search(rf"^{re.escape(name)}=(.*)$", text, re.MULTILINE)
    return match.group(1).strip() if match else None


def number_line(text: str, pattern: str) -> str | None:
    match = re.search(pattern, text, re.MULTILINE)
    return match.group(1) if match else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_directory", type=Path)
    parser.add_argument(
        "--compare",
        type=Path,
        help="optional earlier run for a same-model repeatability comparison",
    )
    args = parser.parse_args()
    run_dir = args.run_directory.resolve()
    work_dir = run_dir / "work"
    manifest_path = run_dir / "manifest.json"
    execution_path = run_dir / "execution.txt"
    console_path = run_dir / "console.log"
    for path in (manifest_path, execution_path, console_path):
        if not path.is_file():
            parser.error(f"missing completed-run file: {path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    run_id = manifest.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        parser.error(f"invalid run_id in {manifest_path}")
    execution = execution_path.read_text(encoding="utf-8", errors="replace")
    console = console_path.read_text(encoding="utf-8", errors="replace")
    input_text = (work_dir / "input.inp").read_text(encoding="utf-8", errors="replace")
    water_phantom = "WATEM" in input_text and "WATTOT" in input_text
    run_status = (
        (run_dir / "status.txt").read_text(encoding="utf-8").strip()
        if (run_dir / "status.txt").is_file()
        else "brak"
    )
    start_text = read_field(execution, "started_utc")
    end_text = read_field(execution, "finished_utc")
    try:
        elapsed = (
            datetime.fromisoformat(end_text.replace("Z", "+00:00"))
            - datetime.fromisoformat(start_text.replace("Z", "+00:00"))
        ).total_seconds()
    except (AttributeError, ValueError):
        elapsed = None

    cycle_reports = sorted(work_dir.glob("input[0-9][0-9][0-9].out"))
    primary_total = 0
    blccre_warnings: list[str] = []
    air_auto_guess = False
    reports_for_review = sorted(set(cycle_reports).union(work_dir.glob("fluka_*/input*.out")))
    for report_path in reports_for_review:
        report = report_path.read_text(encoding="utf-8", errors="replace")
        if report_path in cycle_reports:
            primary = re.search(r"Total number of primaries run:\s+(\d+)", report)
            if primary:
                primary_total += int(primary.group(1))
        if "automatically guessed by FLUKA" in report and "Material AIR" in report:
            air_auto_guess = True
        blccre_warnings.extend(
            re.findall(
                r"Max\. error is\s+([0-9.]+)\s*%, for beta2 =\s*([0-9.Ee+-]+)",
                report,
            )
        )

    if elapsed is None:
        duration = "brak danych"
    else:
        seconds = int(round(elapsed))
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        duration = f"{hours} godz. {minutes} min {seconds} s"

    desktop_root = Path.home() / "Desktop" / "FLUKA-wyniki"
    desktop_dir = desktop_root / run_id
    desktop_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "PODSUMOWANIE SYMULACJI FLUKA — ELEKTRONY NA BLOK OŁOWIU",
        f"ID przebiegu: {run_id}",
        f"Status: {run_status}",
        f"Czas rozpoczęcia (UTC): {start_text or 'brak danych'}",
        f"Czas zakończenia (UTC): {end_text or 'brak danych'}",
        f"Łączny czas obliczeń: {duration}",
        f"Liczba cykli FLUKA: {len(cycle_reports)}",
        f"Ukończone historie pierwotne: {primary_total if cycle_reports else 'nie odczytano'}",
        "",
        "CO SYMULUJEMY",
        "Elektrony o energii kinetycznej 500 MeV padają prostopadle na blok Pb 10 × 10 × 10 cm. Ładunek paczki wynosi 20 pC (około 1,2483 × 10^8 elektronów); poprzeczny profil jest gaussowski, sigma_x = sigma_y = 1 mm.",
        "Normalizacja ładunku: N = |Q|/e = 20e-12 C / 1,602176634e-19 C. Wynik dawki z GeV/g na primary przelicza się współczynnikiem 1,602176462e-7 Gy/(GeV/g), a następnie mnoży przez N.",
        "Dawka pochłonięta jest liczona w powietrzu 10, 20 i 50 cm za tylną powierzchnią bloku, jeśli dany przebieg zawiera te detektory. Widma fluencji fotonów zapisują się dla tych odległości; widma neutronów, elektronów i pozytonów — w 20 cm.",
        "Przyjęty czasowy FWHM 100 ns nie jest rozdzielany w transporcie. Podane wartości są zintegrowane po paczce, nie oznaczają dawki szczytowej ani mocy dawki.",
        "",
        "WYNIKI POSTPROCESSINGU",
    ]
    if run_status not in ("finished_needs_review", "brak"):
        exit_code = read_field(execution, "exit_code")
        lines.extend(("", "PRZEBIEG NIEUKOŃCZONY"))
        if exit_code is not None:
            lines.append(f"Kod zakończenia runnera: {exit_code}.")
        if exit_code == "137" or "returned RC=137" in console:
            lines.append("Proces FLUKA został zakończony sygnałem SIGKILL (kod 137).")
        partial_counts = []
        for error_path in sorted(work_dir.glob("fluka_*/input*.err")):
            error_text = error_path.read_text(encoding="utf-8", errors="replace")
            progress = re.findall(
                r"^\s*(\d+)\s+\d+\s+\d+\s+[0-9.Ee+-]+",
                error_text,
                re.MULTILINE,
            )
            if progress:
                partial_counts.append(int(progress[-1]))
        planned = re.search(r"^START\s+([0-9.eE+-]+)", input_text, re.MULTILINE)
        if partial_counts:
            latest = max(partial_counts)
            planned_histories = float(planned.group(1)) if planned else None
            if planned_histories is not None:
                lines.append(
                    f"Ostatni zapisany postęp cyklu: {latest:,} z "
                    f"{int(planned_histories):,} historii; cykl nie został ukończony."
                )
            else:
                lines.append(f"Ostatni zapisany postęp cyklu: {latest:,} historii.")
        lines.append(
            "Częściowe wyniki scoringu nie są traktowane jako końcowy wynik ani jako statystycznie scalone dane."
        )
    if water_phantom:
        lines.insert(
            lines.index("Normalizacja ładunku: N = |Q|/e = 20e-12 C / 1,602176634e-19 C. Wynik dawki z GeV/g na primary przelicza się współczynnikiem 1,602176462e-7 Gy/(GeV/g), a następnie mnoży przez N."),
            "Wariant wodny zakłada energię monoenergetyczną 500 MeV; nie przypisano rozbieżności kątowej wiązki, bo brak danych źródłowych.",
        )
        lines.insert(
            lines.index("Przyjęty czasowy FWHM 100 ns nie jest rozdzielany w transporcie. Podane wartości są zintegrowane po paczce, nie oznaczają dawki szczytowej ani mocy dawki."),
            "Dodatkowo dawkę pochłoniętą liczymy w wodnym fantomie 10 × 10 × 10 cm, którego przednia powierzchnia znajduje się 1 m za ołowiem; siatka ma woksele 1 cm.",
        )
    for pattern, label in (
        (
            r"Peak dose at 10 cm: DOSE-EM=([0-9.eE+-]+), DOSE=([0-9.eE+-]+) Gy/pulse",
            "Maksymalna dawka 10 cm (DOSE-EM / DOSE)",
        ),
        (
            r"Peak dose at 20 cm: DOSE-EM=([0-9.eE+-]+), DOSE=([0-9.eE+-]+) Gy/pulse",
            "Maksymalna dawka 20 cm (DOSE-EM / DOSE)",
        ),
        (
            r"Peak dose at 50 cm: DOSE-EM=([0-9.eE+-]+), DOSE=([0-9.eE+-]+) Gy/pulse",
            "Maksymalna dawka 50 cm (DOSE-EM / DOSE)",
        ),
    ):
        match = re.search(pattern, console)
        if match:
            lines.append(f"{label}: {match.group(1)} / {match.group(2)} Gy/paczkę")
    for distance in ("10", "20", "50"):
        mean_match = re.search(
            rf"Mean dose at {distance} cm: DOSE-EM=([0-9.eE+-]+), DOSE=([0-9.eE+-]+) Gy/pulse",
            console,
        )
        if mean_match:
            lines.append(
                f"Średnia dawka powierzchniowa {distance} cm (DOSE-EM / DOSE): "
                f"{mean_match.group(1)} / {mean_match.group(2)} Gy/paczkę"
            )
    report_dir = Path(__file__).resolve().parents[1] / "reports" / "generated" / run_id
    distance_csv_for_errors = report_dir / "absorbed-dose-distance-summary.csv"
    distance_rows = []
    if distance_csv_for_errors.is_file():
        with distance_csv_for_errors.open(encoding="utf-8", newline="") as file:
            distance_rows = list(csv.DictReader(file))
        for distance in ("10", "20", "50"):
            distance_label = f"{distance} cm"
            em_row = next(
                (
                    row for row in distance_rows
                    if row["distance_behind_lead_cm"] == distance_label
                    and row["dose_type"] == "DOSE-EM"
                ),
                None,
            )
            total_row = next(
                (
                    row for row in distance_rows
                    if row["distance_behind_lead_cm"] == distance_label
                    and row["dose_type"] == "DOSE"
                ),
                None,
            )
            if em_row is None or total_row is None:
                continue
            if not any(f"Średnia dawka powierzchniowa {distance_label}" in line for line in lines):
                lines.append(
                    f"Średnia dawka powierzchniowa {distance_label} (DOSE-EM / DOSE): "
                    f"{float(em_row['mean_Gy_per_pulse']):.8g} / "
                    f"{float(total_row['mean_Gy_per_pulse']):.8g} Gy/paczkę"
                )
            if not any(f"Maksymalna dawka {distance_label}" in line for line in lines):
                lines.append(
                    f"Maksymalna dawka {distance_label} (DOSE-EM / DOSE): "
                    f"{float(em_row['peak_Gy_per_pulse']):.8g} / "
                    f"{float(total_row['peak_Gy_per_pulse']):.8g} Gy/paczkę"
                )
    water_summary = (
        Path(__file__).resolve().parents[1]
        / "reports"
        / "generated"
        / run_id
        / "absorbed-dose-water-summary.csv"
    )
    if water_phantom and water_summary.is_file():
        with water_summary.open(encoding="utf-8", newline="") as file:
            for row in csv.DictReader(file):
                lines.append(
                    f"Średnia objętościowa dawka w wodzie ({row['dose_type']}): "
                    f"{float(row['mean_Gy_per_pulse']):.8g} Gy/paczkę."
                )
                lines.append(
                    f"Maksimum w wodzie ({row['dose_type']}): "
                    f"{float(row['peak_Gy_per_pulse']):.8g} Gy/paczkę "
                    f"przy x/y/z = {row['peak_x_cm']}/{row['peak_y_cm']}/{row['peak_z_cm']} cm; "
                    f"błąd statystyczny koszyka: {float(row['peak_relative_error_percent']):.5g}%."
                )
    legacy_dose = re.search(
        r"Peak DEMAIR:\s*([0-9.eE+-]+)\s*Gy/pulse;\s*peak DTOT:\s*([0-9.eE+-]+)\s*Gy/pulse",
        console,
    )
    if legacy_dose and not any("20 cm" in line for line in lines):
        lines.append(
            "Maksymalna dawka 20 cm (DOSE-EM / DOSE): "
            f"{legacy_dose.group(1)} / {legacy_dose.group(2)} Gy/paczkę"
        )
    for particle in ("GAMMA10", "GAMMAS", "GAMMA50", "NEUT20", "ELEC20", "POSI20"):
        value = number_line(
            console,
            rf"Integrated {particle} fluence:\s*([0-9.eE+-]+)\s*cm\^-2 per pulse",
        )
        if value is not None:
            distance = {
                "GAMMA10": "fotonów 10 cm",
                "GAMMAS": "fotonów 20 cm",
                "GAMMA50": "fotonów 50 cm",
                "NEUT20": "neutronów 20 cm",
                "ELEC20": "elektronów 20 cm",
                "POSI20": "pozytonów 20 cm",
            }[particle]
            lines.append(f"Fluencja {distance}: {value} cm^-2/paczkę")
    legacy_fluence = re.search(
        r"photon fluence integrated over bins:\s*([0-9.eE+-]+)\s*cm\^-2 per pulse",
        console,
    )
    if legacy_fluence and not any("Fluencja fotonów 20 cm" in line for line in lines):
        lines.append(f"Fluencja fotonów 20 cm: {legacy_fluence.group(1)} cm^-2/paczkę")
    for particle, label in (("DEMAIR", "dawki DOSE-EM"), ("GAMMAS", "widma fotonów")):
        match = re.search(
            rf"{label} per-bin relative error at 20 cm: median=([0-9.eE+-]+)%, p90=([0-9.eE+-]+)%",
            console,
        )
        if match:
            lines.append(
                f"Względny błąd statystyczny koszyków {label} w 20 cm: "
                f"mediana {match.group(1)}%, 90. percentyl {match.group(2)}%"
            )
    if distance_rows:
        for row in distance_rows:
            if row["distance_behind_lead_cm"] == "20 cm" and row["dose_type"] == "DOSE-EM":
                try:
                    error_percent = float(row["peak_relative_error_percent"])
                except ValueError:
                    continue
                if error_percent == error_percent:
                    lines.append(
                        f"Względny błąd statystyczny w koszyku maksimum DOSE-EM (20 cm): {error_percent:.5g}%."
                    )
    if not any("Maksymalna dawka 20 cm" in line for line in lines):
        dose_csv = report_dir / "absorbed-dose-air-map.csv"
        if dose_csv.is_file():
            with dose_csv.open(encoding="utf-8", newline="") as file:
                values = list(csv.DictReader(file))
            if values:
                em_peak = max(float(row["dose_em_Gy_per_pulse"]) for row in values)
                total_peak = max(float(row["dose_total_Gy_per_pulse"]) for row in values)
                lines.append(
                    "Maksymalna dawka 20 cm (DOSE-EM / DOSE): "
                    f"{em_peak:.8g} / {total_peak:.8g} Gy/paczkę"
                )
    if not any("Fluencja fotonów 20 cm" in line for line in lines):
        spectrum_csv = report_dir / "photon-fluence-spectrum-at-20cm.csv"
        if spectrum_csv.is_file():
            with spectrum_csv.open(encoding="utf-8", newline="") as file:
                values = list(csv.DictReader(file))
            if values:
                total_fluence = sum(
                    float(row["fluence_cm-2_per_energy_bin_per_pulse"]) for row in values
                )
                lines.append(f"Fluencja fotonów 20 cm: {total_fluence:.8g} cm^-2/paczkę")
    if args.compare is not None:
        baseline = args.compare.resolve()
        try:
            baseline_id = json.loads((baseline / "manifest.json").read_text(encoding="utf-8"))["run_id"]
            baseline_dir = report_dir.parent / baseline_id
            with (baseline_dir / "absorbed-dose-distance-summary.csv").open(
                encoding="utf-8", newline=""
            ) as file:
                baseline_dose_rows = list(csv.DictReader(file))
            with (report_dir / "absorbed-dose-distance-summary.csv").open(
                encoding="utf-8", newline=""
            ) as file:
                current_dose_rows = list(csv.DictReader(file))
            baseline_dose = next(
                float(row["mean_Gy_per_pulse"])
                for row in baseline_dose_rows
                if row["distance_behind_lead_cm"] == "20 cm" and row["dose_type"] == "DOSE-EM"
            )
            current_dose = next(
                float(row["mean_Gy_per_pulse"])
                for row in current_dose_rows
                if row["distance_behind_lead_cm"] == "20 cm" and row["dose_type"] == "DOSE-EM"
            )
            with (baseline_dir / "photon-fluence-spectrum-at-20cm.csv").open(
                encoding="utf-8", newline=""
            ) as file:
                baseline_spectrum = list(csv.DictReader(file))
            with (report_dir / "photon-fluence-spectrum-at-20cm.csv").open(
                encoding="utf-8", newline=""
            ) as file:
                current_spectrum = list(csv.DictReader(file))
            fluence_column = "fluence_cm-2_per_energy_bin_per_pulse"
            baseline_fluence = sum(float(row[fluence_column]) for row in baseline_spectrum)
            current_fluence = sum(float(row[fluence_column]) for row in current_spectrum)
            lines.extend(
                (
                    "",
                    f"PORÓWNANIE POWTARZALNOŚCI Z {baseline_id}",
                    f"Średnia przestrzenna DOSE-EM w 20 cm: poprzednio {baseline_dose:.8g}, teraz {current_dose:.8g} Gy/paczkę ({(current_dose / baseline_dose - 1.0) * 100.0:+.3g}%).",
                    f"Zintegrowana fluencja fotonów w 20 cm: poprzednio {baseline_fluence:.8g}, teraz {current_fluence:.8g} cm^-2/paczkę ({(current_fluence / baseline_fluence - 1.0) * 100.0:+.3g}%).",
                    "To kontrola powtarzalności Monte Carlo, nie porównanie z pomiarem. Wariant badawczy definiuje suche powietrze jawnie, więc model różni się nieznacznie od poprzedniego przebiegu z automatycznie rozpoznanym AIR.",
                )
            )
        except (OSError, KeyError, StopIteration, ValueError, ZeroDivisionError) as error:
            parser.error(f"cannot compare with {baseline}: {error}")
    if not any("Gy/paczkę" in line or "cm^-2/paczkę" in line for line in lines):
        lines.append("Wyniki liczbowe postprocessingu nie zostały odczytane.")
    lines.extend(("", "PRZEGLĄD I OGRANICZENIA"))
    if len(cycle_reports) > 1:
        lines.append(
            "Wiele cykli połączono narzędziami FLUKA usbsuw/ustsuw; błędy względne koszyków są dostępne w CSV i logach postprocessingu."
        )
    else:
        lines.append("Pojedynczy cykl nie daje niezależnej oceny niepewności między cyklami.")
    if air_auto_guess:
        lines.append(
            "FLUKA zgłosiła automatyczne rozpoznanie materiału AIR; skład i gęstość wymagają potwierdzenia."
        )
    else:
        lines.append("Powietrze jest jawnie zdefiniowane w wejściu jako sucha mieszanina o gęstości 1,205e-3 g/cm3.")
    if blccre_warnings:
        unique = sorted(set(blccre_warnings), key=lambda item: float(item[0]), reverse=True)
        transport_note = (
            "Transport się zakończył, ale wpływ ostrzeżeń wymaga przeglądu."
            if run_status == "finished_needs_review"
            else "Ostrzeżenia pojawiły się przed przerwaniem przebiegu; wpływu na wyniki nie oceniono."
        )
        lines.append(
            "Ostrzeżenia BLCCRE: dopasowanie parametrów materiałowych dla rozpraszania Coulomba przekroczyło cel 1%; "
            + "; ".join(
                f"maks. błąd {error}% przy beta2={beta2}" for error, beta2 in unique
            )
            + f". {transport_note}"
        )
    lines.append(
        "Energia, profil i kierunek wiązki, ładunek, geometria i warunki powietrza pozostają założeniami technicznymi, jeśli nie potwierdzono ich pomiarem. Wynik nie jest walidacją osłony ani oceną bezpieczeństwa radiologicznego."
    )
    lines.extend(("", f"Pliki przebiegu: {run_dir}", f"Wyniki i wykresy: {desktop_dir}"))
    report_text = "\n".join(lines) + "\n"
    output_dir = report_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    project_report = output_dir / "podsumowanie-symulacji.txt"
    project_report.write_text(report_text, encoding="utf-8")
    desktop_report = desktop_dir / "podsumowanie-symulacji.txt"
    shutil.copy2(project_report, desktop_report)
    print(f"Saved {project_report}")
    print(f"Copied {desktop_report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
