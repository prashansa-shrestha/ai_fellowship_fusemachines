# app/main.py
from fastapi import FastAPI
from app.database import engine, Base
from app import router
from app.logger import get_logger

logger = get_logger(__name__)

# Create all tables (if they don't already exist)
# Since you use seed.sql, this is a safety net
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Customer API",
    description="REST API for managing customers, orders, and payments",
    version="1.0.0"
)

app.include_router(router.counts_router)

# New: dashboard endpoint
app.include_router(router.dashboard_router)

# Register the router with the app
app.include_router(router.router)


@app.get("/health")
def health_check():
    """Simple endpoint to verify the API is running."""
    logger.info("Health check called")
    return {"status": "ok"}