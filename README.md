# AI Incident Analyzer — Generative AI & DevOps

Outil qui analyse automatiquement les logs d'une application, détecte les erreurs et utilise un LLM local pour proposer un diagnostic (causes possibles, gravité, vérifications, actions correctives).

> Le diagnostic est une **hypothèse à vérifier**, jamais une certitude. Aucune action corrective n'est appliquée automatiquement.

## Architecture (cible)

```
Application de démo (app/)  ──►  logs/app.log  ──►  Analyseur de logs  ──►  Agent IA (Ollama + LangGraph)  ──►  Diagnostic
```

- **Application de démo** : petite API FastAPI qui simule un service et ses pannes, et écrit des logs.
- **AI Incident Analyzer** (`analyzer/`) : lit les logs, extrait et regroupe les erreurs, puis les fait analyser par un LLM *(LLM à venir)*.

## État d'avancement

- [x] Tâche 1 — Application de démo et génération des logs
- [x] Tâche 2 — Collecte et analyse des logs
- [ ] Tâche 3 — Agent IA (Ollama + LangGraph)
- [ ] Tâche 4 — Docker
- [ ] Tâche 5 — Tests et CI (pytest, GitHub Actions)
- [ ] Tâche 6 — Kubernetes
- [ ] Tâche 7 — Supervision (Prometheus, Grafana)

## Prérequis

- Python 3.11+
- Windows (PowerShell), Linux ou macOS

## Installation

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1        # Linux/macOS : source .venv/bin/activate
pip install -r requirements.txt
```

## Lancement

```powershell
uvicorn app.main:app --reload
```

Documentation interactive : http://127.0.0.1:8000/docs

## Routes de l'application de démo

| Route        | Code | Simulation                          | Logs écrits      |
|--------------|------|-------------------------------------|------------------|
| `/health`    | 200  | Application opérationnelle          | INFO             |
| `/error/500` | 500  | Bug dans le code (division par zéro) | ERROR            |
| `/error/503` | 503  | Base de données injoignable         | WARNING + ERROR  |
| `/error/504` | 504  | Service de paiement trop lent       | WARNING + ERROR  |

## Format des logs

Les logs sont écrits dans `logs/app.log` (et dans la console) :

```
2026-10-17 20:09:23,739 | ERROR | app.main | Database unavailable: connection refused (host=db, port=5432)
```

Format : `date | niveau | module | message`.

## Extraction des incidents

```powershell
python -m analyzer                          # résumé des incidents (texte destiné au LLM)
python -m analyzer --json                   # même résultat au format JSON
python -m analyzer --log-file autre.log     # analyser un autre fichier
```

Étapes : lecture et découpage des lignes → filtrage des `ERROR`/`CRITICAL` → regroupement des erreurs identiques (nombre d'occurrences, première et dernière apparition) → ajout du contexte (jusqu'à 3 `WARNING` précédant l'erreur).

Exemple de sortie :

```
=== Incident 2 ===
Niveau : ERROR
Source : app.main
Message d'erreur : Database unavailable: connection refused (host=db, port=5432)
Occurrences : 2 (du 2026-10-17 20:09:23 au 2026-10-17 23:34:43)
Logs précédant l'erreur :
- WARNING Database connection attempt failed, retrying (host=db, port=5432)
```

## Structure du projet

```
ai-incident-analyzer/
├── app/                    # Application de démo (génère les logs)
│   ├── __init__.py
│   ├── logging_config.py   # configuration des logs (fichier + console)
│   └── main.py             # API FastAPI et routes simulant des erreurs
├── analyzer/               # AI Incident Analyzer
│   ├── __init__.py
│   ├── __main__.py         # commande : python -m analyzer
│   ├── log_parser.py       # lecture et découpage des lignes de log
│   ├── incidents.py        # filtrage, regroupement et contexte des erreurs
│   └── llm_input.py        # mise en forme des incidents pour le LLM
├── logs/                   # app.log (généré, non versionné)
├── requirements.txt
└── README.md
```
