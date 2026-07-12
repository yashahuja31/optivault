from fastapi import FastAPI

from app.config import settings
from app.database import Base, engine
from app.routers import auth, cloud_accounts

app = FastAPI(
    title="OptiVault API",
    description="AI-driven cloud storage cost optimizer",
    version="0.1.0",
)

app.include_router(auth.router)
app.include_router(cloud_accounts.router)


@app.on_event("startup")
def on_startup():
    # In staging/production, schema changes are applied via Alembic
    # migrations (see backend/alembic/) as part of the deploy pipeline.
    # create_all here is purely a local-dev convenience so `docker compose
    # up` gives you a working DB with zero extra steps -- it's a no-op
    # once Alembic-managed tables already exist.
    if settings.environment == "local":
        Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check():
    return {"status": "ok"}
