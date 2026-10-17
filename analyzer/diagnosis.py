from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from analyzer.incidents import Incident

MAX_ITEMS = 5


class Diagnosis(BaseModel):
    """Format de réponse imposé au LLM. Le contenu est une hypothèse, pas une certitude."""

    description: str = Field(description="Description courte de l'incident, en une ou deux phrases")
    possible_causes: list[str] = Field(
        min_length=1, description="Causes possibles, de la plus probable à la moins probable"
    )
    severity: Literal["low", "medium", "high", "critical"] = Field(description="Niveau de gravité estimé")
    checks: list[str] = Field(
        min_length=1, description="Vérifications concrètes pour confirmer ou écarter chaque cause"
    )
    corrective_actions: list[str] = Field(
        min_length=1, description="Actions correctives proposées au développeur (jamais exécutées automatiquement)"
    )

    @field_validator("possible_causes", "checks", "corrective_actions")
    @classmethod
    def remove_duplicates(cls, items: list[str]) -> list[str]:
        """Les petits modèles se répètent parfois : on retire les doublons et on limite la longueur."""
        unique_items = list(dict.fromkeys(item.strip() for item in items if item.strip()))
        return unique_items[:MAX_ITEMS]


@dataclass
class IncidentDiagnosis:
    """Un incident et son diagnostic, ou l'erreur rencontrée pendant l'analyse."""

    incident: Incident
    diagnosis: Diagnosis | None = None
    error: str | None = None
