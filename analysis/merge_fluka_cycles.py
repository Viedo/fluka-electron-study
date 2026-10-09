#!/usr/bin/env python3
"""Merge multi-cycle FLUKA USRBIN and USRTRACK files with official tools."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def merge(executable: Path, inputs: list[Path], output: Path, cwd: Path) -> None:
    missing = [path for path in inputs if not path.is_file() or path.stat().st_size == 0]
    if missing:
        raise SystemExit(f"Missing cycle scoring files for {executable.name}: {missing}")
    answers = "\n".join([*(str(path) for path in inputs), "", str(output), ""])
    result = subprocess.run(
        [str(executable)],
        input=answers,
        text=True,
        cwd=cwd,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(
            f"{executable.name} failed (exit {result.returncode}):\n"
            f"{result.stdout}\n{result.stderr}"
        )
    if not output.is_file() or output.stat().st_size == 0:
        raise SystemExit(f"{executable.name} did not create {output}")
    print(result.stdout, end="")
    print(f"Merged {len(inputs)} cycle files into {output}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_directory", type=Path)
    parser.add_argument("cycles", type=int)
    parser.add_argument("--fluka-bin", type=Path, default=Path("/usr/local/fluka/bin"))
    args = parser.parse_args()
    if args.cycles < 2:
        parser.error("at least two cycles are required for statistical merging")

    work = args.run_directory.resolve() / "work"
    if not work.is_dir():
        parser.error(f"missing work directory: {work}")
    indices = range(1, args.cycles + 1)
    usrbins = [work / f"input{index:03d}_fort.21" for index in indices]
    usrtracks = [work / f"input{index:03d}_fort.22" for index in indices]
    if any(path.exists() for path in usrbins):
        merge(args.fluka_bin / "usbsuw", usrbins, work / "input_multicycle_fort.21.bnn", work)
    if any(path.exists() for path in usrtracks):
        merge(args.fluka_bin / "ustsuw", usrtracks, work / "input_multicycle_fort.22.trk", work)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
