from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class FioParseError(RuntimeError):
    """Raised when fio JSON cannot be parsed or is missing required fields."""


@dataclass
class ProfileMetrics:
    """Parsed metrics for one fio profile."""

    profile_name: str
    throughput_mib_s: float
    iops: float
    p95_ms: float | None
    p99_ms: float | None
    runtime_s: float | None


def kib_per_sec_to_mib_per_sec(value: float) -> float:
    """Convert KiB/s to MiB/s."""
    return value / 1024.0


def _safe_get_number(mapping: dict[str, Any], key: str) -> float:
    """Return numeric field or 0.0 when missing."""
    value = mapping.get(key, 0.0)
    if isinstance(value, (int, float)):
        return float(value)
    return 0.0


def _extract_percentile_ms(io_section: dict[str, Any], percentile_key: str) -> float | None:
    """
    Extract percentile latency and normalize to milliseconds.

    fio may expose completion latency percentiles under fields such as:
    - clat_ns
    - clat_us
    - clat_ms

    Exact JSON structure can vary by fio version.
    """
    latency_fields = [
        ("clat_ns", 1_000_000.0),
        ("clat_us", 1_000.0),
        ("clat_ms", 1.0),
    ]

    for field_name, divisor in latency_fields:
        field = io_section.get(field_name)
        if not isinstance(field, dict):
            continue

        percentiles = field.get("percentile")
        if not isinstance(percentiles, dict):
            continue

        raw_value = percentiles.get(percentile_key)
        if isinstance(raw_value, (int, float)):
            return float(raw_value) / divisor

    return None


def _max_optional(values: list[float | None]) -> float | None:
    """Return max of non-None values, or None if all are None."""
    filtered = [value for value in values if value is not None]
    return max(filtered) if filtered else None


def parse_fio_json(path: Path) -> ProfileMetrics:
    """
    Parse fio JSON output file and extract summary metrics.

    Throughput and IOPS are summed from read and write sections.
    P95/P99 are taken from available latency percentiles. If both read and write
    values exist, the larger one is used as a simple per-profile summary.
    """
    if not path.exists():
        raise FioParseError(f"fio JSON file does not exist: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise FioParseError(f"Malformed fio JSON in file: {path}") from exc

    jobs = data.get("jobs")
    if not isinstance(jobs, list) or not jobs:
        raise FioParseError(f"fio JSON does not contain a valid 'jobs' list: {path}")

    total_bw_kib_s = 0.0
    total_iops = 0.0
    p95_candidates: list[float | None] = []
    p99_candidates: list[float | None] = []
    runtime_s: float | None = None
    profile_name = str(path.stem)

    for job in jobs:
        if not isinstance(job, dict):
            continue

        if isinstance(job.get("jobname"), str):
            profile_name = job["jobname"]

        read_section = job.get("read", {})
        write_section = job.get("write", {})

        if isinstance(read_section, dict):
            total_bw_kib_s += _safe_get_number(read_section, "bw")
            total_iops += _safe_get_number(read_section, "iops")
            p95_candidates.append(_extract_percentile_ms(read_section, "95.000000"))
            p99_candidates.append(_extract_percentile_ms(read_section, "99.000000"))

        if isinstance(write_section, dict):
            total_bw_kib_s += _safe_get_number(write_section, "bw")
            total_iops += _safe_get_number(write_section, "iops")
            p95_candidates.append(_extract_percentile_ms(write_section, "95.000000"))
            p99_candidates.append(_extract_percentile_ms(write_section, "99.000000"))

        job_runtime = job.get("job_runtime")
        if isinstance(job_runtime, (int, float)):
            runtime_s = max(runtime_s or 0.0, float(job_runtime) / 1000.0)

    return ProfileMetrics(
        profile_name=profile_name,
        throughput_mib_s=kib_per_sec_to_mib_per_sec(total_bw_kib_s),
        iops=total_iops,
        p95_ms=_max_optional(p95_candidates),
        p99_ms=_max_optional(p99_candidates),
        runtime_s=runtime_s,
    )
