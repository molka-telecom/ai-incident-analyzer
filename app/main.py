import logging

from fastapi import FastAPI, HTTPException

from app.logging_config import setup_logging

setup_logging()
logger = logging.getLogger("app.main")

app = FastAPI(
    title="AI Incident Analyzer - Demo App",
    description="Application de démonstration qui génère des logs et simule des incidents.",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict:
    """Vérifie que l'application fonctionne."""
    logger.info("Health check OK")
    return {"status": "ok"}


@app.get("/error/500")
def simulate_internal_error() -> dict:
    """Simule un bug dans le code de l'application (HTTP 500)."""
    try:
        items_count = 0
        average_price = 100 / items_count  # bug volontaire : division par zéro
    except ZeroDivisionError as exc:
        logger.error("Internal server error while computing order total: %s: %s", type(exc).__name__, exc)
        raise HTTPException(status_code=500, detail="Internal server error")
    return {"average_price": average_price}


@app.get("/error/503")
def simulate_service_unavailable() -> dict:
    """Simule une base de données injoignable (HTTP 503)."""
    logger.warning("Database connection attempt failed, retrying (host=db, port=5432)")
    logger.error("Database unavailable: connection refused (host=db, port=5432)")
    raise HTTPException(status_code=503, detail="Service unavailable")


@app.get("/error/504")
def simulate_timeout() -> dict:
    """Simule un service externe qui ne répond pas à temps (HTTP 504)."""
    logger.warning("Slow response from payment-service (> 3s)")
    logger.error("Timeout: payment-service did not respond within 5s")
    raise HTTPException(status_code=504, detail="Gateway timeout")
