from __future__ import annotations

import json
from pathlib import Path

import pytest

from fio_parser import FioParseError, ProfileMetrics, parse_fio_json
from report import build_summary_json_path, write_summary_json


def test_parse_fio_json_sums_read_and_write(tmp_path: Path) -> None:
    sample = {
        "jobs": [
            {
                "jobname": "oltp_like",
                "read": {
                    "bw": 1024,
                    "iops": 100.0,
                    "runtime": 30000,
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
                    "runtime": 28000,
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
                "read": {
                    "bw": 4096,
                    "iops": 32.0,
                    "runtime": 10000,
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


def test_parse_fio_json_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FioParseError, match="does not exist"):
        parse_fio_json(tmp_path / "nonexistent.json")


def test_parse_fio_json_malformed_json(tmp_path: Path) -> None:
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{ not valid json", encoding="utf-8")
    with pytest.raises(FioParseError, match="Malformed"):
        parse_fio_json(bad_file)


def test_parse_fio_json_missing_jobs(tmp_path: Path) -> None:
    empty_file = tmp_path / "empty.json"
    empty_file.write_text(json.dumps({"fio version": "3.x", "jobs": []}), encoding="utf-8")
    with pytest.raises(FioParseError, match="valid 'jobs' list"):
        parse_fio_json(empty_file)


def test_build_summary_json_path_includes_run_id(tmp_path: Path) -> None:
    summary_path = build_summary_json_path(tmp_path, "20260418_120000")

    assert summary_path == tmp_path / "summary_20260418_120000.json"


def test_write_summary_json_creates_expected_payload(tmp_path: Path) -> None:
    output_path = tmp_path / "summary_20260418_120000.json"

    metrics_list = [
        ProfileMetrics(
            profile_name="streaming-like",
            throughput_mib_s=2110.62,
            iops=2110.62,
            p95_ms=9.63,
            p99_ms=11.99,
            runtime_s=5.0,
        ),
        ProfileMetrics(
            profile_name="background_backup",
            throughput_mib_s=719.69,
            iops=719.69,
            p95_ms=43.25,
            p99_ms=90.70,
            runtime_s=5.2,
        ),
    ]

    source_json_paths = [
        Path("streaming-like_20260418_120000.json"),
        Path("background_backup_20260418_120000.json"),
    ]

    write_summary_json(
        metrics_list=metrics_list,
        output_path=output_path,
        mode="concurrent",
        source_json_paths=source_json_paths,
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert payload["mode"] == "concurrent"
    assert payload["profiles"] == ["streaming-like", "background_backup"]

    assert payload["combined"]["total_throughput_mib_s"] == 2830.31
    assert payload["combined"]["total_iops"] == 2830.31

    assert payload["per_profile"][0]["profile_name"] == "streaming-like"
    assert payload["per_profile"][0]["source_json"] == "streaming-like_20260418_120000.json"

    assert payload["per_profile"][1]["profile_name"] == "background_backup"
    assert payload["per_profile"][1]["source_json"] == "background_backup_20260418_120000.json"

    assert payload["note"] is not None
