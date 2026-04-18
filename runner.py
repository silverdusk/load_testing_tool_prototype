from __future__ import annotations

import logging
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from profiles import FioProfile

logger = logging.getLogger(__name__)


class FioNotFoundError(RuntimeError):
    """Raised when fio is not installed or not available in PATH."""


class FioExecutionError(RuntimeError):
    """Raised when fio finishes with a non-zero exit code."""


@dataclass
class RunResult:
    """Result of a fio process execution."""

    profile_name: str
    command: list[str]
    returncode: int
    stdout: str
    stderr: str
    json_path: Path


@dataclass
class PendingRun:
    """fio process launched and waiting to be collected."""

    profile_name: str
    command: list[str]
    process: subprocess.Popen[str]
    json_path: Path


def make_run_id() -> str:
    """Return a timestamp identifier shared by all files of one application run."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def build_output_json_path(output_dir: Path, profile_name: str, run_id: str) -> Path:
    """Build a timestamped fio JSON output path."""
    safe_name = profile_name.replace(" ", "_")
    return output_dir / f"{safe_name}_{run_id}.json"


def ensure_fio_installed() -> None:
    """Validate that fio is available in PATH."""
    if shutil.which("fio") is None:
        raise FioNotFoundError(
            "fio was not found in PATH. Install fio and make sure it is available in your shell."
        )


def build_fio_command(
    profile: FioProfile,
    target: Path,
    output_json: Path,
    runtime: int | None = None,
) -> list[str]:
    """
    Build a fio command from a FioProfile.

    Notes:
    - Uses time-based execution.
    - Uses JSON output.
    - Stores output in a dedicated file.
    """
    effective_runtime = runtime if runtime is not None else profile.runtime

    command = [
        "fio",
        f"--name={profile.name}",
        f"--filename={target}",
        f"--rw={profile.rw}",
        f"--bs={profile.bs}",
        f"--iodepth={profile.iodepth}",
        f"--numjobs={profile.numjobs}",
        f"--direct={1 if profile.direct else 0}",
        f"--runtime={effective_runtime}",
        "--time_based=1",                                        # run for fixed duration, not until size is consumed
        f"--group_reporting={1 if profile.group_reporting else 0}",  # merge per-job stats into one summary row
        f"--ioengine={profile.ioengine}",
        f"--size={profile.size}",
        "--output-format=json",                                  # machine-readable output for parsing
        f"--output={output_json}",                               # write JSON to file, not stdout
    ]

    if profile.rwmixread is not None:
        command.append(f"--rwmixread={profile.rwmixread}")

    if profile.http_mode is not None:
        command.append(f"--http-mode={profile.http_mode}")

    return command


def launch_profile(
    profile: FioProfile,
    target: Path,
    output_dir: Path,
    runtime: int | None = None,
    run_id: str | None = None,
) -> PendingRun:
    """Launch one fio process and return a handle that can be awaited later."""
    output_dir.mkdir(parents=True, exist_ok=True)

    effective_run_id = run_id or make_run_id()
    json_path = build_output_json_path(output_dir, profile.name, effective_run_id)
    command = build_fio_command(profile, target, json_path, runtime=runtime)

    logger.info("Launching fio profile '%s'", profile.name)
    logger.debug("Command: %s", " ".join(command))

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    return PendingRun(
        profile_name=profile.name,
        command=command,
        process=process,
        json_path=json_path,
    )


def collect_run(pending: PendingRun) -> RunResult:
    """Wait for a launched fio process and validate its result."""
    stdout, stderr = pending.process.communicate()

    result = RunResult(
        profile_name=pending.profile_name,
        command=pending.command,
        returncode=pending.process.returncode,
        stdout=stdout,
        stderr=stderr,
        json_path=pending.json_path,
    )

    if result.returncode != 0:
        logger.error("Profile '%s' failed with exit code %d", result.profile_name, result.returncode)
        logger.debug("fio stderr: %s", result.stderr.strip())
        raise FioExecutionError(
            f"fio failed for profile '{result.profile_name}' with exit code {result.returncode}"
        )

    if not result.json_path.exists():
        raise FioExecutionError(
            f"fio completed for profile '{result.profile_name}', but JSON output file was not created: "
            f"{result.json_path}"
        )

    logger.info("Profile '%s' completed", result.profile_name)
    return result


def run_profile(
    profile: FioProfile,
    target: Path,
    output_dir: Path,
    runtime: int | None = None,
    run_id: str | None = None,
) -> RunResult:
    """Run a single fio profile and return execution details."""
    ensure_fio_installed()
    pending = launch_profile(profile, target, output_dir, runtime=runtime, run_id=run_id)
    return collect_run(pending)


def run_profiles_concurrently(
    profile1: FioProfile,
    profile2: FioProfile,
    base_target: Path,
    output_dir: Path,
    runtime: int | None = None,
    run_id: str | None = None,
) -> list[RunResult]:
    """
    Run two fio profiles simultaneously.

    Each profile gets its own target file derived from the same base target name.
    This keeps the example simple and reduces accidental file-level interference.
    """
    ensure_fio_installed()
    output_dir.mkdir(parents=True, exist_ok=True)
    effective_run_id = run_id or make_run_id()

    target1 = base_target.with_name(f"{base_target.name}.{profile1.name}.dat")
    target2 = base_target.with_name(f"{base_target.name}.{profile2.name}.dat")

    logger.info("Launching concurrent profiles: '%s' and '%s'", profile1.name, profile2.name)
    pending1 = launch_profile(profile1, target1, output_dir, runtime=runtime, run_id=effective_run_id)
    pending2 = launch_profile(profile2, target2, output_dir, runtime=runtime, run_id=effective_run_id)

    try:
        result1 = collect_run(pending1)
    except Exception:
        logger.debug("Terminating '%s' after sibling failure", pending2.profile_name)
        pending2.process.terminate()
        pending2.process.wait()
        raise

    result2 = collect_run(pending2)
    return [result1, result2]
