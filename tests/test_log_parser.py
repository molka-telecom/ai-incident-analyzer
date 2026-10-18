from datetime import datetime

import pytest

from analyzer.log_parser import parse_line, read_log_file


def test_parse_valid_line():
    entry = parse_line("2026-10-17 20:09:23,739 | ERROR | app.main | Database unavailable\n", line_number=6)

    assert entry is not None
    assert entry.timestamp == datetime(2026, 10, 17, 20, 9, 23, 739000)
    assert entry.level == "ERROR"
    assert entry.logger == "app.main"
    assert entry.message == "Database unavailable"
    assert entry.line_number == 6


def test_message_containing_separator_is_kept_whole():
    entry = parse_line("2026-10-17 20:09:23,739 | CRITICAL | app.main | Disk full | /var/data", line_number=1)

    assert entry.message == "Disk full | /var/data"


@pytest.mark.parametrize(
    "line",
    [
        "",
        "ceci n'est pas un log",
        "2026-10-17 20:09:23,739 | ERROR | il manque un champ",
        "date-invalide | ERROR | app.main | message",
    ],
)
def test_invalid_lines_are_ignored(line):
    assert parse_line(line, line_number=1) is None


def test_read_log_file_skips_invalid_lines(tmp_path):
    log_file = tmp_path / "app.log"
    log_file.write_text(
        "2026-10-17 20:09:23,690 | INFO | app.main | Health check OK\n"
        "ligne invalide\n"
        "\n"
        "2026-10-17 20:09:23,709 | ERROR | app.main | Boom\n",
        encoding="utf-8",
    )

    entries = read_log_file(log_file)

    assert [entry.level for entry in entries] == ["INFO", "ERROR"]
    assert [entry.line_number for entry in entries] == [1, 4]


def test_read_empty_file(tmp_path):
    log_file = tmp_path / "empty.log"
    log_file.write_text("", encoding="utf-8")

    assert read_log_file(log_file) == []
