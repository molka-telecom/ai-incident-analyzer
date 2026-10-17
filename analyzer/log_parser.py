from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# Doit correspondre au LOG_FORMAT de app/logging_config.py
LOG_SEPARATOR = " | "
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S,%f"


@dataclass
class LogEntry:
    """Une ligne de log découpée en champs."""

    timestamp: datetime
    level: str
    logger: str
    message: str
    line_number: int


def parse_line(line: str, line_number: int) -> LogEntry | None:
    """Découpe une ligne 'date | NIVEAU | module | message'. Renvoie None si la ligne est invalide."""
    parts = line.rstrip("\n").split(LOG_SEPARATOR, maxsplit=3)
    if len(parts) != 4:
        return None

    raw_timestamp, level, logger, message = parts
    try:
        timestamp = datetime.strptime(raw_timestamp, TIMESTAMP_FORMAT)
    except ValueError:
        return None

    return LogEntry(timestamp, level, logger, message, line_number)


def read_log_file(path: Path) -> list[LogEntry]:
    """Lit un fichier de logs et renvoie la liste des lignes valides."""
    entries = []
    with path.open(encoding="utf-8") as log_file:
        for line_number, line in enumerate(log_file, start=1):
            entry = parse_line(line, line_number)
            if entry is not None:
                entries.append(entry)
    return entries
