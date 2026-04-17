from __future__ import annotations

import json
from pathlib import Path

from parser import parse_fio_json


def test_parse_fio_json_sums_read_and_write(tmp_path: Path) -> None:
    sample = {
        "jobs": [
            {
                "jobname": "oltp_like",
                "job_runtime": 30000,
                "read": {
                    "bw": 1024,
                    "iops": 100.0,
                    "clat_ns": {
                        "percentile": {
                            "95.000000": 2_000_000,
                            "99.000000": 4_000_000,
                        }
                    },
                },
                "write": {
                    "bw": 2048,
                    "iops": 200.0,
                    "clat_ns": {
                        "percentile": {
                            "95.000000": 3_000_000,
                            "99.000000": 5_000_000,
                        }
                    },
                },
            }
        ]
    }

    json_path = tmp_path / "sample.json"
    json_path.write_text(json.dumps(sample), encoding="utf-8")

    metrics = parse_fio_json(json_path)

    assert metrics.profile_name == "oltp_like"
    assert metrics.throughput_mib_s == 3.0
    assert metrics.iops == 300.0
    assert metrics.p95_ms == 3.0
    assert metrics.p99_ms == 5.0
    assert metrics.runtime_s == 30.0


def test_parse_fio_json_handles_read_only(tmp_path: Path) -> None:
    sample = {
        "jobs": [
            {
                "jobname": "streaming_like",
                "job_runtime": 10000,
                "read": {
                    "bw": 4096,
                    "iops": 32.0,
                    "clat_us": {
                        "percentile": {
                            "95.000000": 500.0,
                            "99.000000": 900.0,
                        }
                    },
                },
                "write": {},
            }
        ]
    }

    json_path = tmp_path / "sample_read_only.json"
    json_path.write_text(json.dumps(sample), encoding="utf-8")

    metrics = parse_fio_json(json_path)

    assert metrics.profile_name == "streaming_like"
    assert metrics.throughput_mib_s == 4.0
    assert metrics.iops == 32.0
    assert metrics.p95_ms == 0.5
    assert metrics.p99_ms == 0.9
    assert metrics.runtime_s == 10.0
