from datetime import datetime, timedelta

from analyzer.incidents import extract_incidents
from analyzer.log_parser import LogEntry

START = datetime(2026, 10, 17, 20, 0, 0)


def make_entries(*lines: tuple[str, str]) -> list[LogEntry]:
    """Crée des LogEntry à partir de couples (niveau, message), espacés d'une seconde."""
    return [
        LogEntry(START + timedelta(seconds=i), level, "app.main", message, line_number=i + 1)
        for i, (level, message) in enumerate(lines)
    ]


def test_only_errors_are_kept():
    entries = make_entries(("INFO", "ok"), ("WARNING", "slow"), ("ERROR", "boom"), ("CRITICAL", "disk full"))

    incidents = extract_incidents(entries)

    assert sorted(incident.message for incident in incidents) == ["boom", "disk full"]


def test_identical_errors_are_grouped():
    entries = make_entries(("ERROR", "boom"), ("INFO", "ok"), ("ERROR", "boom"), ("ERROR", "boom"))

    incidents = extract_incidents(entries)

    assert len(incidents) == 1
    assert incidents[0].count == 3
    assert incidents[0].first_seen == START
    assert incidents[0].last_seen == START + timedelta(seconds=3)
    assert incidents[0].line_numbers == [1, 3, 4]


def test_context_contains_preceding_warnings():
    entries = make_entries(("INFO", "ok"), ("WARNING", "retrying"), ("ERROR", "db down"))

    incidents = extract_incidents(entries)

    assert incidents[0].context == ["retrying"]


def test_context_is_limited_to_three_warnings():
    entries = make_entries(
        ("WARNING", "w1"), ("WARNING", "w2"), ("WARNING", "w3"), ("WARNING", "w4"), ("ERROR", "boom")
    )

    incidents = extract_incidents(entries)

    assert incidents[0].context == ["w2", "w3", "w4"]


def test_error_on_first_line_has_no_context():
    incidents = extract_incidents(make_entries(("ERROR", "boom")))

    assert incidents[0].context == []


def test_most_frequent_incident_comes_first():
    entries = make_entries(("ERROR", "rare"), ("ERROR", "frequent"), ("ERROR", "frequent"))

    incidents = extract_incidents(entries)

    assert [incident.message for incident in incidents] == ["frequent", "rare"]


def test_no_errors_gives_no_incidents():
    assert extract_incidents(make_entries(("INFO", "ok"), ("WARNING", "slow"))) == []
