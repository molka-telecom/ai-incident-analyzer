from analyzer.diagnosis import IncidentDiagnosis

SEVERITY_LABELS = {"low": "Faible", "medium": "Moyenne", "high": "Élevée", "critical": "Critique"}

WARNING_BANNER = (
    "⚠ Diagnostic généré par une IA : les causes sont des hypothèses à vérifier.\n"
    "  Aucune action n'a été exécutée automatiquement."
)


def format_result(result: IncidentDiagnosis, number: int) -> str:
    incident = result.incident
    lines = [
        f"=== Incident {number} : {incident.message} ===",
        f"Occurrences : {incident.count}",
    ]

    if result.diagnosis is None:
        lines.append(f"Analyse impossible : {result.error}")
        return "\n".join(lines)

    diagnosis = result.diagnosis
    lines.append(f"Gravité estimée : {SEVERITY_LABELS[diagnosis.severity]}")
    lines.append(f"Description : {diagnosis.description}")
    lines.append("Causes possibles (hypothèses à vérifier) :")
    lines.extend(f"  {i}. {cause}" for i, cause in enumerate(diagnosis.possible_causes, start=1))
    lines.append("Vérifications recommandées :")
    lines.extend(f"  - {check}" for check in diagnosis.checks)
    lines.append("Actions correctives proposées (à valider par un développeur) :")
    lines.extend(f"  - {action}" for action in diagnosis.corrective_actions)
    return "\n".join(lines)


def format_report(results: list[IncidentDiagnosis], total_lines: int, total_incidents: int) -> str:
    header = f"{total_lines} lignes lues, {total_incidents} incident(s) détecté(s), {len(results)} analysé(s)"
    if not results:
        return f"{header}\nAucune erreur à analyser."

    sections = [header, WARNING_BANNER]
    sections.extend(format_result(result, number) for number, result in enumerate(results, start=1))
    return "\n\n".join(sections)
