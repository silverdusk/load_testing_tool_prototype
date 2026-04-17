from __future__ import annotations

import argparse
import sys
from pathlib import Path

from parser import FioParseError, parse_fio_json
from profiles import get_profile
from report import format_full_report
from runner import FioExecutionError, FioNotFoundError, run_profile, run_profiles_concurrently


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line interface."""
    parser = argparse.ArgumentParser(description="Small fio-based load testing tool.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run a single fio profile.")
    run_parser.add_argument("--profile", required=True, help="Profile name.")
    run_parser.add_argument("--target", required=True, help="Target file path.")
    run_parser.add_argument("--runtime", type=int, default=None, help="Override runtime in seconds.")
    run_parser.add_argument("--output-dir", default="results", help="Directory for fio JSON output.")

    concurrent_parser = subparsers.add_parser("run-concurrent", help="Run two fio profiles simultaneously.")
    concurrent_parser.add_argument("--profile1", required=True, help="First profile name.")
    concurrent_parser.add_argument("--profile2", required=True, help="Second profile name.")
    concurrent_parser.add_argument("--target", required=True, help="Base target file path.")
    concurrent_parser.add_argument("--runtime", type=int, default=None, help="Override runtime in seconds.")
    concurrent_parser.add_argument("--output-dir", default="results", help="Directory for fio JSON output.")

    return parser


def handle_run(args: argparse.Namespace) -> int:
    """Handle single-profile execution."""
    profile = get_profile(args.profile)
    result = run_profile(
        profile=profile,
        target=Path(args.target),
        output_dir=Path(args.output_dir),
        runtime=args.runtime,
    )
    metrics = parse_fio_json(result.json_path)
    print(format_full_report([metrics]))
    return 0


def handle_run_concurrent(args: argparse.Namespace) -> int:
    """Handle concurrent two-profile execution."""
    profile1 = get_profile(args.profile1)
    profile2 = get_profile(args.profile2)

    results = run_profiles_concurrently(
        profile1=profile1,
        profile2=profile2,
        base_target=Path(args.target),
        output_dir=Path(args.output_dir),
        runtime=args.runtime,
    )

    metrics_list = [parse_fio_json(result.json_path) for result in results]
    print(format_full_report(metrics_list))
    return 0


def main() -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "run":
            return handle_run(args)
        if args.command == "run-concurrent":
            return handle_run_concurrent(args)
    except (ValueError, FioNotFoundError, FioExecutionError, FioParseError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Unknown command: {args.command}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
