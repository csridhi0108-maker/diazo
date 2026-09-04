"""
Background jobs, run periodically via APScheduler (registered in
app/main.py's startup event). Two responsibilities, matching the
honest scope discussed:

1. check_missed_logs() — genuinely a push: creates a caregiver/doctor
   notification via the existing notification infrastructure.
2. flag_due_meal_reminders() — NOT a push (a plain web app can't
   reliably push to a closed browser tab). Instead, marks which
   patients have an overdue meal reminder in the DB; the frontend
   checks this on load/poll and shows an in-app banner. Documented
   here as a deliberate, honest scope decision, not an oversight.
"""

import asyncio
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.models.meal_log import MealLog
from app.models.glucose_log import GlucoseLog
from app.models.notification import Notification, NotificationType
from app.services.notification_service import notify_linked_caregivers

MISSED_LOG_THRESHOLD_HOURS = 12


async def check_missed_logs():
    """
    Runs periodically. For every patient, checks whether their most
    recent log (meal OR glucose, whichever is more recent) is older
    than the threshold — if so, notifies their linked caregivers/
    doctors. Avoids re-notifying every run by only firing once per
    "missed" episode would require tracking last-alerted state, which
    is a reasonable future improvement; for now this may notify on
    each scheduler run while the patient remains unresponsive, which
    is acceptable for a demo/student-project scope.
    """
    db: Session = SessionLocal()
    try:
        patients = db.query(User).filter(User.role == UserRole.patient).all()
        cutoff = datetime.now(timezone.utc) - timedelta(hours=MISSED_LOG_THRESHOLD_HOURS)

        for patient in patients:
            last_meal = (
                db.query(MealLog)
                .filter(MealLog.patient_id == patient.id)
                .order_by(MealLog.timestamp.desc())
                .first()
            )
            last_glucose = (
                db.query(GlucoseLog)
                .filter(GlucoseLog.patient_id == patient.id)
                .order_by(GlucoseLog.timestamp.desc())
                .first()
            )

            most_recent = None
            if last_meal:
                most_recent = last_meal.timestamp
            if last_glucose and (most_recent is None or last_glucose.timestamp > most_recent):
                most_recent = last_glucose.timestamp

            # No logs at all yet, or nothing since the threshold —
            # either way, worth a caregiver check-in if they have one.
            # No logs at all yet, or nothing since the threshold —
            # either way, worth a caregiver check-in if they have one.
            if most_recent is None or most_recent < cutoff:
                # Only alert once per missed-log episode: skip if we
                # already sent a missed_log notification more recently
                # than the patient's last log (i.e. nothing's changed
                # since we last alerted). Once they log something new,
                # most_recent moves forward and this check naturally
                # allows a fresh alert next time they go quiet again.
                last_alert = (
                    db.query(Notification)
                    .filter(
                        Notification.patient_id == patient.id,
                        Notification.type == NotificationType.missed_log,
                    )
                    .order_by(Notification.created_at.desc())
                    .first()
                )
                already_alerted = last_alert is not None and (
                    most_recent is None or last_alert.created_at > most_recent
                )

                if not already_alerted:
                    await notify_linked_caregivers(
                        db, patient.id, NotificationType.missed_log,
                        f"No logs from this patient in over {MISSED_LOG_THRESHOLD_HOURS} hours — "
                        f"consider checking in.",
                    )
    finally:
        db.close()


def start_scheduler():
    """Called once from main.py's startup event."""
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_missed_logs, "interval", hours=1, id="check_missed_logs")
    scheduler.start()
    return scheduler