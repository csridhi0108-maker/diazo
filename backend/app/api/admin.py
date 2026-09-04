"""
Admin endpoints — account/link oversight and management.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.dependencies import require_role
from app.models.user import User, UserRole
from app.models.caregiver_link import CareLink, LinkStatus
from app.schemas.admin import AssignCaregiverRequest

# Import models needed for cascade deletion to prevent foreign key errors
from app.models.glucose_log import GlucoseLog
from app.models.meal_log import MealLog
from app.models.activity_log import ActivityLog
from app.models.patient_profile import PatientProfile
from app.models.notification import Notification
from app.models.report import Report
from app.models.ai_plan import AIPlan
from app.models.recommendation import Recommendation
from app.models.meal_weight_reading import MealWeightReading

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.get("/users")
def list_all_users(
    _: None = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    users = db.query(User).order_by(User.created_at.desc()).limit(200).all()
    return [
        {
            "id": str(u.id),
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role.value if hasattr(u.role, 'value') else str(u.role),
            "created_at": u.created_at.isoformat() if u.created_at else None
        }
        for u in users
    ]


@router.get("/links")
def list_all_links(
    _: None = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    """All caregiver/doctor <-> patient links, enriched with user details for visibility."""
    links = db.query(CareLink).order_by(CareLink.created_at.desc()).limit(200).all()
    
    result = []
    for link in links:
        caregiver = db.query(User).filter(User.id == link.linked_user_id).first()
        patient = db.query(User).filter(User.id == link.patient_id).first()
        
        result.append({
            "id": str(link.id),
            "linked_user_id": str(link.linked_user_id),
            "patient_id": str(link.patient_id),
            "link_type": link.link_type,
            "status": link.status.value if hasattr(link.status, 'value') else str(link.status),
            "created_at": link.created_at.isoformat() if link.created_at else None,
            "caregiver_email": caregiver.email if caregiver else "Unknown",
            "caregiver_name": caregiver.full_name if caregiver else "Unknown",
            "patient_email": patient.email if patient else "Unknown",
            "patient_name": patient.full_name if patient else "Unknown",
        })
    return result


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_user(
    user_id: uuid.UUID,
    _: None = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Prevent deleting the last admin
    if user.role == UserRole.admin:
        admin_count = db.query(func.count(User.id)).filter(User.role == UserRole.admin).scalar()
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="Cannot delete the last admin account")

    # Cascade delete associated records to prevent Foreign Key constraint errors
    # Order matters: delete child records before parent records
    
    # 1. Notifications
    db.query(Notification).filter(Notification.recipient_id == user_id).delete(synchronize_session=False)
    db.query(Notification).filter(Notification.patient_id == user_id).delete(synchronize_session=False)
    
    # 2. Care Links (both as caregiver and as patient)
    db.query(CareLink).filter(CareLink.linked_user_id == user_id).delete(synchronize_session=False)
    db.query(CareLink).filter(CareLink.patient_id == user_id).delete(synchronize_session=False)
    
    # 3. Patient-specific data
    db.query(MealWeightReading).filter(MealWeightReading.patient_id == user_id).delete(synchronize_session=False)
    db.query(Report).filter(Report.patient_id == user_id).delete(synchronize_session=False)
    db.query(Recommendation).filter(Recommendation.patient_id == user_id).delete(synchronize_session=False)
    db.query(AIPlan).filter(AIPlan.patient_id == user_id).delete(synchronize_session=False)
    db.query(ActivityLog).filter(ActivityLog.patient_id == user_id).delete(synchronize_session=False)
    db.query(MealLog).filter(MealLog.patient_id == user_id).delete(synchronize_session=False)
    db.query(GlucoseLog).filter(GlucoseLog.patient_id == user_id).delete(synchronize_session=False)
    
    # 4. Patient Profile (if it exists)
    db.query(PatientProfile).filter(PatientProfile.user_id == user_id).delete(synchronize_session=False)
    
    # 5. Finally, delete the user
    db.delete(user)
    db.commit()
    
    return None


@router.delete("/links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_care_link(
    link_id: uuid.UUID,
    _: None = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    link = db.query(CareLink).filter(CareLink.id == link_id).first()
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    
    db.delete(link)
    db.commit()


@router.post("/assign-link", status_code=status.HTTP_201_CREATED)
def assign_caregiver(
    request: AssignCaregiverRequest,
    _: None = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    """Admin can directly link a caregiver to a patient (bypasses consent)."""
    caregiver = db.query(User).filter(User.id == request.caregiver_id).first()
    if not caregiver or caregiver.role not in [UserRole.caregiver, UserRole.doctor]:
        raise HTTPException(status_code=400, detail="Invalid caregiver ID or role")
    
    patient = db.query(User).filter(User.id == request.patient_id, User.role == UserRole.patient).first()
    if not patient:
        raise HTTPException(status_code=400, detail="Invalid patient ID")
    
    existing = db.query(CareLink).filter(
        CareLink.linked_user_id == request.caregiver_id,
        CareLink.patient_id == request.patient_id
    ).first()
    
    if existing:
        existing.status = LinkStatus.approved
        db.commit()
        db.refresh(existing)
        return {"id": str(existing.id), "message": "Link updated to approved"}

    new_link = CareLink(
        linked_user_id=request.caregiver_id,
        patient_id=request.patient_id,
        link_type=request.link_type,
        status=LinkStatus.approved,
    )
    db.add(new_link)
    db.commit()
    db.refresh(new_link)
    
    return {"id": str(new_link.id), "message": "Caregiver successfully linked to patient"}


@router.get("/stats")
def get_system_stats(
    _: None = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    total_users = db.query(func.count(User.id)).scalar()
    by_role = dict(db.query(User.role, func.count(User.id)).group_by(User.role).all())
    total_links = db.query(func.count(CareLink.id)).scalar()
    approved_links = db.query(func.count(CareLink.id)).filter(CareLink.status == LinkStatus.approved).scalar()
    pending_links = db.query(func.count(CareLink.id)).filter(CareLink.status == LinkStatus.pending).scalar()

    return {
        "total_users": total_users or 0,
        "users_by_role": {str(role.value) if hasattr(role, 'value') else str(role): count for role, count in by_role.items()},
        "total_care_links": total_links or 0,
        "approved_links": approved_links or 0,
        "pending_links": pending_links or 0,
    }