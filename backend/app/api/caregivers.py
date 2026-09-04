"""
Caregiver/doctor <-> patient linking endpoints. Covers request,
approve/revoke, and listing — the consent mechanism that makes
CareLink.status == approved actually get set.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_role
from app.models.user import User, UserRole
from app.models.caregiver_link import CareLink, LinkStatus
from app.schemas.caregiver import LinkRequestCreate, LinkRespond

router = APIRouter(prefix="/api/v1/caregivers", tags=["caregivers"])


@router.post("/link-request", status_code=status.HTTP_201_CREATED)
def create_link_request(
    payload: LinkRequestCreate,
    current_user: User = Depends(require_role(UserRole.caregiver, UserRole.doctor)),
    db: Session = Depends(get_db),
):
    """
    A caregiver or doctor requests access to a patient by email.
    Creates a 'pending' link — no access is granted until the patient
    approves it via PATCH /link-request/{link_id}.
    """
    patient = db.query(User).filter(
        User.email == payload.patient_email, User.role == UserRole.patient
    ).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No patient found with that email",
        )

    existing = db.query(CareLink).filter(
        CareLink.linked_user_id == current_user.id,
        CareLink.patient_id == patient.id,
        CareLink.status != LinkStatus.revoked,
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A link request already exists for this patient (pending or approved)",
        )

    link = CareLink(
        linked_user_id=current_user.id,
        patient_id=patient.id,
        link_type=payload.link_type,
        status=LinkStatus.pending,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    
    return {
        "id": link.id,
        "patient_email": patient.email,
        "patient_name": patient.full_name,
        "status": link.status.value,
        "message": "Request sent successfully. Waiting for patient approval."
    }


@router.get("/link-requests/pending")
def list_pending_requests(
    current_user: User = Depends(require_role(UserRole.patient)),
    db: Session = Depends(get_db),
):
    """Patient views their own pending link requests, to decide
    whether to approve or reject each."""
    links = (
        db.query(CareLink)
        .filter(CareLink.patient_id == current_user.id, CareLink.status == LinkStatus.pending)
        .all()
    )
    
    # Enrich with caregiver details so the patient knows who is asking
    result = []
    for link in links:
        caregiver = db.query(User).filter(User.id == link.linked_user_id).first()
        result.append({
            "link_id": link.id,
            "caregiver_email": caregiver.email if caregiver else "Unknown",
            "caregiver_name": caregiver.full_name if caregiver else "Unknown Caregiver",
            "link_type": link.link_type.value,
            "created_at": link.created_at,
        })
    return result


@router.patch("/link-request/{link_id}")
def respond_to_link_request(
    link_id: uuid.UUID,
    payload: LinkRespond,
    current_user: User = Depends(require_role(UserRole.patient)),
    db: Session = Depends(get_db),
):
    """
    The consent step. Only the patient the link is FOR can approve or
    revoke it.
    """
    link = db.query(CareLink).filter(CareLink.id == link_id).first()
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link request not found")
    if link.patient_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only respond to link requests made for you",
        )

    link.status = LinkStatus.approved if payload.approve else LinkStatus.revoked
    link.responded_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(link)
    return {
        "link_id": link.id,
        "status": link.status.value,
        "message": "Link approved." if payload.approve else "Link revoked."
    }


@router.get("/my-patients")
def list_my_patients(
    current_user: User = Depends(require_role(UserRole.caregiver, UserRole.doctor)),
    db: Session = Depends(get_db),
):
    """
    A caregiver/doctor's list of approved patient links.
    Enriched with patient name/email for the dashboard UI.
    """
    links = (
        db.query(CareLink)
        .filter(CareLink.linked_user_id == current_user.id, CareLink.status == LinkStatus.approved)
        .all()
    )
    
    result = []
    for link in links:
        patient = db.query(User).filter(User.id == link.patient_id).first()
        result.append({
            "link_id": link.id,
            "patient_id": link.patient_id,
            "patient_email": patient.email if patient else "Unknown",
            "patient_name": patient.full_name if patient else "Unknown Patient",
            "link_type": link.link_type.value,
            "status": link.status.value,
            "created_at": link.created_at,
        })
    return result