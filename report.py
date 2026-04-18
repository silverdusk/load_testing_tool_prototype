from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Literal

from fio_parser import ProfileMetrics

logger = logging.getLogger(__name__)


PERCENTILE_NOTE = (
    "Exact combined P95/P99 are not shown because they cannot be calculated correctly "
    "from separate fio JSON summaries alone. Exact aggregation would require "
    "histogram-style data such as json+."
)


def build_summary_json_path(output_dir: Path, run_id: str) -> Path:
    """Build a timestamped summary JSON path."""
    return output_dir / f"summary_{run_id}.json"


def write_summary_json(
    metrics_list: list[ProfileMetrics],
    output_path: Path,
    mode: Literal["single", "concurrent"],
    source_json_paths: list[Path] | None = None,
) -> None:
    """Write app-generated summary JSON."""
    per_profile = []

    source_names = [p.name for p in source_json_paths] if source_json_paths else []

    for index, metrics in enumerate(metrics_list):
        item = {
            "profile_name": metrics.profile_name,
            "throughput_mib_s": round(metrics.throughput_mib_s, 2),
            "iops": round(metrics.iops, 2),
            "p95_ms": round(metrics.p95_ms, 2) if metrics.p95_ms is not None else None,
            "p99_ms": round(metrics.p99_ms, 2) if metrics.p99_ms is not None else None,
            "runtime_s": round(metrics.runtime_s, 2) if metrics.runtime_s is not None else None,
        }
        if index < len(source_names):
            item["source_json"] = source_names[index]
        per_profile.append(item)

    payload: dict = {
        "mode": mode,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "profiles": [m.profile_name for m in metrics_list],
        "per_profile": per_profile,
    }

    if len(metrics_list) > 1:
        payload["combined"] = {
            "total_throughput_mib_s": round(sum(m.throughput_mib_s for m in metrics_list), 2),
            "total_iops": round(sum(m.iops for m in metrics_list), 2),
        }
        payload["note"] = PERCENTILE_NOTE

    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    logger.info("Summary JSON written: %s", output_path)


def _format_latency(value: float | None) -> str:
    """Format latency in milliseconds."""
    return f"{value:.2f} ms" if value is not None else "N/A"


def format_profile_summary(metrics: ProfileMetrics) -> str:
    """Format one profile summary for console output."""
    runtime = f"{metrics.runtime_s:.1f} s" if metrics.runtime_s is not None else "N/A"

    return (
        f"Profile: {metrics.profile_name}\n"
        f"  Throughput : {metrics.throughput_mib_s:.2f} MiB/s\n"
        f"  IOPS       : {metrics.iops:.2f}\n"
        f"  P95        : {_format_latency(metrics.p95_ms)}\n"
        f"  P99        : {_format_latency(metrics.p99_ms)}\n"
        f"  Runtime    : {runtime}"
    )


def format_combined_summary(metrics_list: list[ProfileMetrics]) -> str:
    """
    Format combined summary.

    Exact combined P95/P99 should not be derived from separate fio JSON
    summaries because percentiles are not safely aggregatable without more
    detailed histogram-style data such as fio JSON+.
    """
    total_throughput = sum(item.throughput_mib_s for item in metrics_list)
    total_iops = sum(item.iops for item in metrics_list)

    return (
        "Combined summary:\n"
        f"  Total throughput : {total_throughput:.2f} MiB/s\n"
        f"  Total IOPS       : {total_iops:.2f}\n"
        "  Note             : Exact combined P95/P99 are not shown because they cannot be\n"
        "                     calculated correctly from separate fio JSON summaries alone.\n"
        "                     Exact aggregation would require histogram-style data such as json+."
    )


def format_full_report(metrics_list: list[ProfileMetrics]) -> str:
    """Format the final report shown in the console."""
    sections = [format_profile_summary(item) for item in metrics_list]
    if len(metrics_list) > 1:
        sections.append(format_combined_summary(metrics_list))
    return "\n\n".join(sections)
