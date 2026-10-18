import logging
import os
from pathlib import Path

# Dossier logs/ à la racine du projet, sauf si LOG_DIR est défini (ex. dossier temporaire pendant les tests)
LOG_DIR = Path(os.getenv("LOG_DIR", Path(__file__).resolve().parent.parent / "logs"))
LOG_FILE = LOG_DIR / "app.log"

# Format stable : il sera relu et découpé par le parser de la tâche 2
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure le logger 'app' : écriture dans logs/app.log et dans la console."""
    logger = logging.getLogger("app")

    # Évite d'ajouter les handlers deux fois (ex. rechargement automatique d'uvicorn)
    if logger.handlers:
        return logger

    LOG_DIR.mkdir(exist_ok=True)
    formatter = logging.Formatter(LOG_FORMAT)

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.setLevel(level)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False  # n'envoie pas nos logs au logger racine (pas de doublons)

    return logger
