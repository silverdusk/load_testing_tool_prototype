from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class FioProfile:
    """Definition of fio workload profile."""

    name: str
    ioengine: str
    http_mode: str
    rw: str
    bs: str
    iodepth: int
    numjobs: int
    direct: bool
    time_based: bool
    runtime: int
    ioengine: str = "libaio"
    size: str = "1G"
    rwmixread: Optional[int] = None
    group_reporting: bool = False
    filename: Optional[str] = None

PROFILES: dict[str, FioProfile] = {
    "oltp_like": FioProfile(
        name="oltp-like",
        ioengine="libaio", # can be used io_uring - async I/O
        rw="randrw", # mixed random read and write
        rwmixread=70, # Percentage of a mixed workload that should be reads. Default: 50
        bs="4k", # The block size in bytes used for I/O units. Small transactions I/O
        iodepth=16, # queue depth per job for async testing
        numjobs=4, # number of parallel threads
        direct=1, # to bypass Page cache and measure real storage
        runtime=30,
    ),
    "streaming_like": FioProfile(
        name="streaming-like",
        rw="read", # sequential reading
        bs="1m", # bigger blocks than for OLTP
        iodepth=8,
        numjobs=2,
        direct=1,
        runtime=30,
    ),
    "streaming_s3_like": FioProfile(
        name="streaming-s3-like",
        ioengine=http,
        http_mode=s3,
        direct=1,
        rw="read",
        bs="1m",
        numjobs=16,
        time_based=1,
        runtime=60,
        group_reporting=1
    ),
    "background_backup": FioProfile(
        name="background_backup",
        rw="write",
        bs="1m",
        iodepth=8,
        numjobs=2,
        direct=1,
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
