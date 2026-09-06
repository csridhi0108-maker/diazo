"""
FastAPI application entrypoint. Wires together CORS, routers, and
(for local dev only) table creation. In staging/production, schema
changes should go through Alembic migrations instead of create_all —
see alembic/env.py once that's set up.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app.api import caregiver_dashboard

# Import every model so Base.metadata knows about all tables before
# create_all runs. Without these imports, SQLAlchemy has no way of
# knowing these tables exist yet, even though Base is shared.
from app.models import user, patient_profile, caregiver_link, meal_log, glucose_log, activity_log, ai_plan, recommendation, notification, report, meal_weight_reading, food_item, scale_status  # noqa: F401
from app.api import auth, patients, plans, ml, caregivers, notifications_ws, dashboard, admin, reports, hardware, glucose_logs, nutrition, log
from app.core.ws_manager import ws_router
from app.scheduler.jobs import start_scheduler

app = FastAPI(
    title="DIAZO API",
    description="AI-assisted diabetes tracking and management platform",
    version="0.1.0",
)

# CORS: only the frontend origin(s) listed in .env are allowed to call
# this API from a browser. Tighten CORS_ORIGINS in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route registration — each new api/*.py router gets included here as
# it's built (caregivers, plans, ml, reports, admin,
# notifications_ws all still to come).
app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(log.router)
app.include_router(plans.router)
app.include_router(ml.router)
app.include_router(caregivers.router)
app.include_router(notifications_ws.router)
app.include_router(dashboard.router)
app.include_router(admin.router)
app.include_router(reports.router)
app.include_router(hardware.router)
app.include_router(ws_router)
app.include_router(glucose_logs.router)
app.include_router(caregiver_dashboard.router)
app.include_router(nutrition.router)


@app.on_event("startup")
def on_startup():
    """
    Dev-only convenience: creates any tables that don't exist yet,
    based on the currently imported models. This is NOT a substitute
    for Alembic — once the schema stabilizes, migrations should be
    the only way tables change, so this call can be removed or left
    as a harmless no-op (create_all skips tables that already exist).
    """
    if settings.ENVIRONMENT == "development":
        Base.metadata.create_all(bind=engine)

    start_scheduler()


@app.get("/health")
def health_check():
    """Simple liveness check — useful for Render's health check config
    and for confirming the API is up before testing anything else."""
    return {"status": "ok"}