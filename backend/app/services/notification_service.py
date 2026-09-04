"""
Creates notifications for a patient's linked, approved caregivers/doctors.
"""

import uuid

from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationType
from app.models.caregiver_link import CareLink, LinkStatus
from app.core.ws_manager import manager


async def notify_linked_caregivers(
    db: Session,
    patient_id: uuid.UUID,
    notification_type: NotificationType,
    message: str,
) -> list[Notification]:
    
    # Try to get patient name safely
    patient_name = "A patient"
    try:
        from app.models.user import User
        patient = db.query(User).filter(User.id == patient_id).first()
        if patient and hasattr(patient, 'full_name') and patient.full_name:
            patient_name = patient.full_name
    except Exception as e:
        print(f"Could not fetch patient name: {e}")
        pass
    
    # Replace "This patient" with actual name
    final_message = message.replace("This patient", patient_name)

    links = (
        db.query(CareLink)
        .filter(CareLink.patient_id == patient_id, CareLink.status == LinkStatus.approved)
        .all()
    )

    created = []
    for link in links:
        notification = Notification(
            recipient_id=link.linked_user_id,
            patient_id=patient_id,
            type=notification_type,
            message=final_message,
        )
        db.add(notification)
        created.append(notification)

    db.commit()
    for n in created:
        db.refresh(n)
        await manager.push_to_user(n.recipient_id, {
            "id": str(n.id),
            "type": n.type.value,
            "message": n.message,
            "patient_id": str(n.patient_id),
            "created_at": n.created_at.isoformat(),
        })

    return created