import argparse
import json
from pathlib import Path

from analyzer.incidents import extract_incidents
from analyzer.llm_input import format_incident_for_llm, incident_to_dict
from analyzer.log_parser import read_log_file

DEFAULT_LOG_FILE = Path("logs/app.log")


def main() -> None:
    parser = argparse.ArgumentParser(description="Extrait les incidents d'un fichier de logs.")
    parser.add_argument("--log-file", type=Path, default=DEFAULT_LOG_FILE, help="Chemin du fichier de logs")
    parser.add_argument("--json", action="store_true", help="Affiche les incidents au format JSON")
    args = parser.parse_args()

    if not args.log_file.exists():
        print(f"Fichier introuvable : {args.log_file}")
        raise SystemExit(1)

    entries = read_log_file(args.log_file)
    incidents = extract_incidents(entries)

    if args.json:
        print(json.dumps([incident_to_dict(incident) for incident in incidents], indent=2, ensure_ascii=False))
        return

    print(f"{len(entries)} lignes lues, {len(incidents)} incident(s) détecté(s)\n")
    for number, incident in enumerate(incidents, start=1):
        print(f"=== Incident {number} ===")
        print(format_incident_for_llm(incident))
        print()


if __name__ == "__main__":
    main()
