import os

# Modifiables par variables d'environnement (utile plus tard avec Docker / Kubernetes)
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "300"))  # secondes ; le modèle est lent sur CPU
