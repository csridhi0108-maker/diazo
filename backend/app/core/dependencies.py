"""
Reusable FastAPI dependencies for authentication and authorization.
Every protected route uses one of these via Depends(...) instead of
re-implementing token checks or permission logic inline.

This is the single place that enforces:
  - "is this a valid, logged-in user?"          -> get_current_user
  - "is this user a patient/caregiver/etc?"      -> require_role(...)
  - "is this caregiver/doctor actually approved
     to view this specific patient's data?"       -> get_authorized_patient_id
"""

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User, UserRole
from app.models.caregiver_link import CareLink, LinkStatus

# Tells FastAPI where a client should POST credentials to get a token
# (used only for the auto-generated Swagger UI "Authorize" button —
# the actual login logic lives in api/auth.py).
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Decodes the JWT from the Authorization header, loads the
    corresponding User from the DB, and returns it. Raises 401 if the
    token is missing/invalid/expired, or the user no longer exists.
    Every other dependency below builds on top of this one.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
    if user is None:
        raise credentials_exception

    return user


def require_role(*allowed_roles: UserRole):
    """
    Factory that builds a dependency restricting a route to specific
    roles. Usage: Depends(require_role(UserRole.admin))
    or for multiple: Depends(require_role(UserRole.caregiver, UserRole.doctor))
    """

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return current_user

    return role_checker


def get_authorized_patient_id(
    patient_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> uuid.UUID:
    """
    The core consent-enforcement dependency. Confirms the requesting
    user is allowed to read this specific patient's data:
      - the patient themself, OR
      - a caregiver/doctor with an APPROVED CareLink to this patient.
    Used on every route under /logs, /plans, /ml, /reports that takes
    a patient_id — this is what makes caregiver access read-only and
    consent-gated in practice, not just in the spec.
    """
    if current_user.role == UserRole.patient and current_user.id == patient_id:
        return patient_id

    if current_user.role in (UserRole.caregiver, UserRole.doctor):
        link = (
            db.query(CareLink)
            .filter(
                CareLink.linked_user_id == current_user.id,
                CareLink.patient_id == patient_id,
                CareLink.status == LinkStatus.approved,
            )
            .first()
        )
        if link is not None:
            return patient_id

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not authorized to access this patient's data",
    )