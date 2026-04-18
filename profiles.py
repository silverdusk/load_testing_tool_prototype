from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FioProfile:
    """Definition of fio workload profile."""

    name: str
    rw: str
    bs: str
    iodepth: int
    numjobs: int
    direct: bool
    runtime: int
    ioengine: str = "posixaio"  # posixaio works on macOS and Linux; prefer libaio/io_uring on Linux
    time_based: bool = True
    size: str = "1G"
    rwmixread: int | None = None
    group_reporting: bool = True

PROFILES: dict[str, FioProfile] = {
    "oltp_like": FioProfile(
        name="oltp-like",
        ioengine="posixaio", # posixaio works on macOS and Linux; prefer libaio/io_uring on Linux
        rw="randrw",         # random mixed read/write simulates unpredictable DB access patterns
        rwmixread=70,        # 70% reads / 30% writes — typical OLTP ratio; fio default is 50%
        bs="4k",             # matches common DB page size; small blocks stress IOPS over throughput
        iodepth=16,          # outstanding I/O requests per job; higher depth exercises async I/O
        numjobs=4,           # parallel workers simulating concurrent DB sessions
        direct=True,         # bypass page cache to measure raw storage latency, not OS buffer speed
        runtime=30,
    ),
    "streaming_like": FioProfile(
        name="streaming-like",
        rw="read",           # sequential reads simulate continuous media delivery
        bs="1m",             # large blocks maximize throughput; typical streaming chunk size
        iodepth=8,           # enough depth to keep the read pipeline full without over-queuing
        numjobs=2,           # two parallel readers simulate concurrent stream clients
        direct=True,         # bypass page cache for accurate storage throughput measurement
        runtime=30,
    ),
    "background_backup": FioProfile(
        name="background_backup",
        rw="write",          # sequential writes simulate a backup stream writing data continuously
        bs="1m",             # large blocks reduce IOPS pressure; optimized for throughput
        iodepth=8,           # moderate depth keeps write pipeline full without starvation
        numjobs=2,           # two writers provide realistic backup concurrency
        direct=True,         # bypass page cache so writes reach storage immediately
        runtime=30,
    ),
}


def get_profile(name: str) -> FioProfile:
    """Return a predefined fio profile by name."""
    try:
        return PROFILES[name]
    except KeyError as exc:
        available = ", ".join(sorted(PROFILES))
        raise ValueError(f"Unknown profile '{name}'. Available profiles: {available}") from exc
