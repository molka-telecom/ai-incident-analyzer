# Image légère avec Python 3.11 (même version qu'en local)
FROM python:3.11-slim

# Pas de fichiers .pyc, logs Python affichés immédiatement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 1. Dépendances d'abord : cette couche reste en cache tant que requirements.txt ne change pas
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Puis le code
COPY app/ app/
COPY analyzer/ analyzer/

# Utilisateur sans droits administrateur (bonne pratique de sécurité)
RUN useradd --create-home appuser && mkdir -p logs && chown appuser:appuser logs
USER appuser

EXPOSE 8000

# Docker vérifie régulièrement que l'application répond
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"

# Par défaut : lancer l'application de démo
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
