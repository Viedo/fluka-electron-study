#!/usr/bin/env python3
"""Plot energy-deposition views from the EDEP USRBIN of a completed run."""

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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_directory", type=Path, help="path to a project runs/<run_id> directory")
    args = parser.parse_args()

    run_dir = args.run_directory.resolve()
    work_dir = run_dir / "work"
    merged_file = work_dir / "input_multicycle_fort.21.bnn"
    output_file = merged_file if merged_file.is_file() else work_dir / "input001_fort.21"
    output_summaries = sorted(work_dir.glob("input[0-9][0-9][0-9].out"))
    if not output_file.is_file() or not output_summaries:
        parser.error(f"missing completed USRBIN run files in {work_dir}")
    manifest_file = run_dir / "manifest.json"
    if not manifest_file.is_file():
        parser.error(f"missing run manifest in {run_dir}")
    run_id = json.loads(manifest_file.read_text(encoding="utf-8")).get("run_id")
    if not isinstance(run_id, str) or not run_id:
        parser.error(f"invalid run_id in {manifest_file}")

    flair_dir = Path(os.environ.get("FLAIR_HOME", "/usr/local/flair")).resolve()
    sys.path[:0] = [str(flair_dir / "lib"), str(flair_dir)]
    import Data

    data = Data.Usrbin(str(output_file))
    detector_index = next(
        (index for index, detector in enumerate(data.detector) if detector.name == "EDEP"),
        None,
    )
    if detector_index is None:
        parser.error("USRBIN file has no EDEP detector")

    detector = data[detector_index]
    values = data.readArray(detector_index)
    plane = values[detector.nx // 2, :, :].T
    positive = plane[plane > 0]
    if positive.size == 0:
        parser.error("central x slice has no non-zero scoring bins")

    primaries = 0
    for summary_file in output_summaries:
        summary = summary_file.read_text(encoding="utf-8", errors="replace")
        match = re.search(r"Total number of primaries run:\s+(\d+)", summary)
        if match is None:
            parser.error(f"cannot determine primary count from {summary_file}")
        primaries += int(match.group(1))

    project_root = Path(__file__).resolve().parents[1]
    output_dir = project_root / "reports" / "generated" / run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    plot_file = output_dir / "energy-deposition-central-x.png"
    cmap = plt.colormaps["inferno"].copy()
    cmap.set_bad("#d9d9d9")

    fig, ax = plt.subplots(figsize=(9, 6), constrained_layout=True)
    image = ax.imshow(
        np.ma.masked_less_equal(plane, 0),
        origin="lower",
        aspect="auto",
        extent=(detector.ylow, detector.yhigh, detector.zlow, detector.zhigh),
        interpolation="nearest",
        cmap=cmap,
        norm=LogNorm(vmin=float(positive.min()), vmax=float(positive.max())),
    )
    ax.set_xlabel("y [cm]")
    ax.set_ylabel("z [cm]")
    ax.set_title(
        f"Energy deposition - central x slice\n{primaries:,} primaries"
    )
    colorbar = fig.colorbar(image, ax=ax)
    colorbar.set_label("Energy density [GeV/cm^3 per primary; gray = zero]")
    fig.savefig(plot_file, dpi=180)
    plt.close(fig)

    print(f"Saved {plot_file}")
    print(
        f"Detector {detector.name}: {detector.nx}x{detector.ny}x{detector.nz} bins; "
        f"central-slice range {positive.min():.6g} to {positive.max():.6g} "
        "GeV/cm^3 per primary"
    )

    z_centers = np.linspace(
        detector.zlow + (detector.zhigh - detector.zlow) / (2 * detector.nz),
        detector.zhigh - (detector.zhigh - detector.zlow) / (2 * detector.nz),
        detector.nz,
    )
    requested_depths = (1.0, 5.0, 9.0)
    z_indices = sorted(
        {int(np.argmin(np.abs(z_centers - depth))) for depth in requested_depths}
    )
    slices = [values[:, :, index].T for index in z_indices]
    slice_positive = [image[image > 0] for image in slices if np.any(image > 0)]
    if not slice_positive:
        parser.error("selected transverse slices have no non-zero scoring bins")
    positive_slices = np.concatenate(slice_positive)
    fig, axes = plt.subplots(
        1, len(z_indices), figsize=(5 * len(z_indices), 4.5), squeeze=False,
        constrained_layout=True,
    )
    image_artist = None
    for axis, index, image in zip(axes[0], z_indices, slices):
        image_artist = axis.imshow(
            np.ma.masked_less_equal(image, 0),
            origin="lower",
            aspect="equal",
            extent=(detector.xlow, detector.xhigh, detector.ylow, detector.yhigh),
            interpolation="nearest",
            cmap=cmap,
            norm=LogNorm(
                vmin=float(positive_slices.min()),
                vmax=float(positive_slices.max()),
            ),
        )
        axis.set_xlabel("x [cm]")
        axis.set_ylabel("y [cm]")
        axis.set_title(f"z = {z_centers[index]:.2f} cm")
    fig.suptitle(f"Energy deposition across the beam, {primaries:,} primaries")
    if image_artist is not None:
        colorbar = fig.colorbar(image_artist, ax=axes.ravel().tolist())
        colorbar.set_label("Energy density [GeV/cm^3 per primary; gray = zero]")
    transverse_file = output_dir / "energy-deposition-transverse-slices.png"
    fig.savefig(transverse_file, dpi=180)
    plt.close(fig)
    print(f"Saved {transverse_file}")

    dx = (detector.xhigh - detector.xlow) / detector.nx
    dy = (detector.yhigh - detector.ylow) / detector.ny
    dz = (detector.zhigh - detector.zlow) / detector.nz
    energy_per_depth_bin = np.sum(values, axis=(0, 1)) * dx * dy * dz
    profile_file = output_dir / "energy-deposition-longitudinal.png"
    fig, ax = plt.subplots(figsize=(8, 5), constrained_layout=True)
    ax.plot(z_centers, energy_per_depth_bin, marker="o", markersize=3)
    ax.set_xlabel("Depth z [cm]")
    ax.set_ylabel("Energy deposited [GeV per primary per z bin]")
    ax.set_title(f"Longitudinal energy deposition, {primaries:,} primaries")
    ax.grid(True, alpha=0.3)
    fig.savefig(profile_file, dpi=180)
    plt.close(fig)

    csv_file = output_dir / "energy-deposition-longitudinal.csv"
    np.savetxt(
        csv_file,
        np.column_stack((z_centers, energy_per_depth_bin)),
        delimiter=",",
        header="z_center_cm,energy_deposited_GeV_per_primary_per_z_bin",
        comments="",
        fmt="%.8g",
    )
    print(f"Saved {profile_file}")
    print(f"Saved {csv_file}")

    x_centers = detector.xlow + (np.arange(detector.nx) + 0.5) * dx
    y_centers = detector.ylow + (np.arange(detector.ny) + 0.5) * dy
    radius = np.hypot(x_centers[:, None], y_centers[None, :])
    radial_step = 0.5
    radial_max = float(radius.max())
    radial_edges = np.arange(
        0.0,
        np.ceil(radial_max / radial_step) * radial_step + radial_step * 0.5,
        radial_step,
    )
    energy_by_xy_cell = np.sum(values, axis=2) * dx * dy * dz
    energy_by_annulus, _ = np.histogram(
        radius.ravel(),
        bins=radial_edges,
        weights=energy_by_xy_cell.ravel(),
    )
    xy_cells_by_annulus, _ = np.histogram(radius.ravel(), bins=radial_edges)
    voxel_counts = xy_cells_by_annulus * detector.nz
    annulus_volumes = voxel_counts * dx * dy * dz
    density_by_annulus = np.divide(
        energy_by_annulus,
        annulus_volumes,
        out=np.zeros_like(energy_by_annulus),
        where=annulus_volumes > 0,
    )
    radial_centers = (radial_edges[:-1] + radial_edges[1:]) / 2
    radial_positive = density_by_annulus > 0
    if not np.any(radial_positive):
        parser.error("radial profile has no non-zero scoring bins")

    radial_file = output_dir / "energy-deposition-radial.png"
    fig, ax = plt.subplots(figsize=(8, 5), constrained_layout=True)
    ax.plot(
        radial_centers[radial_positive],
        density_by_annulus[radial_positive],
        marker="o",
        markersize=4,
    )
    ax.set_yscale("log")
    ax.set_xlabel("Radius from beam axis r [cm]")
    ax.set_ylabel("Mean energy density [GeV/cm^3 per primary]")
    ax.set_title(f"Radial energy deposition in lead, {primaries:,} primaries")
    ax.grid(True, which="both", alpha=0.3)
    fig.savefig(radial_file, dpi=180)
    plt.close(fig)

    volume_threshold = float(values.max()) * 1.0e-3
    occupied = values >= volume_threshold
    if not np.any(occupied):
        parser.error("3D visualization threshold excludes all scoring bins")
    x_centers = detector.xlow + (np.arange(detector.nx) + 0.5) * dx
    y_centers = detector.ylow + (np.arange(detector.ny) + 0.5) * dy
    xx, yy, zz = np.meshgrid(x_centers, y_centers, z_centers, indexing="ij")
    norm = LogNorm(vmin=volume_threshold, vmax=float(values.max()))
    fig = plt.figure(figsize=(10, 8), constrained_layout=True)
    ax = fig.add_subplot(111, projection="3d")
    points = ax.scatter(
        xx[occupied],
        yy[occupied],
        zz[occupied],
        c=values[occupied],
        s=14,
        cmap="inferno",
        norm=norm,
        marker="s",
        linewidths=0,
        depthshade=False,
    )
    ax.set_xlim(detector.xlow, detector.xhigh)
    ax.set_ylim(detector.ylow, detector.yhigh)
    ax.set_zlim(detector.zlow, detector.zhigh)
    ax.set_box_aspect(
        (
            detector.xhigh - detector.xlow,
            detector.yhigh - detector.ylow,
            detector.zhigh - detector.zlow,
        )
    )
    ax.set_xlabel("x [cm]")
    ax.set_ylabel("y [cm]")
    ax.set_zlabel("z [cm]")
    ax.set_title(
        f"3D energy-deposition voxels, {primaries:,} primaries\n"
        "Showing bins at or above 0.1% of the maximum"
    )
    colorbar = fig.colorbar(points, ax=ax, shrink=0.65, pad=0.12)
    colorbar.set_label("Energy density [GeV/cm^3 per primary]")
    volume_file = output_dir / "energy-deposition-3d.png"
    fig.savefig(volume_file, dpi=180)
    plt.close(fig)
    print(
        f"Saved {volume_file} "
        f"({int(occupied.sum())} voxels; threshold {volume_threshold:.6g} GeV/cm^3 per primary)"
    )

    radial_csv = output_dir / "energy-deposition-radial.csv"
    np.savetxt(
        radial_csv,
        np.column_stack(
            (
                radial_edges[:-1],
                radial_edges[1:],
                radial_centers,
                density_by_annulus,
                energy_by_annulus,
                voxel_counts,
            )
        ),
        delimiter=",",
        header=(
            "radius_min_cm,radius_max_cm,radius_center_cm,"
            "mean_energy_density_GeV_per_cm3_per_primary,"
            "energy_deposited_GeV_per_primary_per_annulus,scored_voxel_count"
        ),
        comments="",
        fmt="%.8g",
    )
    print(f"Saved {radial_file}")
    print(f"Saved {radial_csv}")

    desktop_root = Path(
        os.environ.get(
            "FLUKA_DESKTOP_RESULTS_DIR",
            str(Path.home() / "Desktop" / "FLUKA-wyniki"),
        )
    ).expanduser()
    desktop_run_dir = desktop_root / run_id
    desktop_run_dir.mkdir(parents=True, exist_ok=True)
    plot_files = (
        plot_file,
        transverse_file,
        profile_file,
        radial_file,
        volume_file,
    )
    for source in plot_files:
        destination = desktop_run_dir / source.name
        shutil.copy2(source, destination)
        print(f"Copied {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
