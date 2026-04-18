from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from main import _validate_common_args, handle_run_concurrent
from profiles import get_profile


class TestValidateCommonArgs:
    def test_accepts_valid_args(self, tmp_path: Path) -> None:
        _validate_common_args(tmp_path / "test.dat", tmp_path / "results", runtime=30)

    def test_rejects_zero_runtime(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="positive integer"):
            _validate_common_args(tmp_path / "test.dat", tmp_path, runtime=0)

    def test_rejects_negative_runtime(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="positive integer"):
            _validate_common_args(tmp_path / "test.dat", tmp_path, runtime=-5)

    def test_accepts_none_runtime(self, tmp_path: Path) -> None:
        _validate_common_args(tmp_path / "test.dat", tmp_path, runtime=None)

    def test_rejects_nonexistent_target_parent(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="Target parent directory does not exist"):
            _validate_common_args(tmp_path / "ghost" / "test.dat", tmp_path, runtime=None)

    def test_rejects_target_that_is_directory(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="must be a file path"):
            _validate_common_args(tmp_path, tmp_path / "results", runtime=None)

    def test_rejects_output_dir_that_is_a_file(self, tmp_path: Path) -> None:
        existing_file = tmp_path / "not_a_dir.txt"
        existing_file.write_text("x", encoding="utf-8")
        with pytest.raises(ValueError, match="not a directory"):
            _validate_common_args(tmp_path / "test.dat", existing_file, runtime=None)


class TestHandleRunConcurrent:
    def test_rejects_duplicate_profiles(self, tmp_path: Path) -> None:
        args = argparse.Namespace(
            profile1="streaming_like",
            profile2="streaming_like",
            target=str(tmp_path / "test.dat"),
            output_dir=str(tmp_path),
            runtime=None,
            write_summary_json=False,
        )
        with pytest.raises(ValueError, match="must be different"):
            handle_run_concurrent(args)


class TestGetProfile:
    def test_returns_known_profile(self) -> None:
        profile = get_profile("oltp_like")
        assert profile.name == "oltp-like"

    def test_raises_for_unknown_profile(self) -> None:
        with pytest.raises(ValueError, match="Unknown profile"):
            get_profile("nonexistent")

    def test_error_lists_available_profiles(self) -> None:
        with pytest.raises(ValueError, match="oltp_like"):
            get_profile("nonexistent")
