import argparse
import pathlib
import shutil
import subprocess
import sys

from ttu_tower.config.loader import parse as parse_pipeline_config

CONFIGS_DIR = pathlib.Path(__file__).parent.parent / "configs"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Run ttu-runall over every config in ./configs/")
    parser.add_argument("--averaging-minutes", type=int, metavar="MINUTES", help="Override [datafile] averaging_minutes for every stage")
    parser.add_argument("--redo-failures", "-f", action="store_true", help="Passed through to primary: also reprocess previously-failed files")
    parser.add_argument("--redo-all", "-r", action="store_true", help="Clear each config's existing primary output first, so every file is reprocessed instead of skipped")
    parser.add_argument("--nproc", "-n", type=int, metavar="N", help="Passed through to primary")
    parser.add_argument("--skip-primary", action="store_true", help="Skip the primary stage entirely")
    parser.add_argument("--test", "-t", action="store_true", help="Short test run, passed through to every stage")
    return parser.parse_args(argv)


def find_configs() -> list[pathlib.Path]:
    return sorted(CONFIGS_DIR.glob("*.ini"))


def clear_primary_output(config_path: pathlib.Path, args) -> None:
    resolve_args = [str(config_path)]
    if args.averaging_minutes is not None:
        resolve_args += ["--averaging-minutes", str(args.averaging_minutes)]
    if args.test:
        resolve_args += ["--test"]
    config = parse_pipeline_config("primary", cl_args=resolve_args)

    run_dir = pathlib.Path(config.run_dir)
    if run_dir.is_dir():
        print(f"Clearing existing output: {run_dir}")
        shutil.rmtree(run_dir)


def main(argv=None):
    args = parse_args(argv)

    extra = []
    if args.averaging_minutes is not None:
        extra += ["--averaging-minutes", str(args.averaging_minutes)]
    if args.redo_failures:
        extra += ["--redo-failures"]
    if args.nproc is not None:
        extra += ["--nproc", str(args.nproc)]
    if args.skip_primary:
        extra += ["--skip-primary"]
    if args.test:
        extra += ["--test"]

    configs = find_configs()
    if not configs:
        print(f"No .ini configs found in {CONFIGS_DIR}")
        return

    failed = []
    for config in configs:
        if args.redo_all:
            clear_primary_output(config, args)

        cmd = [sys.executable, "-m", "ttu_tower.cli.runall", str(config), *extra]
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd)
        if result.returncode != 0:
            failed.append(config.name)

    succeeded = len(configs) - len(failed)
    print(f"Done. {succeeded}/{len(configs)} succeeded.")
    if failed:
        print(f"Failed: {', '.join(failed)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
