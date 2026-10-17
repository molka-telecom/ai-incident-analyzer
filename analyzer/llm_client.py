import ollama
from pydantic import ValidationError

from analyzer.config import OLLAMA_HOST, OLLAMA_MODEL, OLLAMA_TIMEOUT
from analyzer.diagnosis import Diagnosis

SYSTEM_PROMPT = """Tu es un ingénieur SRE expérimenté qui aide un développeur à analyser un incident à partir de ses logs.

Règles :
- Réponds uniquement en français, au format JSON demandé.
- Les causes sont des hypothèses à vérifier, jamais des certitudes.
- Base-toi uniquement sur les informations fournies et n'invente pas de détails absents des logs.
- Sois concis : 2 à 4 éléments par liste, sans répéter deux fois la même idée.
- Les vérifications servent à confirmer ou écarter une cause (commandes, configuration, métriques à consulter).
- Les actions correctives sont différentes des vérifications : ce sont les corrections à appliquer
  une fois la cause confirmée. Ce sont des propositions pour le développeur, jamais destructives :
  pas de suppression de données, pas de modification en production sans vérification préalable.

Niveaux de gravité :
- low : aucun impact visible pour les utilisateurs
- medium : impact limité ou ponctuel
- high : une fonctionnalité importante est indisponible
- critical : le service entier est indisponible ou des données sont perdues"""

MAX_ATTEMPTS = 2


def diagnose_incident(incident_text: str) -> Diagnosis:
    """Envoie un incident au LLM et renvoie son diagnostic structuré."""
    client = ollama.Client(host=OLLAMA_HOST, timeout=OLLAMA_TIMEOUT)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Analyse cet incident :\n\n{incident_text}"},
    ]

    last_error = None
    for _ in range(MAX_ATTEMPTS):
        response = client.chat(
            model=OLLAMA_MODEL,
            messages=messages,
            format=Diagnosis.model_json_schema(),  # force le LLM à répondre dans ce format JSON
            options={"temperature": 0.1},  # réponses plus stables et moins « créatives »
        )
        try:
            return Diagnosis.model_validate_json(response.message.content)
        except ValidationError as exc:
            last_error = exc

    raise ValueError(f"Réponse du LLM invalide après {MAX_ATTEMPTS} tentatives : {last_error}")
