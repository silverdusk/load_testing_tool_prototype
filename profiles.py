from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


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
    size: str = "1G"
    rwmixread: Optional[int] = None

PROFILES: dict[str, FioProfile] = {
    "oltp_like": FioProfile(
        name="oltp-like",
        rw="randrw",
        bs="4k",
        iodepth=16,
        numjobs=4,
        direct=True,
        runtime=30,
        rwmixread=70,
    ),
    "streaming_like": FioProfile(
        name="streaming-like",
        rw="read",
        bs="1m",
        iodepth=8,
        numjobs=2,
        direct=True,
        runtime=30,
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
