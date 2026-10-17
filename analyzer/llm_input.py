from analyzer.incidents import Incident

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def incident_to_dict(incident: Incident) -> dict:
    """Convertit un incident en dictionnaire (exportable en JSON)."""
    return {
        "level": incident.level,
        "logger": incident.logger,
        "message": incident.message,
        "occurrences": incident.count,
        "first_seen": incident.first_seen.strftime(DATE_FORMAT),
        "last_seen": incident.last_seen.strftime(DATE_FORMAT),
        "context": incident.context,
        "line_numbers": incident.line_numbers,
    }


def format_incident_for_llm(incident: Incident) -> str:
    """Résumé court et lisible d'un incident, destiné à être envoyé au LLM."""
    lines = [
        f"Niveau : {incident.level}",
        f"Source : {incident.logger}",
        f"Message d'erreur : {incident.message}",
        f"Occurrences : {incident.count} "
        f"(du {incident.first_seen.strftime(DATE_FORMAT)} au {incident.last_seen.strftime(DATE_FORMAT)})",
    ]
    if incident.context:
        lines.append("Logs précédant l'erreur :")
        lines.extend(f"- WARNING {message}" for message in incident.context)
    else:
        lines.append("Logs précédant l'erreur : aucun")
    return "\n".join(lines)
