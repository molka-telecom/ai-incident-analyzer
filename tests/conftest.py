import os
import tempfile

# Doit être défini AVANT l'import de l'application :
# les tests écrivent leurs logs dans un dossier temporaire, pas dans le vrai logs/app.log
os.environ["LOG_DIR"] = tempfile.mkdtemp(prefix="test-logs-")
