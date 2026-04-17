from __future__ import annotations

from fio_parser import ProfileMetrics


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
    sections.append(format_combined_summary(metrics_list))
    return "\n\n".join(sections)
