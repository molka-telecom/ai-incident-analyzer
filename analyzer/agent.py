import logging
from collections.abc import Callable
from pathlib import Path
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from analyzer.diagnosis import Diagnosis, IncidentDiagnosis
from analyzer.incidents import Incident, extract_incidents
from analyzer.llm_client import diagnose_incident
from analyzer.llm_input import format_incident_for_llm
from analyzer.log_parser import read_log_file
from analyzer.report import format_report

logger = logging.getLogger(__name__)


class AgentState(TypedDict, total=False):
    """Les données qui circulent d'une étape (nœud) à l'autre du workflow."""

    log_file: Path
    max_incidents: int
    total_lines: int
    incidents: list[Incident]
    results: list[IncidentDiagnosis]
    report: str


def build_agent(diagnose: Callable[[str], Diagnosis] = diagnose_incident):
    """Construit le workflow. `diagnose` est remplaçable (ex. par un faux LLM dans les tests)."""

    def collect_incidents(state: AgentState) -> AgentState:
        entries = read_log_file(state["log_file"])
        incidents = extract_incidents(entries)
        logger.info("%d lignes lues, %d incident(s) détecté(s)", len(entries), len(incidents))
        return {"total_lines": len(entries), "incidents": incidents}

    def has_incidents(state: AgentState) -> str:
        return "diagnose" if state["incidents"] else "no_incident"

    def diagnose_incidents(state: AgentState) -> AgentState:
        to_analyze = state["incidents"][: state["max_incidents"]]
        results = []
        for number, incident in enumerate(to_analyze, start=1):
            logger.info("Analyse de l'incident %d/%d par le LLM : %s", number, len(to_analyze), incident.message)
            try:
                diagnosis = diagnose(format_incident_for_llm(incident))
                results.append(IncidentDiagnosis(incident, diagnosis=diagnosis))
            except Exception as exc:  # une erreur sur un incident ne bloque pas les autres
                logger.warning("Échec de l'analyse : %s", exc)
                results.append(IncidentDiagnosis(incident, error=str(exc)))
        return {"results": results}

    def build_report(state: AgentState) -> AgentState:
        results = state.get("results", [])
        return {"report": format_report(results, state["total_lines"], len(state["incidents"]))}

    graph = StateGraph(AgentState)
    graph.add_node("collect_incidents", collect_incidents)
    graph.add_node("diagnose_incidents", diagnose_incidents)
    graph.add_node("build_report", build_report)

    graph.add_edge(START, "collect_incidents")
    graph.add_conditional_edges(
        "collect_incidents",
        has_incidents,
        {"diagnose": "diagnose_incidents", "no_incident": "build_report"},
    )
    graph.add_edge("diagnose_incidents", "build_report")
    graph.add_edge("build_report", END)

    return graph.compile()


def run_agent(log_file: Path, max_incidents: int = 3) -> AgentState:
    """Lance le workflow complet sur un fichier de logs."""
    agent = build_agent()
    return agent.invoke({"log_file": log_file, "max_incidents": max_incidents})
