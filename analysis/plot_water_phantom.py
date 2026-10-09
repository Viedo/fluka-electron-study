#!/usr/bin/env python3
"""Plot and export absorbed dose scored in a FLUKA water phantom."""

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
    parser.add_argument("run_directory", type=Path)
    args = parser.parse_args()

    run_dir = args.run_directory.resolve()
    work_dir = run_dir / "work"
    merged_file = work_dir / "input_multicycle_fort.21.bnn"
    dose_file = merged_file if merged_file.is_file() else work_dir / "input001_fort.21"
    manifest_file = run_dir / "manifest.json"
    reports = sorted(work_dir.glob("input[0-9][0-9][0-9].out"))
    for path in (dose_file, manifest_file):
        if not path.is_file():
            parser.error(f"missing required completed-run file: {path}")
    if not reports:
        parser.error(f"missing FLUKA cycle reports in {work_dir}")

    primaries = 0
    for report_path in reports:
        text = report_path.read_text(encoding="utf-8", errors="replace")
        match = re.search(r"Total number of primaries run:\s+(\d+)", text)
        if match is None:
            parser.error(f"cannot determine primary count from {report_path}")
        primaries += int(match.group(1))

    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    run_id = manifest.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        parser.error(f"invalid run_id in {manifest_file}")

    flair_dir = Path(os.environ.get("FLAIR_HOME", "/usr/local/flair")).resolve()
    sys.path[:0] = [str(flair_dir / "lib"), str(flair_dir)]
    import Data

    data = Data.Usrbin(str(dose_file))
    index_by_name = {detector.name: index for index, detector in enumerate(data.detector)}
    names = ("WATEM", "WATTOT")
    if any(name not in index_by_name for name in names):
        parser.error("USRBIN file must contain both WATEM and WATTOT detectors")

    em = data[index_by_name["WATEM"]]
    total = data[index_by_name["WATTOT"]]
    if (em.nx, em.ny, em.nz) != (total.nx, total.ny, total.nz):
        parser.error("WATEM and WATTOT dose grids have different dimensions")
    if min(em.nx, em.ny, em.nz) < 1:
        parser.error("water-phantom dose grid has invalid dimensions")
    if not np.allclose(
        (em.xlow, em.xhigh, em.ylow, em.yhigh, em.zlow, em.zhigh),
        (total.xlow, total.xhigh, total.ylow, total.yhigh, total.zlow, total.zhigh),
    ):
        parser.error("WATEM and WATTOT dose grids have different boundaries")

    scale = ELECTRONS_PER_PULSE * GEV_PER_G_TO_GY

    def read_score(name: str) -> tuple[np.ndarray, np.ndarray]:
        index = index_by_name[name]
        detector = data[index]
        values = data.readArray(index).astype(float) * scale
        data.open()
        try:
            raw_error = data.readRawStat(index)
        finally:
            data.close()
        if raw_error is None:
            errors = np.full(values.shape, np.nan)
        else:
            errors = (
                np.frombuffer(raw_error, dtype=np.float32)
                .astype(float)
                .reshape((detector.nx, detector.ny, detector.nz), order="F")
                * 100.0
            )
        return values, errors

    dose_em, error_em = read_score("WATEM")
    dose_total, error_total = read_score("WATTOT")
    positive = np.concatenate((dose_em[dose_em > 0], dose_total[dose_total > 0]))
    if positive.size == 0:
        parser.error("water-phantom dose contains no non-zero bins")
    vmin = float(positive.min())
    vmax = float(positive.max())
    if vmax <= vmin:
        vmax = vmin * (1.0 + 1e-6)

    dx = (em.xhigh - em.xlow) / em.nx
    dy = (em.yhigh - em.ylow) / em.ny
    dz = (em.zhigh - em.zlow) / em.nz
    x = em.xlow + (np.arange(em.nx) + 0.5) * dx
    y = em.ylow + (np.arange(em.ny) + 0.5) * dy
    z = em.zlow + (np.arange(em.nz) + 0.5) * dz
    xx, yy, zz = np.meshgrid(x, y, z, indexing="ij")

    project_root = Path(__file__).resolve().parents[1]
    output_dir = project_root / "reports" / "generated" / run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    cmap = plt.colormaps["inferno"].copy()
    cmap.set_bad("#d9d9d9")
    middle_z = em.nz // 2
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), constrained_layout=True)
    image = None
    for axis, values, title in (
        (axes[0], dose_em, "Electromagnetic dose (DOSE-EM)"),
        (axes[1], dose_total, "Total absorbed dose (DOSE)"),
    ):
        image = axis.imshow(
            np.ma.masked_less_equal(values[:, :, middle_z].T, 0),
            origin="lower",
            aspect="equal",
            extent=(em.xlow, em.xhigh, em.ylow, em.yhigh),
            interpolation="nearest",
            cmap=cmap,
            norm=LogNorm(vmin=vmin, vmax=vmax),
        )
        axis.set_xlabel("x [cm]")
        axis.set_ylabel("y [cm]")
        axis.set_title(title)
    assert image is not None
    fig.suptitle(
        f"Water phantom central slice (z={z[middle_z]:g} cm)\n"
        f"{primaries:,} histories, 20 pC electron pulse"
    )
    colorbar = fig.colorbar(image, ax=axes.ravel().tolist())
    colorbar.set_label("Absorbed dose [Gy per pulse]")
    slice_plot = output_dir / "absorbed-dose-water-central-slice.png"
    fig.savefig(slice_plot, dpi=180)
    plt.close(fig)

    fig = plt.figure(figsize=(9, 7), constrained_layout=True)
    axis = fig.add_subplot(111, projection="3d")
    positive_total = dose_total > 0
    axis.scatter(
        xx[positive_total],
        yy[positive_total],
        zz[positive_total],
        c=dose_total[positive_total],
        s=24,
        cmap=cmap,
        norm=LogNorm(vmin=vmin, vmax=vmax),
    )
    axis.set_xlabel("x [cm]")
    axis.set_ylabel("y [cm]")
    axis.set_zlabel("z [cm]")
    axis.set_title(f"Absorbed dose in 10 cm water phantom\n{primaries:,} histories")
    colorbar = fig.colorbar(axis.collections[0], ax=axis, pad=0.12)
    colorbar.set_label("Total absorbed dose [Gy per pulse]")
    volume_plot = output_dir / "absorbed-dose-water-3d.png"
    fig.savefig(volume_plot, dpi=180)
    plt.close(fig)

    csv_file = output_dir / "absorbed-dose-water-phantom.csv"
    np.savetxt(
        csv_file,
        np.column_stack(
            (
                xx.ravel(),
                yy.ravel(),
                zz.ravel(),
                dose_em.ravel(),
                error_em.ravel(),
                dose_total.ravel(),
                error_total.ravel(),
            )
        ),
        delimiter=",",
        header=(
            "x_cm,y_cm,z_cm,dose_em_Gy_per_pulse,dose_em_relative_error_percent,"
            "dose_total_Gy_per_pulse,dose_total_relative_error_percent"
        ),
        comments="",
        fmt="%.8g",
    )
    stats_file = output_dir / "absorbed-dose-water-summary.csv"
    summary_rows = []
    for name, values, errors in (
        ("DOSE-EM", dose_em, error_em),
        ("DOSE", dose_total, error_total),
    ):
        peak_index = np.unravel_index(np.argmax(values), values.shape)
        peak_error = float(errors[peak_index])
        nonzero_errors = errors[np.isfinite(errors) & (values > 0)]
        median_error = float(np.median(nonzero_errors)) if nonzero_errors.size else float("nan")
        p90_error = float(np.percentile(nonzero_errors, 90)) if nonzero_errors.size else float("nan")
        summary_rows.append(
            (
                name,
                float(values.mean()),
                float(values[peak_index]),
                float(x[peak_index[0]]),
                float(y[peak_index[1]]),
                float(z[peak_index[2]]),
                peak_error,
                median_error,
                p90_error,
            )
        )
        print(
            f"Water phantom {name}: mean={values.mean():.8g}, "
            f"peak={values[peak_index]:.8g} Gy/pulse at "
            f"x={x[peak_index[0]]:g}, y={y[peak_index[1]]:g}, z={z[peak_index[2]]:g} cm; "
            f"peak relative error={peak_error:.5g}%"
        )
        if nonzero_errors.size:
            print(
                f"Water phantom {name} relative error: "
                f"median={median_error:.5g}%, p90={p90_error:.5g}%"
            )
    np.savetxt(
        stats_file,
        np.asarray(summary_rows, dtype=object),
        delimiter=",",
        header=(
            "dose_type,mean_Gy_per_pulse,peak_Gy_per_pulse,peak_x_cm,peak_y_cm,"
            "peak_z_cm,peak_relative_error_percent,median_relative_error_percent,"
            "p90_relative_error_percent"
        ),
        comments="",
        fmt="%s",
    )

    desktop_root = Path(
        os.environ.get(
            "FLUKA_DESKTOP_RESULTS_DIR",
            str(Path.home() / "Desktop" / "FLUKA-wyniki"),
        )
    ).expanduser()
    desktop_dir = desktop_root / run_id
    desktop_dir.mkdir(parents=True, exist_ok=True)
    for source in (slice_plot, volume_plot, csv_file, stats_file):
        destination = desktop_dir / source.name
        shutil.copy2(source, destination)
        print(f"Copied {destination}")
    print(f"Scored water phantom: {em.nx} x {em.ny} x {em.nz} voxels")
    print(f"Electrons per pulse: {ELECTRONS_PER_PULSE:.8g}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
