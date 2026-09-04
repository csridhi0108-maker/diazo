"""
Weekly report endpoints — generate a fresh one, view past ones, 
or download a PDF for a doctor's visit.
"""

import io
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_authorized_patient_id
from app.models.report import Report
from app.schemas.report import ReportOut
from app.services.report_service import generate_weekly_report, generate_report_pdf

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.post("/{patient_id}/generate", response_model=ReportOut, status_code=201)
def generate_report(
    patient_id: uuid.UUID = Depends(get_authorized_patient_id),
    db: Session = Depends(get_db),
):
    """Computes and saves a fresh weekly report right now."""
    return generate_weekly_report(db, patient_id)


@router.get("/{patient_id}", response_model=list[ReportOut])
def list_reports(
    patient_id: uuid.UUID = Depends(get_authorized_patient_id),
    db: Session = Depends(get_db),
):
    """Past reports, most recent first."""
    return (
        db.query(Report)
        .filter(Report.patient_id == patient_id)
        .order_by(Report.generated_at.desc())
        .limit(20)
        .all()
    )


@router.get("/{patient_id}/{report_id}/pdf")
def download_report_pdf(
    patient_id: uuid.UUID,
    report_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """
    Downloads a specific report as a PDF file WITH AI INSIGHTS.
    """
    # Security check: ensure the report belongs to this patient
    report = db.query(Report).filter(
        Report.id == report_id, 
        Report.patient_id == patient_id
    ).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found for this patient.")

    # Generate the PDF WITH database access (this is the key fix!)
    pdf_bytes = generate_report_pdf(report, db)

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=DIAZO_Health_Report_{report_id}.pdf"}
    )