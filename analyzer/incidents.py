from dataclasses import dataclass, field
from datetime import datetime

from analyzer.log_parser import LogEntry

ERROR_LEVELS = {"ERROR", "CRITICAL"}
CONTEXT_LEVEL = "WARNING"
MAX_CONTEXT_LINES = 3


@dataclass
class Incident:
    """Une erreur unique, avec son nombre d'occurrences et son contexte."""

    level: str
    logger: str
    message: str
    count: int
    first_seen: datetime
    last_seen: datetime
    context: list[str] = field(default_factory=list)
    line_numbers: list[int] = field(default_factory=list)


def get_context(entries: list[LogEntry], index: int) -> list[str]:
    """Renvoie les WARNING qui précèdent directement l'erreur située à la position index."""
    context = []
    i = index - 1
    while i >= 0 and len(context) < MAX_CONTEXT_LINES and entries[i].level == CONTEXT_LEVEL:
        context.insert(0, entries[i].message)
        i -= 1
    return context


def extract_incidents(entries: list[LogEntry]) -> list[Incident]:
    """Garde uniquement les erreurs et regroupe celles qui ont le même message."""
    incidents: dict[tuple[str, str], Incident] = {}

    for index, entry in enumerate(entries):
        if entry.level not in ERROR_LEVELS:
            continue

        key = (entry.logger, entry.message)
        if key not in incidents:
            incidents[key] = Incident(
                level=entry.level,
                logger=entry.logger,
                message=entry.message,
                count=0,
                first_seen=entry.timestamp,
                last_seen=entry.timestamp,
            )

        incident = incidents[key]
        incident.count += 1
        incident.last_seen = entry.timestamp
        incident.line_numbers.append(entry.line_number)
        for message in get_context(entries, index):
            if message not in incident.context:
                incident.context.append(message)

    # Les incidents les plus fréquents en premier
    return sorted(incidents.values(), key=lambda incident: incident.count, reverse=True)
