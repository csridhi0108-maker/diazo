"""
Emergency SOS: one-button alert from patient to all linked caregivers
and doctors, bypassing normal notification rules — always immediate,
always high-priority. Reuses the same Notification model/service as
meal-logged alerts, just with type=emergency.

Also includes basic notification-reading endpoints for the
caregiver/doctor side (mark as read, list mine) since notifications
without a way to view them aren't useful.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.notification import Notification, NotificationType
from app.schemas.notification import NotificationOut
from app.services.notification_service import notify_linked_caregivers

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


@router.post("/emergency", response_model=list[NotificationOut], status_code=status.HTTP_201_CREATED)
async def trigger_emergency_sos(
    current_user: User = Depends(require_role(UserRole.patient)),
    db: Session = Depends(get_db),
):
    """
    Patient-triggered emergency alert. No request body needed — this
    is deliberately a single action, not a form, since a real
    emergency shouldn't require filling anything in. Notifies every
    approved caregiver/doctor linked to this patient immediately.
    """
    notifications = await notify_linked_caregivers(
        db, current_user.id, NotificationType.emergency,
        "EMERGENCY ALERT: This patient has triggered an emergency SOS. Please check on them immediately.",
    )
    if not notifications:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No linked caregivers or doctors to notify. Please link a caregiver first.",
        )
    return notifications


@router.get("/mine", response_model=list[NotificationOut])
def list_my_notifications(
    current_user: User = Depends(require_role(UserRole.caregiver, UserRole.doctor)),
    db: Session = Depends(get_db),
):
    """Caregiver/doctor's own notification feed, most recent first."""
    return (
        db.query(Notification)
        .filter(Notification.recipient_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(100)
        .all()
    )


@router.patch("/{notification_id}/read", response_model=NotificationOut)
def mark_notification_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(require_role(UserRole.caregiver, UserRole.doctor)),
    db: Session = Depends(get_db),
):
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    if notification.recipient_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your notification")

    notification.read = True
    db.commit()
    db.refresh(notification)
    return notification