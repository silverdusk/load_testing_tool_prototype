from __future__ import annotations

import argparse
import logging
import sys
from enum import IntEnum
from pathlib import Path

from fio_parser import FioParseError, parse_fio_json
from profiles import get_profile
from report import build_summary_json_path, format_full_report, write_summary_json
from runner import (
    FioExecutionError,
    FioNotFoundError,
    make_run_id,
    run_profile,
    run_profiles_concurrently,
)

logger = logging.getLogger(__name__)


class ExitCode(IntEnum):
    SUCCESS = 0
    INTERNAL_ERROR = 1
    ARGUMENT_ERROR = 2   # consistent with argparse default for bad arguments
    FIO_NOT_FOUND = 3
    FIO_EXECUTION_FAILED = 4
    PARSE_FAILED = 5


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line interface."""
    parser = argparse.ArgumentParser(description="Small fio-based load testing tool.")
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable debug-level logging.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run a single fio profile.")
    run_parser.add_argument("--profile", required=True, help="Profile name.")
    run_parser.add_argument("--target", required=True, help="Target file path.")
    run_parser.add_argument(
        "--runtime", type=int, default=None, help="Override runtime in seconds."
    )
    run_parser.add_argument(
        "--output-dir", default="results", help="Directory for fio JSON output."
    )
    run_parser.add_argument(
        "--write-summary-json",
        action="store_true",
        help="Write app-generated summary JSON file.",
    )

    concurrent_parser = subparsers.add_parser(
        "run-concurrent",
        help="Run two fio profiles simultaneously.",
    )

    concurrent_parser.add_argument("--profile1", required=True, help="First profile name.")
    concurrent_parser.add_argument("--profile2", required=True, help="Second profile name.")
    concurrent_parser.add_argument("--target", required=True, help="Base target file path.")
    concurrent_parser.add_argument(
        "--runtime", type=int, default=None, help="Override runtime in seconds."
    )
    concurrent_parser.add_argument(
        "--output-dir", default="results", help="Directory for fio JSON output."
    )
    concurrent_parser.add_argument(
        "--write-summary-json",
        action="store_true",
        help="Write app-generated summary JSON file.",
    )

    return parser


def _validate_common_args(target: Path, output_dir: Path, runtime: int | None) -> None:
    """Validate arguments shared by both run and run-concurrent."""
    if runtime is not None and runtime <= 0:
        raise ValueError(f"--runtime must be a positive integer, got {runtime}")
    if not target.parent.exists():
        raise ValueError(f"Target parent directory does not exist: {target.parent}")
    if target.is_dir():
        raise ValueError(f"--target must be a file path, not a directory: {target}")
    if output_dir.exists() and not output_dir.is_dir():
        raise ValueError(f"--output-dir exists but is not a directory: {output_dir}")


def handle_run(args: argparse.Namespace) -> ExitCode:
    """Handle single-profile execution."""
    target = Path(args.target)
    output_dir = Path(args.output_dir)
    _validate_common_args(target, output_dir, args.runtime)

    profile = get_profile(args.profile)
    run_id = make_run_id()

    result = run_profile(
        profile=profile,
        target=target,
        output_dir=output_dir,
        runtime=args.runtime,
        run_id=run_id,
    )
    metrics = parse_fio_json(result.json_path)
    print(format_full_report([metrics]))

    if args.write_summary_json:
        summary_path = build_summary_json_path(output_dir, run_id)
        write_summary_json(
            metrics_list=[metrics],
            output_path=summary_path,
            mode="single",
            source_json_paths=[result.json_path],
        )
    return ExitCode.SUCCESS


def handle_run_concurrent(args: argparse.Namespace) -> ExitCode:
    """Handle concurrent two-profile execution."""
    target = Path(args.target)
    output_dir = Path(args.output_dir)
    _validate_common_args(target, output_dir, args.runtime)

    if args.profile1 == args.profile2:
        raise ValueError(
            f"--profile1 and --profile2 must be different, got '{args.profile1}' for both; "
            "duplicate profiles would overwrite the same output file"
        )

    profile1 = get_profile(args.profile1)
    profile2 = get_profile(args.profile2)
    run_id = make_run_id()

    results = run_profiles_concurrently(
        profile1=profile1,
        profile2=profile2,
        base_target=target,
        output_dir=output_dir,
        runtime=args.runtime,
        run_id=run_id,
    )

    metrics_list = [parse_fio_json(result.json_path) for result in results]
    print(format_full_report(metrics_list))

    if args.write_summary_json:
        summary_path = build_summary_json_path(output_dir, run_id)
        write_summary_json(
            metrics_list=metrics_list,
            output_path=summary_path,
            mode="concurrent",
            source_json_paths=[result.json_path for result in results],
        )
    return ExitCode.SUCCESS


def main() -> ExitCode:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
        stream=sys.stderr,
    )

    try:
        if args.command == "run":
            return handle_run(args)
        if args.command == "run-concurrent":
            return handle_run_concurrent(args)
    except ValueError as exc:
        logger.error("%s", exc)
        return ExitCode.ARGUMENT_ERROR
    except FioNotFoundError as exc:
        logger.error("%s", exc)
        return ExitCode.FIO_NOT_FOUND
    except FioExecutionError as exc:
        logger.error("%s", exc)
        return ExitCode.FIO_EXECUTION_FAILED
    except FioParseError as exc:
        logger.error("%s", exc)
        return ExitCode.PARSE_FAILED
    except Exception as exc:
        logger.error("Unexpected error: %s", exc)
        return ExitCode.INTERNAL_ERROR

    logger.error("Unknown command: %s", args.command)
    return ExitCode.INTERNAL_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
