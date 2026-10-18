from pathlib import Path

import pytest

from analyzer.agent import build_agent
from analyzer.diagnosis import Diagnosis

LOG_CONTENT = (
    "2026-10-17 20:09:23,690 | INFO | app.main | Health check OK\n"
    "2026-10-17 20:09:23,709 | ERROR | app.main | Internal server error\n"
    "2026-10-17 20:09:23,738 | WARNING | app.main | Database connection attempt failed, retrying\n"
    "2026-10-17 20:09:23,739 | ERROR | app.main | Database unavailable\n"
    "2026-10-17 20:09:23,741 | ERROR | app.main | Timeout: payment-service\n"
)

FAKE_DIAGNOSIS = Diagnosis(
    description="desc",
    possible_causes=["cause"],
    severity="medium",
    checks=["check"],
    corrective_actions=["action"],
)


@pytest.fixture
def log_file(tmp_path) -> Path:
    path = tmp_path / "app.log"
    path.write_text(LOG_CONTENT, encoding="utf-8")
    return path


class FakeLLM:
    """Faux LLM : enregistre les incidents reçus et renvoie toujours le même diagnostic."""

    def __init__(self, fail_on: str | None = None):
        self.fail_on = fail_on
        self.received = []

    def __call__(self, incident_text: str) -> Diagnosis:
        self.received.append(incident_text)
        if self.fail_on and self.fail_on in incident_text:
            raise ConnectionError("Ollama injoignable")
        return FAKE_DIAGNOSIS


def test_all_incidents_are_diagnosed(log_file):
    llm = FakeLLM()

    state = build_agent(diagnose=llm).invoke({"log_file": log_file, "max_incidents": 10})

    assert len(state["results"]) == 3
    assert all(result.diagnosis == FAKE_DIAGNOSIS for result in state["results"])
    assert "3 incident(s) détecté(s), 3 analysé(s)" in state["report"]
    assert "hypothèses à vérifier" in state["report"]


def test_context_is_sent_to_llm(log_file):
    llm = FakeLLM()

    build_agent(diagnose=llm).invoke({"log_file": log_file, "max_incidents": 10})

    database_prompt = next(text for text in llm.received if "Database unavailable" in text)
    assert "Database connection attempt failed" in database_prompt


def test_max_incidents_is_respected(log_file):
    llm = FakeLLM()

    state = build_agent(diagnose=llm).invoke({"log_file": log_file, "max_incidents": 1})

    assert len(llm.received) == 1
    assert len(state["results"]) == 1


def test_llm_is_not_called_without_errors(tmp_path):
    log_file = tmp_path / "app.log"
    log_file.write_text("2026-10-17 20:09:23,690 | INFO | app.main | Health check OK\n", encoding="utf-8")
    llm = FakeLLM()

    state = build_agent(diagnose=llm).invoke({"log_file": log_file, "max_incidents": 3})

    assert llm.received == []
    assert "Aucune erreur à analyser" in state["report"]


def test_one_failure_does_not_stop_other_incidents(log_file):
    llm = FakeLLM(fail_on="Database unavailable")

    state = build_agent(diagnose=llm).invoke({"log_file": log_file, "max_incidents": 10})

    results = {result.incident.message: result for result in state["results"]}
    assert results["Database unavailable"].diagnosis is None
    assert "Ollama injoignable" in results["Database unavailable"].error
    assert results["Internal server error"].diagnosis == FAKE_DIAGNOSIS
    assert "Analyse impossible" in state["report"]
