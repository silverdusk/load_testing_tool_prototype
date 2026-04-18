from __future__ import annotations

from pathlib import Path

from profiles import PROFILES
from runner import build_fio_command, build_output_json_path


_OLTP = PROFILES["oltp_like"]
_STREAMING = PROFILES["streaming_like"]


def test_build_fio_command_contains_required_flags(tmp_path: Path) -> None:
    output_json = tmp_path / "out.json"
    cmd = build_fio_command(_OLTP, Path("/data/test.dat"), output_json)

    assert "fio" == cmd[0]
    assert "--output-format=json" in cmd
    assert f"--output={output_json}" in cmd
    assert "--time_based=1" in cmd
    assert "--filename=/data/test.dat" in cmd
    assert f"--name={_OLTP.name}" in cmd


def test_build_fio_command_runtime_uses_override(tmp_path: Path) -> None:
    output_json = tmp_path / "out.json"
    cmd = build_fio_command(_OLTP, Path("/data/test.dat"), output_json, runtime=10)

    assert "--runtime=10" in cmd
    assert f"--runtime={_OLTP.runtime}" not in cmd


def test_build_fio_command_runtime_falls_back_to_profile(tmp_path: Path) -> None:
    output_json = tmp_path / "out.json"
    cmd = build_fio_command(_OLTP, Path("/data/test.dat"), output_json, runtime=None)

    assert f"--runtime={_OLTP.runtime}" in cmd


def test_build_fio_command_rwmixread_included_when_set(tmp_path: Path) -> None:
    output_json = tmp_path / "out.json"
    cmd = build_fio_command(_OLTP, Path("/data/test.dat"), output_json)

    assert f"--rwmixread={_OLTP.rwmixread}" in cmd


def test_build_fio_command_rwmixread_omitted_when_none(tmp_path: Path) -> None:
    output_json = tmp_path / "out.json"
    cmd = build_fio_command(_STREAMING, Path("/data/test.dat"), output_json)

    assert not any(arg.startswith("--rwmixread") for arg in cmd)


def test_build_fio_command_direct_flag(tmp_path: Path) -> None:
    output_json = tmp_path / "out.json"
    cmd = build_fio_command(_OLTP, Path("/data/test.dat"), output_json)

    assert "--direct=1" in cmd


def test_build_output_json_path_format(tmp_path: Path) -> None:
    path = build_output_json_path(tmp_path, "oltp_like", "20260418_120000")

    assert path == tmp_path / "oltp_like_20260418_120000.json"


def test_build_output_json_path_replaces_spaces(tmp_path: Path) -> None:
    path = build_output_json_path(tmp_path, "my profile", "20260418_120000")

    assert " " not in path.name
    assert "my_profile" in path.name
