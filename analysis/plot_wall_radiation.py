#!/usr/bin/env python3
"""Convert wall-radiation USRBIN/USRTRACK scores to per-bunch plots."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np

ELEMENTARY_CHARGE_C = 1.602176634e-19
GEV_PER_G_TO_GY = 1.602176462e-7
PULSE_CHARGE_C = 20e-12
ELECTRONS_PER_PULSE = PULSE_CHARGE_C / ELEMENTARY_CHARGE_C


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_directory", type=Path, help="completed electron_wall run directory")
    args = parser.parse_args()

    run_dir = args.run_directory.resolve()
    work_dir = run_dir / "work"
    merged_dose_file = work_dir / "input_multicycle_fort.21.bnn"
    merged_spectrum_file = work_dir / "input_multicycle_fort.22.trk"
    dose_file = merged_dose_file if merged_dose_file.is_file() else work_dir / "input001_fort.21"
    spectrum_file = (
        merged_spectrum_file if merged_spectrum_file.is_file() else work_dir / "input001_fort.22"
    )
    summary_files = sorted(work_dir.glob("input[0-9][0-9][0-9].out"))
    manifest_file = run_dir / "manifest.json"
    for path in (dose_file, spectrum_file, manifest_file):
        if not path.is_file():
            parser.error(f"missing required completed-run file: {path}")
    if not summary_files:
        parser.error(f"missing FLUKA cycle reports in {work_dir}")

    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    run_id = manifest.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        parser.error(f"invalid run_id in {manifest_file}")

    primaries = 0
    for summary_file in summary_files:
        summary = summary_file.read_text(encoding="utf-8", errors="replace")
        match = re.search(r"Total number of primaries run:\s+(\d+)", summary)
        if match is None:
            parser.error(f"cannot determine primary count from {summary_file}")
        primaries += int(match.group(1))

    flair_dir = Path(os.environ.get("FLAIR_HOME", "/usr/local/flair")).resolve()
    sys.path[:0] = [str(flair_dir / "lib"), str(flair_dir)]
    import Data

    dose_data = Data.Usrbin(str(dose_file))
    dose_by_name = {detector.name: index for index, detector in enumerate(dose_data.detector)}
    required_names = ("DEMAIR", "DTOT")
    if any(name not in dose_by_name for name in required_names):
        parser.error("USRBIN file must contain both DEMAIR and DTOT detectors")

    em_index = dose_by_name["DEMAIR"]
    total_index = dose_by_name["DTOT"]
    em_detector = dose_data[em_index]
    total_detector = dose_data[total_index]
    if (
        em_detector.nx != total_detector.nx
        or em_detector.ny != total_detector.ny
        or em_detector.nz != total_detector.nz
    ):
        parser.error("DEMAIR and DTOT dose grids have different dimensions")
    if em_detector.nz != 1:
        parser.error(f"expected a one-layer dose map, got nz={em_detector.nz}")

    dose_scale = ELECTRONS_PER_PULSE * GEV_PER_G_TO_GY
    def score_values(name: str) -> tuple[np.ndarray, np.ndarray]:
        index = dose_by_name[name]
        detector = dose_data[index]
        values = dose_data.readArray(index)[:, :, 0].T * dose_scale
        dose_data.open()
        try:
            raw_error = dose_data.readRawStat(index)
        finally:
            dose_data.close()
        if raw_error is None:
            errors = np.full(values.shape, np.nan)
        else:
            errors = (
                np.frombuffer(raw_error, dtype=np.float32)
                .astype(float)
                .reshape((detector.nx, detector.ny, detector.nz), order="F")[:, :, 0]
                .T
                * 100.0
            )
        return values, errors

    dose_em, error_em = score_values("DEMAIR")
    dose_total, error_total = score_values("DTOT")
    distance_pairs = (
        ("10 cm", "D10EM", "D10TOT"),
        ("20 cm", "DEMAIR", "DTOT"),
        ("50 cm", "D50EM", "D50TOT"),
    )
    dose_scores: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    dose_errors: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for distance, em_name, total_name in distance_pairs:
        if em_name in dose_by_name and total_name in dose_by_name:
            em_values, em_errors = score_values(em_name)
            total_values, total_errors = score_values(total_name)
            dose_scores[distance] = (em_values, total_values)
            dose_errors[distance] = (em_errors, total_errors)
    positive_dose = np.concatenate(
        [values[values > 0] for pair in dose_scores.values() for values in pair]
    )
    if positive_dose.size == 0:
        parser.error("dose map contains no non-zero bins")

    project_root = Path(__file__).resolve().parents[1]
    output_dir = project_root / "reports" / "generated" / run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    cmap = plt.colormaps["inferno"].copy()
    cmap.set_bad("#d9d9d9")
    vmin = float(positive_dose.min())
    vmax = float(positive_dose.max())
    if vmax <= vmin:
        vmax = vmin * (1.0 + 1e-6)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5), constrained_layout=True)
    for axis, values, title in (
        (axes[0], dose_em, "Electromagnetic dose (DOSE-EM)"),
        (axes[1], dose_total, "Total absorbed dose (DOSE)"),
    ):
        image = axis.imshow(
            np.ma.masked_less_equal(values, 0),
            origin="lower",
            aspect="equal",
            extent=(
                em_detector.xlow,
                em_detector.xhigh,
                em_detector.ylow,
                em_detector.yhigh,
            ),
            interpolation="nearest",
            cmap=cmap,
            norm=LogNorm(vmin=vmin, vmax=vmax),
        )
        axis.set_xlabel("x [cm]")
        axis.set_ylabel("y [cm]")
        axis.set_title(title)
    fig.suptitle(
        f"Absorbed dose in air 20 cm behind 10 cm Pb\n"
        f"{primaries:,} histories, 20 pC ({ELECTRONS_PER_PULSE:.5g} electrons/pulse)"
    )
    colorbar = fig.colorbar(image, ax=axes.ravel().tolist())
    colorbar.set_label("Absorbed dose [Gy per pulse; gray = zero]")
    dose_plot = output_dir / "absorbed-dose-air-map.png"
    fig.savefig(dose_plot, dpi=180)
    plt.close(fig)

    dx = (em_detector.xhigh - em_detector.xlow) / em_detector.nx
    dy = (em_detector.yhigh - em_detector.ylow) / em_detector.ny
    x_centers = em_detector.xlow + (np.arange(em_detector.nx) + 0.5) * dx
    y_centers = em_detector.ylow + (np.arange(em_detector.ny) + 0.5) * dy
    xx, yy = np.meshgrid(x_centers, y_centers, indexing="xy")
    dose_csv = output_dir / "absorbed-dose-air-map.csv"
    np.savetxt(
        dose_csv,
        np.column_stack(
            (
                xx.ravel(),
                yy.ravel(),
                dose_em.ravel(),
                error_em.ravel(),
                dose_total.ravel(),
                error_total.ravel(),
            )
        ),
        delimiter=",",
        header=(
            "x_cm,y_cm,dose_em_Gy_per_pulse,dose_em_relative_error_percent,"
            "dose_total_Gy_per_pulse,dose_total_relative_error_percent"
        ),
        comments="",
        fmt="%.8g",
    )
    distance_rows = []
    for distance, (em_values, total_values) in dose_scores.items():
        for label, values, errors in (
            ("DOSE-EM", em_values, dose_errors[distance][0]),
            ("DOSE", total_values, dose_errors[distance][1]),
        ):
            iy, ix = np.unravel_index(np.argmax(values), values.shape)
            peak_error = float(errors[iy, ix])
            distance_rows.append(
                (
                    distance,
                    label,
                    float(values.mean()),
                    float(values[iy, ix]),
                    float(x_centers[ix]),
                    float(y_centers[iy]),
                    peak_error,
                )
            )
    distance_csv = output_dir / "absorbed-dose-distance-summary.csv"
    np.savetxt(
        distance_csv,
        np.asarray(distance_rows, dtype=object),
        delimiter=",",
        header=(
            "distance_behind_lead_cm,dose_type,mean_Gy_per_pulse,"
            "peak_Gy_per_pulse,peak_x_cm,peak_y_cm,peak_relative_error_percent"
        ),
        comments="",
        fmt="%s",
    )
    print(f"Saved {distance_csv}")
    if len(dose_scores) > 1:
        fig, axes = plt.subplots(
            len(dose_scores),
            2,
            figsize=(11, 4 * len(dose_scores)),
            squeeze=False,
            constrained_layout=True,
        )
        for row, (distance, (em_values, total_values)) in enumerate(dose_scores.items()):
            for column, (values, title) in enumerate(
                ((em_values, "DOSE-EM"), (total_values, "DOSE"))
            ):
                image = axes[row, column].imshow(
                    np.ma.masked_less_equal(values, 0),
                    origin="lower",
                    aspect="equal",
                    extent=(em_detector.xlow, em_detector.xhigh, em_detector.ylow, em_detector.yhigh),
                    interpolation="nearest",
                    cmap=cmap,
                    norm=LogNorm(vmin=vmin, vmax=vmax),
                )
                axes[row, column].set_title(f"{distance} behind wall: {title}")
                axes[row, column].set_xlabel("x [cm]")
                axes[row, column].set_ylabel("y [cm]")
        colorbar = fig.colorbar(image, ax=axes.ravel().tolist())
        colorbar.set_label("Absorbed dose [Gy per pulse]")
        distance_plot = output_dir / "absorbed-dose-distance-maps.png"
        fig.savefig(distance_plot, dpi=180)
        plt.close(fig)
        print(f"Saved {distance_plot}")

    spectrum_data = Data.Usrtrack(str(spectrum_file))
    spectrum_index = next(
        (
            index
            for index, detector in enumerate(spectrum_data.detector)
            if detector.name == "GAMMAS"
        ),
        None,
    )
    if spectrum_index is None:
        parser.error("USRTRACK file has no GAMMAS photon detector")
    spectrum_data.open()
    try:
        track_index_by_name = {
            detector.name: index for index, detector in enumerate(spectrum_data.detector)
        }
        track_names = [
            name
            for name in ("GAMMA10", "GAMMAS", "GAMMA50", "NEUT20", "ELEC20", "POSI20")
            if name in track_index_by_name
        ]
        track_scores = {}
        for name in track_names:
            index = track_index_by_name[name]
            detector = spectrum_data[index]
            raw_values = spectrum_data.readRawData(index)
            raw_statistics = spectrum_data.readRawStat(index)
            differential = np.frombuffer(raw_values, dtype=np.float32).astype(float)
            if differential.size != detector.ne:
                parser.error(f"USRTRACK {name} has an unexpected number of bins")
            low = np.asarray([detector.xmin(i) for i in range(detector.ne)])
            high = np.asarray([detector.xmax(i) for i in range(detector.ne)])
            errors = (
                np.full(differential.shape, np.nan)
                if raw_statistics is None
                else np.frombuffer(raw_statistics, dtype=np.float32).astype(float) * 100.0
            )
            fluence = differential * (high - low) * ELECTRONS_PER_PULSE
            track_scores[name] = (low, high, fluence, errors)
    finally:
        spectrum_data.close()
    if "GAMMAS" not in track_scores:
        parser.error("USRTRACK file has no GAMMAS photon detector")
    energy_low, energy_high, bin_fluence_per_pulse, relative_error_percent = track_scores["GAMMAS"]
    energy_center = np.sqrt(energy_low * energy_high)
    positive_spectrum = bin_fluence_per_pulse > 0
    if not np.any(positive_spectrum):
        parser.error("photon spectrum has no non-zero bins")

    spectrum_plot = output_dir / "photon-fluence-spectrum-at-20cm.png"
    fig, ax = plt.subplots(figsize=(8, 5), constrained_layout=True)
    ax.plot(
        energy_center[positive_spectrum] * 1e3,
        bin_fluence_per_pulse[positive_spectrum],
        marker=".",
        linewidth=1,
    )
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Photon energy [MeV]")
    ax.set_ylabel("Photon fluence [cm$^{-2}$ per energy bin per pulse]")
    ax.set_title(
        f"Photon spectrum averaged over air slab, {primaries:,} histories\n"
        "20 pC electron pulse; 20 cm behind 10 cm Pb"
    )
    ax.grid(True, which="both", alpha=0.3)
    fig.savefig(spectrum_plot, dpi=180)
    plt.close(fig)

    photon_names = [name for name in ("GAMMA10", "GAMMAS", "GAMMA50") if name in track_scores]
    if len(photon_names) > 1:
        fig, ax = plt.subplots(figsize=(8, 5), constrained_layout=True)
        for name in photon_names:
            low, high, fluence, _ = track_scores[name]
            positive = fluence > 0
            ax.plot(
                np.sqrt(low[positive] * high[positive]) * 1e3,
                fluence[positive],
                marker=".",
                linewidth=1,
                label={"GAMMA10": "10 cm", "GAMMAS": "20 cm", "GAMMA50": "50 cm"}[name],
            )
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("Photon energy [MeV]")
        ax.set_ylabel("Photon fluence [cm$^{-2}$ per energy bin per pulse]")
        ax.set_title("Photon spectra at different distances behind the lead")
        ax.grid(True, which="both", alpha=0.3)
        ax.legend()
        distance_spectrum_plot = output_dir / "photon-fluence-spectrum-by-distance.png"
        fig.savefig(distance_spectrum_plot, dpi=180)
        plt.close(fig)
        print(f"Saved {distance_spectrum_plot}")

    particle_names = [name for name in ("GAMMAS", "NEUT20", "ELEC20", "POSI20") if name in track_scores]
    if len(particle_names) > 1:
        fig, ax = plt.subplots(figsize=(8, 5), constrained_layout=True)
        labels = {"GAMMAS": "Photons", "NEUT20": "Neutrons", "ELEC20": "Electrons", "POSI20": "Positrons"}
        for name in particle_names:
            low, high, fluence, _ = track_scores[name]
            positive = fluence > 0
            ax.plot(
                np.sqrt(low[positive] * high[positive]) * 1e3,
                fluence[positive],
                marker=".",
                linewidth=1,
                label=labels[name],
            )
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("Particle kinetic energy [MeV]")
        ax.set_ylabel("Track-length fluence [cm$^{-2}$ per energy bin per pulse]")
        ax.set_title("Particle fluence spectra, 20 cm behind the lead")
        ax.grid(True, which="both", alpha=0.3)
        ax.legend()
        particle_plot = output_dir / "particle-fluence-spectra-at-20cm.png"
        fig.savefig(particle_plot, dpi=180)
        plt.close(fig)
        print(f"Saved {particle_plot}")

    spectrum_csv = output_dir / "photon-fluence-spectrum-at-20cm.csv"
    np.savetxt(
        spectrum_csv,
        np.column_stack(
            (
                energy_low,
                energy_high,
                energy_center,
                bin_fluence_per_pulse / (energy_high - energy_low),
                bin_fluence_per_pulse,
                relative_error_percent,
            )
        ),
        delimiter=",",
        header=(
            "energy_low_GeV,energy_high_GeV,energy_center_GeV,"
            "differential_fluence_cm-2_GeV-1_per_pulse,"
            "fluence_cm-2_per_energy_bin_per_pulse,relative_error_percent"
        ),
        comments="",
        fmt="%.8g",
    )
    all_spectra_csv = output_dir / "particle-fluence-spectra.csv"
    spectrum_columns = [energy_low, energy_high, energy_center]
    spectrum_headers = ["energy_low_GeV", "energy_high_GeV", "energy_center_GeV"]
    for name in track_names:
        _, _, fluence, errors = track_scores[name]
        spectrum_columns.extend((fluence, errors))
        spectrum_headers.extend((f"{name.lower()}_fluence_cm-2_per_bin_per_pulse", f"{name.lower()}_relative_error_percent"))
    np.savetxt(
        all_spectra_csv,
        np.column_stack(spectrum_columns),
        delimiter=",",
        header=",".join(spectrum_headers),
        comments="",
        fmt="%.8g",
    )

    for path in (dose_plot, spectrum_plot):
        print(f"Saved {path}")
    for path in (dose_csv, spectrum_csv, distance_csv):
        print(f"Saved {path}")
    print(f"Saved {all_spectra_csv}")
    print(f"Electrons per pulse: {ELECTRONS_PER_PULSE:.8g}")
    for name in track_names:
        fluence = track_scores[name][2]
        print(f"Integrated {name} fluence: {fluence.sum():.8g} cm^-2 per pulse")
    for distance, (em_values, total_values) in dose_scores.items():
        print(
            f"Mean dose at {distance}: DOSE-EM={em_values.mean():.8g}, "
            f"DOSE={total_values.mean():.8g} Gy/pulse"
        )
        print(f"Peak dose at {distance}: DOSE-EM={em_values.max():.8g}, DOSE={total_values.max():.8g} Gy/pulse")
    finite_dose_errors = error_em[np.isfinite(error_em) & (dose_em > 0)]
    finite_spectrum_errors = relative_error_percent[np.isfinite(relative_error_percent) & positive_spectrum]
    if finite_dose_errors.size:
        print(
            f"DEMAIR per-bin relative error at 20 cm: "
            f"median={np.median(finite_dose_errors):.5g}%, "
            f"p90={np.percentile(finite_dose_errors, 90):.5g}%"
        )
    if finite_spectrum_errors.size:
        print(
            f"GAMMAS per-bin relative error at 20 cm: "
            f"median={np.median(finite_spectrum_errors):.5g}%, "
            f"p90={np.percentile(finite_spectrum_errors, 90):.5g}%"
        )

    desktop_root = Path(
        os.environ.get(
            "FLUKA_DESKTOP_RESULTS_DIR",
            str(Path.home() / "Desktop" / "FLUKA-wyniki"),
        )
    ).expanduser()
    desktop_run_dir = desktop_root / run_id
    desktop_run_dir.mkdir(parents=True, exist_ok=True)
    desktop_plots = [dose_plot, spectrum_plot]
    for extra_name in (
        "absorbed-dose-distance-maps.png",
        "photon-fluence-spectrum-by-distance.png",
        "particle-fluence-spectra-at-20cm.png",
    ):
        extra = output_dir / extra_name
        if extra.is_file():
            desktop_plots.append(extra)
    for source in desktop_plots:
        destination = desktop_run_dir / source.name
        shutil.copy2(source, destination)
        print(f"Copied {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
