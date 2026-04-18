from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from fio_parser import FioParseError, parse_fio_json
from profiles import get_profile
from report import build_summary_json_path, format_full_report, write_summary_json
from runner import (
    FioExecutionError,
    FioNotFoundError,
    make_run_id,
    run_profile,
    run_profiles_concurrently
)

logger = logging.getLogger(__name__)


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
    run_parser.add_argument("--runtime", type=int, default=None, help="Override runtime in seconds.")
    run_parser.add_argument("--output-dir", default="results", help="Directory for fio JSON output.")
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
    concurrent_parser.add_argument("--runtime", type=int, default=None, help="Override runtime in seconds.")
    concurrent_parser.add_argument("--output-dir", default="results", help="Directory for fio JSON output.")
    concurrent_parser.add_argument(
        "--write-summary-json",
        action="store_true",
        help="Write app-generated summary JSON file.",
    )

    return parser


def handle_run(args: argparse.Namespace) -> int:
    """Handle single-profile execution."""
    profile = get_profile(args.profile)
    output_dir = Path(args.output_dir)
    run_id = make_run_id()

    result = run_profile(
        profile=profile,
        target=Path(args.target),
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
    return 0


def handle_run_concurrent(args: argparse.Namespace) -> int:
    """Handle concurrent two-profile execution."""
    profile1 = get_profile(args.profile1)
    profile2 = get_profile(args.profile2)
    output_dir = Path(args.output_dir)
    run_id = make_run_id()

    results = run_profiles_concurrently(
        profile1=profile1,
        profile2=profile2,
        base_target=Path(args.target),
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
    return 0


def main() -> int:
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
    except (ValueError, FioNotFoundError, FioExecutionError, FioParseError) as exc:
        logger.error("%s", exc)
        return 1

    logger.error("Unknown command: %s", args.command)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
