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
    ioengine: str = "libaio"
    time_based: bool = True
    size: str = "1G"
    rwmixread: int | None = None
    group_reporting: bool = True
    filename: str | None = None
    http_mode: str | None = None

PROFILES: dict[str, FioProfile] = {
    "oltp_like": FioProfile(
        name="oltp-like",
        ioengine="libaio", # can be used io_uring - async I/O
        rw="randrw", # mixed random read and write
        rwmixread=70, # Percentage of a mixed workload that should be reads. Default: 50
        bs="4k", # The block size in bytes used for I/O units. Small transactions I/O
        iodepth=16, # queue depth per job for async testing
        numjobs=4, # number of parallel threads
        direct=True, # to bypass Page cache and measure real storage
        runtime=30,
    ),
    "streaming_like": FioProfile(
        name="streaming-like",
        rw="read", # sequential reading
        bs="1m", # bigger blocks than for OLTP
        iodepth=8,
        numjobs=2,
        direct=True,
        runtime=30,
    ),
    # Template only: requires --http-host, --http-s3-key-id, --http-s3-keyfile,
    # and --http-s3-bucket which are not modeled here. Extend FioProfile before use.
    "streaming_s3_like": FioProfile(
        name="streaming-s3-like",
        ioengine="http",
        http_mode="s3",
        rw="read",
        bs="1m",
        iodepth=1,
        numjobs=16,
        direct=True,
        runtime=60,
        group_reporting=True,
    ),
    "background_backup": FioProfile(
        name="background_backup",
        rw="write",
        bs="1m",
        iodepth=8,
        numjobs=2,
        direct=True,
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
