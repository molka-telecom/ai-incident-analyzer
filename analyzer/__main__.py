import argparse
import json
import logging
from pathlib import Path

from analyzer.agent import run_agent
from analyzer.incidents import extract_incidents
from analyzer.llm_input import format_incident_for_llm, incident_to_dict
from analyzer.log_parser import read_log_file

DEFAULT_LOG_FILE = Path("logs/app.log")


def show_incidents(log_file: Path, as_json: bool) -> None:
    """Tâche 2 : affiche les incidents extraits, sans LLM."""
    entries = read_log_file(log_file)
    incidents = extract_incidents(entries)

    if as_json:
        print(json.dumps([incident_to_dict(incident) for incident in incidents], indent=2, ensure_ascii=False))
        return

    print(f"{len(entries)} lignes lues, {len(incidents)} incident(s) détecté(s)\n")
    for number, incident in enumerate(incidents, start=1):
        print(f"=== Incident {number} ===")
        print(format_incident_for_llm(incident))
        print()


def diagnose(log_file: Path, max_incidents: int, as_json: bool) -> None:
    """Tâche 3 : fait analyser les incidents par l'agent IA."""
    logging.basicConfig(level=logging.INFO, format="[agent] %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)  # masque les logs techniques des requêtes HTTP
    state = run_agent(log_file, max_incidents)

    if as_json:
        output = [
            {
                "incident": incident_to_dict(result.incident),
                "diagnosis": result.diagnosis.model_dump() if result.diagnosis else None,
                "error": result.error,
            }
            for result in state.get("results", [])
        ]
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return

    print()
    print(state["report"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Extrait les incidents d'un fichier de logs et les fait analyser par un LLM.")
    parser.add_argument("--log-file", type=Path, default=DEFAULT_LOG_FILE, help="Chemin du fichier de logs")
    parser.add_argument("--json", action="store_true", help="Affiche le résultat au format JSON")
    parser.add_argument("--diagnose", action="store_true", help="Fait analyser les incidents par le LLM")
    parser.add_argument("--max-incidents", type=int, default=3, help="Nombre maximal d'incidents envoyés au LLM")
    args = parser.parse_args()

    if not args.log_file.exists():
        print(f"Fichier introuvable : {args.log_file}")
        raise SystemExit(1)

    if args.diagnose:
        diagnose(args.log_file, args.max_incidents, args.json)
    else:
        show_incidents(args.log_file, args.json)


if __name__ == "__main__":
    main()
