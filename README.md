# AI Incident Analyzer — Generative AI & DevOps

Outil qui analyse automatiquement les logs d'une application, détecte les erreurs et utilise un LLM local pour proposer un diagnostic (causes possibles, gravité, vérifications, actions correctives).

> Le diagnostic est une **hypothèse à vérifier**, jamais une certitude. Aucune action corrective n'est appliquée automatiquement.

## Architecture (cible)

```
Application de démo (app/)  ──►  logs/app.log  ──►  Analyseur de logs  ──►  Agent IA (Ollama + LangGraph)  ──►  Diagnostic
```

- **Application de démo** : petite API FastAPI qui simule un service et ses pannes, et écrit des logs.
- **AI Incident Analyzer** (`analyzer/`) : lit les logs, extrait et regroupe les erreurs, puis les fait analyser par un LLM local (Ollama) via un workflow LangGraph.

## État d'avancement

- [x] Tâche 1 — Application de démo et génération des logs
- [x] Tâche 2 — Collecte et analyse des logs
- [x] Tâche 3 — Agent IA (Ollama + LangGraph)
- [x] Tâche 4 — Docker
- [ ] Tâche 5 — Tests et CI (pytest, GitHub Actions)
- [ ] Tâche 6 — Kubernetes
- [ ] Tâche 7 — Supervision (Prometheus, Grafana)

## Prérequis

- Python 3.11+
- Windows (PowerShell), Linux ou macOS
- [Ollama](https://ollama.com) lancé localement, avec le modèle `qwen2.5:3b` (`ollama pull qwen2.5:3b`)

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

## Diagnostic par l'agent IA

```powershell
python -m analyzer --diagnose                    # analyse les 3 incidents les plus fréquents
python -m analyzer --diagnose --max-incidents 1  # plus rapide
python -m analyzer --diagnose --json             # résultat au format JSON
```

Workflow LangGraph :

```
START → collect_incidents ─┬─ incidents trouvés → diagnose_incidents → build_report → END
                           └─ aucun incident ───────────────────────→ build_report → END
```

- Le LLM est contraint de répondre dans un format JSON précis (schéma Pydantic `Diagnosis`) : description, causes possibles, gravité (`low` / `medium` / `high` / `critical`), vérifications, actions correctives.
- Réponse invalide → nouvelle tentative (2 au maximum). Échec sur un incident → les autres sont quand même analysés.
- Le diagnostic est présenté comme une hypothèse. **Aucune action n'est exécutée** : l'agent propose, le développeur décide.

Configuration (variables d'environnement) :

| Variable         | Défaut                   | Rôle                                  |
|------------------|--------------------------|---------------------------------------|
| `OLLAMA_HOST`    | `http://127.0.0.1:11434` | Adresse du serveur Ollama             |
| `OLLAMA_MODEL`   | `qwen2.5:3b`             | Modèle utilisé                        |
| `OLLAMA_TIMEOUT` | `300`                    | Délai maximal d'une réponse (secondes) |

Exemple de résultat (extrait) :

```
=== Incident 2 : Database unavailable: connection refused (host=db, port=5432) ===
Occurrences : 2
Gravité estimée : Moyenne
Description : L'incident est lié à une impossibilité de se connecter à la base de données.
Causes possibles (hypothèses à vérifier) :
  1. La base de données est hors ligne ou indisponible.
  2. Le serveur de base de données est en maintenance.
  3. La configuration de la base de données a été modifiée, ce qui a affecté la connexion.
Vérifications recommandées :
  - Vérifier la disponibilité du serveur de base de données.
  - Vérifier la configuration de la base de données (port, nom d'hôte, etc.).
```

Sur un PC portable sans GPU dédié (i5-1235U), l'analyse de 3 incidents prend environ 1 à 2 minutes.

## Docker

Prérequis : Docker Desktop démarré, Ollama lancé sur la machine hôte.

```powershell
docker compose build                          # construire l'image
docker compose up -d                          # lancer l'application de démo (http://127.0.0.1:8000/docs)
docker compose ps                             # état du conteneur (doit être "healthy")
docker compose logs -f demo-app               # suivre les logs du conteneur
docker compose run --rm analyzer              # lancer l'agent IA sur logs/app.log
docker compose down                           # tout arrêter
```

- Une seule image (`ai-incident-analyzer`) sert aux deux services : `demo-app` (API) et `analyzer` (agent, lancé à la demande).
- Le dossier `logs/` du PC est monté dans les conteneurs : l'API y écrit, l'agent le lit en **lecture seule**.
- Ollama reste sur la machine hôte (modèle déjà téléchargé, meilleures performances) ; le conteneur l'atteint via `host.docker.internal`.
- Le conteneur tourne avec un utilisateur non-root et possède un `HEALTHCHECK` sur `/health`.
- Port déjà utilisé (ex. uvicorn lancé en local) ? Choisir un autre port : `$env:APP_PORT="8001"; docker compose up -d`.
- Le fuseau horaire des conteneurs est réglé par `TZ` (défaut `Europe/Paris`), sinon les logs seraient en UTC.

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
│   ├── llm_input.py        # mise en forme des incidents pour le LLM
│   ├── config.py           # configuration Ollama (variables d'environnement)
│   ├── diagnosis.py        # format de réponse imposé au LLM (Pydantic)
│   ├── llm_client.py       # appel à Ollama et prompt système
│   ├── agent.py            # workflow LangGraph
│   └── report.py           # mise en forme du rapport final
├── logs/                   # app.log (généré, non versionné)
├── Dockerfile              # image Python de l'application
├── .dockerignore           # fichiers exclus de l'image
├── docker-compose.yml      # services demo-app et analyzer
├── requirements.txt
└── README.md
```
