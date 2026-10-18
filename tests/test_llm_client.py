import json
from types import SimpleNamespace

import pytest

from analyzer import llm_client
from analyzer.diagnosis import Diagnosis

VALID_ANSWER = {
    "description": "La base de données est injoignable.",
    "possible_causes": ["Base arrêtée", "Base arrêtée", "Mauvais port"],
    "severity": "high",
    "checks": ["Vérifier l'état du service"],
    "corrective_actions": ["Redémarrer la base après vérification"],
}


class FakeOllamaClient:
    """Remplace ollama.Client : renvoie des réponses préparées à l'avance, sans appeler de vrai LLM."""

    def __init__(self, answers: list[str]):
        self.answers = answers
        self.calls = []

    def chat(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(message=SimpleNamespace(content=self.answers[len(self.calls) - 1]))


@pytest.fixture
def fake_ollama(monkeypatch):
    def install(answers: list[str]) -> FakeOllamaClient:
        fake = FakeOllamaClient(answers)
        monkeypatch.setattr(llm_client.ollama, "Client", lambda **kwargs: fake)
        return fake

    return install


def test_valid_answer_is_parsed(fake_ollama):
    fake = fake_ollama([json.dumps(VALID_ANSWER)])

    diagnosis = llm_client.diagnose_incident("Message d'erreur : Database unavailable")

    assert diagnosis.severity == "high"
    assert diagnosis.description == "La base de données est injoignable."
    assert len(fake.calls) == 1


def test_request_uses_schema_and_low_temperature(fake_ollama):
    fake = fake_ollama([json.dumps(VALID_ANSWER)])

    llm_client.diagnose_incident("incident")

    call = fake.calls[0]
    assert call["format"] == Diagnosis.model_json_schema()
    assert call["options"]["temperature"] == 0.1
    assert call["messages"][0]["role"] == "system"
    assert "incident" in call["messages"][1]["content"]


def test_invalid_answer_is_retried(fake_ollama):
    fake = fake_ollama(["pas du JSON", json.dumps(VALID_ANSWER)])

    diagnosis = llm_client.diagnose_incident("incident")

    assert diagnosis.severity == "high"
    assert len(fake.calls) == 2


def test_error_after_too_many_invalid_answers(fake_ollama):
    fake_ollama(["pas du JSON", '{"severity": "inconnue"}'])

    with pytest.raises(ValueError, match="invalide"):
        llm_client.diagnose_incident("incident")


def test_duplicates_are_removed():
    diagnosis = Diagnosis(**VALID_ANSWER)

    assert diagnosis.possible_causes == ["Base arrêtée", "Mauvais port"]


def test_empty_lists_are_rejected():
    with pytest.raises(ValueError):
        Diagnosis(**{**VALID_ANSWER, "checks": []})
