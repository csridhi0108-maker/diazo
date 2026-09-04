"""
Patient onboarding and profile endpoints. A patient must complete
onboarding (POST /me) before most other features make sense — the
AI plan, risk assessment, and analytics all read from this profile.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_role
from app.models.user import User, UserRole
from app.models.patient_profile import PatientProfile
from app.schemas.patient import PatientOnboarding, PatientProfileOut, PatientProfileUpdate
from app.services.plan_service import generate_plan_for_patient

router = APIRouter(prefix="/api/v1/patients", tags=["patients"])


@router.post("/me", response_model=PatientProfileOut, status_code=status.HTTP_201_CREATED)
def complete_onboarding(
    payload: PatientOnboarding,
    current_user: User = Depends(require_role(UserRole.patient)),
    db: Session = Depends(get_db),
):
    """
    Creates the patient's profile. Only callable by users with the
    'patient' role. Fails if onboarding was already completed.
    """
    existing = (
        db.query(PatientProfile)
        .filter(PatientProfile.user_id == current_user.id)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Onboarding already completed. Use PATCH /me to update your profile.",
        )

    # Extract full_name before dumping the rest to PatientProfile
    profile_data = payload.model_dump()
    full_name = profile_data.pop("full_name", None)

    # Save the name to the User model
    if full_name:
        current_user.full_name = full_name
        db.add(current_user)

    # Save medical data to the PatientProfile model
    profile = PatientProfile(user_id=current_user.id, **profile_data)
    db.add(profile)
    db.commit()
    db.refresh(profile)

    # Generate the initial AI plan immediately
    generate_plan_for_patient(profile, db)

    return profile


@router.get("/me", response_model=PatientProfileOut)
def get_my_profile(
    current_user: User = Depends(require_role(UserRole.patient)),
    db: Session = Depends(get_db),
):
    profile = (
        db.query(PatientProfile)
        .filter(PatientProfile.user_id == current_user.id)
        .first()
    )
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Onboarding not completed yet. POST /me first.",
        )
    
    # FIX: Return ALL fields required by PatientProfileOut schema
    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "full_name": current_user.full_name,
        "diabetes_type": profile.diabetes_type,
        "diagnosis_duration_months": profile.diagnosis_duration_months,
        "sex": profile.sex,
        "age": profile.age,
        "height_cm": profile.height_cm,
        "weight_kg": profile.weight_kg,
        "activity_level": profile.activity_level,
        "medications": profile.medications,
        "dietary_prefs": profile.dietary_prefs,
        "family_history": profile.family_history,
    }


@router.patch("/me", response_model=PatientProfileOut)
def update_my_profile(
    payload: PatientProfileUpdate,
    current_user: User = Depends(require_role(UserRole.patient)),
    db: Session = Depends(get_db),
):
    profile = (
        db.query(PatientProfile)
        .filter(PatientProfile.user_id == current_user.id)
        .first()
    )
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Onboarding not completed yet. POST /me first.",
        )

    updates = payload.model_dump(exclude_unset=True)
    
    # Handle full_name update separately for the User model
    full_name = updates.pop("full_name", None)
    if full_name is not None:
        current_user.full_name = full_name
        db.add(current_user)

    # Update the rest of the PatientProfile fields
    for field, value in updates.items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    
    # FIX: Return ALL fields required by PatientProfileOut schema
    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "full_name": current_user.full_name,
        "diabetes_type": profile.diabetes_type,
        "diagnosis_duration_months": profile.diagnosis_duration_months,
        "sex": profile.sex,
        "age": profile.age,
        "height_cm": profile.height_cm,
        "weight_kg": profile.weight_kg,
        "activity_level": profile.activity_level,
        "medications": profile.medications,
        "dietary_prefs": profile.dietary_prefs,
        "family_history": profile.family_history,
    }