"""Tests for tte/log.py — trim_file() function."""

import os
import pytest

from tte.log import trim_file


class TestTrimFile:
    """Test the trim_file() function for log rotation."""

    def test_trim_file_keeps_recent_lines_when_exceeding_max(self, temp_log_file):
        """Should keep only the most recent max_lines when file exceeds limit."""
        # Write 15 lines
        with open(temp_log_file, "w", encoding="utf-8") as f:
            for i in range(1, 16):
                f.write(f"Line {i}\n")

        # Trim to 10 lines
        trim_file(temp_log_file, max_lines=10)

        # Read result
        with open(temp_log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        assert len(lines) == 10
        # Should keep lines 6-15 (last 10)
        assert lines[0] == "Line 6\n"
        assert lines[-1] == "Line 15\n"

    def test_trim_file_respects_max_lines_parameter(self, temp_log_file):
        """max_lines parameter should control how many lines are kept."""
        # Write 20 lines
        with open(temp_log_file, "w", encoding="utf-8") as f:
            for i in range(1, 21):
                f.write(f"Line {i}\n")

        # Trim to 5 lines
        trim_file(temp_log_file, max_lines=5)

        # Read result
        with open(temp_log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        assert len(lines) == 5
        # Should keep lines 16-20
        assert lines[0] == "Line 16\n"
        assert lines[-1] == "Line 20\n"

    def test_trim_file_does_not_modify_file_below_limit(self, temp_log_file):
        """File with fewer lines than max_lines should remain unchanged."""
        # Write 5 lines
        with open(temp_log_file, "w", encoding="utf-8") as f:
            for i in range(1, 6):
                f.write(f"Line {i}\n")

        # Trim with max_lines=10
        trim_file(temp_log_file, max_lines=10)

        # Read result
        with open(temp_log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        assert len(lines) == 5
        assert lines[0] == "Line 1\n"
        assert lines[-1] == "Line 5\n"

    def test_trim_file_creates_file_when_missing(self, tmp_path):
        """Should create empty file if it doesn't exist."""
        nonexistent_file = tmp_path / "new_log.log"
        assert not nonexistent_file.exists()

        trim_file(str(nonexistent_file), max_lines=100)

        assert nonexistent_file.exists()
        with open(nonexistent_file, "r", encoding="utf-8") as f:
            content = f.read()
        assert content == ""

    def test_trim_file_handles_empty_file(self, temp_log_file):
        """Empty file should remain empty after trim."""
        # Create empty file
        with open(temp_log_file, "w", encoding="utf-8") as f:
            f.write("")

        trim_file(temp_log_file, max_lines=100)

        with open(temp_log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        assert len(lines) == 0

    def test_trim_file_preserves_line_content(self, temp_log_file):
        """Line content should be preserved exactly (including formatting)."""
        # Write lines with various formatting
        test_lines = [
            "2026-02-13 10:00:00 - INFO - Starting application\n",
            "2026-02-13 10:00:01 - DEBUG - Connection established\n",
            "2026-02-13 10:00:02 - WARNING - High memory usage: 85%\n",
            "2026-02-13 10:00:03 - ERROR - Failed to connect to API\n",
        ]
        with open(temp_log_file, "w", encoding="utf-8") as f:
            f.writelines(test_lines)

        # Trim (should not modify since below limit)
        trim_file(temp_log_file, max_lines=10)

        with open(temp_log_file, "r", encoding="utf-8") as f:
            result_lines = f.readlines()

        assert result_lines == test_lines
