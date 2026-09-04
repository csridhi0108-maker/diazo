"""
DIAZO Weekly Report Service

Responsible for:

1. Computing the deterministic weekly health snapshot.
2. Running the deterministic analytics engine.
3. Passing verified analytics to the explanation layer.
4. Using the LLM ONLY to explain already-computed information.
5. Generating a detailed, professional PDF report.

IMPORTANT ARCHITECTURE RULE:

    Database
        ↓
    Deterministic Analytics
        ↓
    Explain Layer
        ↓
    LLM phrasing
        ↓
    PDF

The LLM never calculates medical statistics, diagnoses conditions,
or invents health information.
"""

import uuid
from datetime import datetime, timedelta, timezone
from io import BytesIO
from xml.sax.saxutils import escape

from sqlalchemy.orm import Session

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
)

from app.models.user import User
from app.models.glucose_log import GlucoseLog
from app.models.meal_log import MealLog
from app.models.activity_log import ActivityLog
from app.models.report import Report

from app.intelligence.analytics_engine import (
    analyze_carb_glucose_correlation,
    analyze_adherence,
    analyze_activity_impact,
    analyze_spike_events,
)

from app.intelligence.explain import (
    build_correlation_insight,
    build_adherence_insight,
    build_activity_insight,
    build_spike_insight,
)

from app.intelligence.llm_explain import phrase_insight


# =========================================================
# CONSTANTS
# =========================================================

REPORT_DAYS = 7

EMERALD = colors.HexColor("#047857")
EMERALD_DARK = colors.HexColor("#065F46")
EMERALD_LIGHT = colors.HexColor("#ECFDF5")
EMERALD_BORDER = colors.HexColor("#A7F3D0")

TEAL = colors.HexColor("#0F766E")

SLATE_900 = colors.HexColor("#111827")
SLATE_700 = colors.HexColor("#374151")
SLATE_600 = colors.HexColor("#4B5563")
SLATE_500 = colors.HexColor("#6B7280")
SLATE_400 = colors.HexColor("#9CA3AF")
SLATE_200 = colors.HexColor("#E5E7EB")
SLATE_100 = colors.HexColor("#F3F4F6")
SLATE_50 = colors.HexColor("#F8FAFC")

WHITE = colors.white


# =========================================================
# SAFE TEXT HELPERS
# =========================================================

def _safe_text(value) -> str:
    """
    Escapes arbitrary text before putting it inside a ReportLab
    Paragraph.
    """
    if value is None:
        return ""

    return escape(str(value))


def _safe_paragraph_text(value) -> str:
    """
    Escapes LLM output so ReportLab does not interpret arbitrary
    LLM-generated text as XML/HTML markup.
    """
    if not value:
        return ""

    return (
        escape(str(value))
        .replace("\n", "<br/>")
    )


# =========================================================
# PAGE NUMBER
# =========================================================

def _draw_page_number(canvas, doc):
    """
    Adds a professional footer to every page.
    """

    canvas.saveState()

    width, _ = letter

    canvas.setStrokeColor(SLATE_200)
    canvas.setLineWidth(0.5)

    canvas.line(
        54,
        38,
        width - 54,
        38,
    )

    canvas.setFont(
        "Helvetica",
        8,
    )

    canvas.setFillColor(
        SLATE_500
    )

    canvas.drawString(
        54,
        25,
        "DIAZO Health Technologies",
    )

    canvas.drawRightString(
        width - 54,
        25,
        f"Page {doc.page}",
    )

    canvas.restoreState()


# =========================================================
# INSIGHT TITLES
# =========================================================

def _insight_title(insight_type: str) -> str:
    titles = {
        "correlation": "Meal & Glucose Pattern",
        "adherence": "Tracking Consistency",
        "activity_impact": "Activity & Glucose Pattern",
        "spike_events": "Specific Glucose Spike Events",
    }

    return titles.get(
        insight_type,
        insight_type.replace("_", " ").title(),
    )


# =========================================================
# CONFIDENCE
# =========================================================

def _confidence_value(insight: dict) -> int:
    try:
        return int(
            round(
                float(
                    insight.get(
                        "confidence_score",
                        0,
                    )
                ) * 100
            )
        )
    except Exception:
        return 0


# =========================================================
# BUILD FRESH WEEKLY INSIGHTS
# =========================================================

def _build_report_insights(
    db: Session,
    patient_id: uuid.UUID,
) -> list[dict]:
    """
    Computes fresh analytics specifically for the weekly report.

    We deliberately DO NOT read old Recommendation rows here.

    This means the PDF always represents the current reporting
    period rather than potentially stale historical recommendations.
    """

    insights = []

    # -----------------------------------------------------
    # 1. CARB / GLUCOSE CORRELATION
    # -----------------------------------------------------

    try:
        correlation_raw = analyze_carb_glucose_correlation(
            db,
            patient_id,
            days=REPORT_DAYS,
        )

        correlation_insight = build_correlation_insight(
            correlation_raw
        )

        if correlation_insight:
            insights.append(
                correlation_insight
            )

    except Exception:
        # Optional insight should never prevent PDF generation.
        pass

    # -----------------------------------------------------
    # 2. ADHERENCE
    # -----------------------------------------------------

    try:
        adherence_raw = analyze_adherence(
            db,
            patient_id,
            days=REPORT_DAYS,
        )

        adherence_insight = build_adherence_insight(
            adherence_raw
        )

        if adherence_insight:
            insights.append(
                adherence_insight
            )

    except Exception:
        pass

    # -----------------------------------------------------
    # 3. ACTIVITY / GLUCOSE
    # -----------------------------------------------------

    try:
        activity_raw = analyze_activity_impact(
            db,
            patient_id,
            days=REPORT_DAYS,
        )

        activity_insight = build_activity_insight(
            activity_raw
        )

        if activity_insight:
            insights.append(
                activity_insight
            )

    except Exception:
        pass

    # -----------------------------------------------------
    # 4. SPECIFIC SPIKE EVENTS
    # -----------------------------------------------------

    try:
        spike_raw = analyze_spike_events(
            db,
            patient_id,
            days=REPORT_DAYS,
            top_n=5,
        )

        spike_insight = build_spike_insight(
            spike_raw
        )

        if spike_insight:
            insights.append(
                spike_insight
            )

    except Exception:
        pass

    return insights


# =========================================================
# WEEKLY SNAPSHOT
# =========================================================

def generate_weekly_report(
    db: Session,
    patient_id: uuid.UUID,
) -> Report:
    """
    Computes and stores a deterministic weekly report snapshot.

    All numerical values are calculated directly from database
    records. The LLM is NOT involved here.
    """

    now = datetime.now(timezone.utc)

    since = now - timedelta(
        days=REPORT_DAYS
    )

    patient = (
        db.query(User)
        .filter(
            User.id == patient_id
        )
        .first()
    )

    # -----------------------------------------------------
    # Fetch logs
    # -----------------------------------------------------

    glucose_logs = (
        db.query(GlucoseLog)
        .filter(
            GlucoseLog.patient_id == patient_id,
            GlucoseLog.timestamp >= since,
            GlucoseLog.timestamp <= now,
        )
        .order_by(
            GlucoseLog.timestamp.asc()
        )
        .all()
    )

    meal_logs = (
        db.query(MealLog)
        .filter(
            MealLog.patient_id == patient_id,
            MealLog.timestamp >= since,
            MealLog.timestamp <= now,
        )
        .order_by(
            MealLog.timestamp.asc()
        )
        .all()
    )

    activity_logs = (
        db.query(ActivityLog)
        .filter(
            ActivityLog.patient_id == patient_id,
            ActivityLog.date >= since.date(),
            ActivityLog.date <= now.date(),
        )
        .order_by(
            ActivityLog.date.asc()
        )
        .all()
    )

    # -----------------------------------------------------
    # Glucose calculations
    # -----------------------------------------------------

    glucose_values = [
        float(log.value)
        for log in glucose_logs
        if log.value is not None
    ]

    avg_glucose = (
        sum(glucose_values) / len(glucose_values)
        if glucose_values
        else 0.0
    )

    min_glucose = (
        min(glucose_values)
        if glucose_values
        else None
    )

    max_glucose = (
        max(glucose_values)
        if glucose_values
        else None
    )

    glucose_days = len(
        {
            log.timestamp.date()
            for log in glucose_logs
            if log.timestamp is not None
        }
    )

    # -----------------------------------------------------
    # Meal calculations
    # -----------------------------------------------------

    meal_days = len(
        {
            log.timestamp.date()
            for log in meal_logs
            if log.timestamp is not None
        }
    )

    meal_count = len(
        meal_logs
    )

    total_carbs = sum(
        float(log.estimated_carbs or 0)
        for log in meal_logs
    )

    # -----------------------------------------------------
    # Activity calculations
    # -----------------------------------------------------

    total_steps = sum(
        int(log.steps or 0)
        for log in activity_logs
    )

    activity_days = len(
        activity_logs
    )

    total_calories_burned = sum(
        float(log.calories_burned or 0)
        for log in activity_logs
    )

    # -----------------------------------------------------
    # Patient information
    # -----------------------------------------------------

    patient_name = (
        getattr(
            patient,
            "full_name",
            None,
        )
        or getattr(
            patient,
            "email",
            "Patient",
        ).split("@")[0]
    )

    patient_weight = getattr(
        patient,
        "weight_kg",
        None,
    )

    # -----------------------------------------------------
    # Save snapshot
    # -----------------------------------------------------

    report = Report(
        patient_id=patient_id,

        # Report model uses DATE columns.
        period_start=since.date(),
        period_end=now.date(),

        generated_at=now,

        summary_data={
            "avg_glucose": round(
                avg_glucose,
                1,
            ),

            "min_glucose": (
                round(
                    min_glucose,
                    1,
                )
                if min_glucose is not None
                else None
            ),

            "max_glucose": (
                round(
                    max_glucose,
                    1,
                )
                if max_glucose is not None
                else None
            ),

            "glucose_readings_count": len(
                glucose_logs
            ),

            "glucose_days_logged": glucose_days,

            "meal_days_logged": meal_days,

            "meal_count": meal_count,

            "total_carbs": round(
                total_carbs,
                1,
            ),

            "activity_days": activity_days,

            "total_steps": total_steps,

            "total_calories_burned": round(
                total_calories_burned,
                1,
            ),

            "patient_weight_kg": patient_weight,

            "patient_name": patient_name,
        },
    )

    db.add(
        report
    )

    db.commit()

    db.refresh(
        report
    )

    return report


# =========================================================
# WEEKLY SUMMARY DATA FOR LLM
# =========================================================

def _build_summary_data(
    data: dict,
    insights: list[dict],
) -> dict:
    """
    Creates the exact structured information supplied to the LLM
    for the weekly overview.

    The LLM is not allowed to calculate anything from these values.
    """

    return {
        "tracking_window_days": REPORT_DAYS,

        "average_glucose_mg_dl": data.get(
            "avg_glucose",
            0,
        ),

        "minimum_glucose_mg_dl": data.get(
            "min_glucose"
        ),

        "maximum_glucose_mg_dl": data.get(
            "max_glucose"
        ),

        "glucose_readings": data.get(
            "glucose_readings_count",
            0,
        ),

        "glucose_days_logged": data.get(
            "glucose_days_logged",
            0,
        ),

        "meal_days_logged": data.get(
            "meal_days_logged",
            0,
        ),

        "meal_count": data.get(
            "meal_count",
            0,
        ),

        "total_carbs_g": data.get(
            "total_carbs",
            0,
        ),

        "activity_days": data.get(
            "activity_days",
            0,
        ),

        "total_steps": data.get(
            "total_steps",
            0,
        ),

        "total_calories_burned": data.get(
            "total_calories_burned",
            0,
        ),

        "available_insight_types": [
            insight.get(
                "insight_type"
            )
            for insight in insights
        ],
    }


# =========================================================
# FALLBACK WEEKLY SUMMARY
# =========================================================

def _build_fallback_summary(
    data: dict,
) -> str:
    """
    Deterministic fallback if Groq is unavailable.
    """

    g_days = data.get(
        "glucose_days_logged",
        0,
    )

    m_days = data.get(
        "meal_days_logged",
        0,
    )

    avg_glucose = data.get(
        "avg_glucose",
        0,
    )

    readings = data.get(
        "glucose_readings_count",
        0,
    )

    steps = data.get(
        "total_steps",
        0,
    )

    meals = data.get(
        "meal_count",
        0,
    )

    if g_days >= 5 and m_days >= 5:

        tracking_text = (
            "Logging consistency was strong this week, "
            "providing a useful data foundation for "
            "personalized pattern analysis."
        )

    elif g_days >= 2 or m_days >= 2:

        tracking_text = (
            "Logging was partial this week. More consistent "
            "daily logging would provide a stronger foundation "
            "for personalized insights."
        )

    else:

        tracking_text = (
            "Very little data was logged this week. More regular "
            "glucose and meal logging would help identify "
            "personal patterns over time."
        )

    return (
        f"{tracking_text} "
        f"The average recorded glucose was "
        f"{avg_glucose:.1f} mg/dL across "
        f"{readings} readings. "
        f"{meals} meals and {steps:,} steps were recorded "
        f"during the reporting period."
    )


# =========================================================
# TABLE HELPER
# =========================================================

def _styled_table(
    data,
    col_widths,
    header_background=EMERALD,
    font_size=9,
):
    """
    Creates a consistent professional table.
    """

    table = Table(
        data,
        colWidths=col_widths,
        repeatRows=1,
        hAlign="LEFT",
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    header_background,
                ),

                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    WHITE,
                ),

                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),

                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    font_size,
                ),

                (
                    "TEXTCOLOR",
                    (0, 1),
                    (-1, -1),
                    SLATE_700,
                ),

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    SLATE_200,
                ),

                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [
                        WHITE,
                        EMERALD_LIGHT,
                    ],
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
            ]
        )
    )

    return table


# =========================================================
# PDF GENERATION
# =========================================================

def generate_report_pdf(
    report: Report,
    db: Session = None,
) -> bytes:
    """
    Generates a comprehensive multi-section weekly PDF.

    Sections:

    1. Report header
    2. Weekly health snapshot
    3. Data coverage
    4. AI weekly overview
    5. Personalized AI insights
    6. Detailed insight evidence
    7. Spike events
    8. Glucose log
    9. Meal log
    10. Activity log
    11. Data interpretation note
    12. Disclaimer
    """

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,

        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54,

        title="DIAZO Weekly Health Report",
        author="DIAZO Health Technologies",
    )

    styles = getSampleStyleSheet()

    elements = []

    # =====================================================
    # STYLES
    # =====================================================

    title_style = ParagraphStyle(
        "DIAZOTitle",
        parent=styles["Heading1"],
        fontSize=24,
        leading=29,
        textColor=EMERALD_DARK,
        spaceAfter=18,
        alignment=TA_CENTER,
    )

    subtitle_style = ParagraphStyle(
        "DIAZOSubtitle",
        parent=styles["Normal"],
        fontSize=11,
        leading=16,
        textColor=SLATE_500,
        alignment=TA_CENTER,
        spaceAfter=20,
    )

    section_style = ParagraphStyle(
        "DIAZOSection",
        parent=styles["Heading2"],
        fontSize=16,
        leading=20,
        textColor=SLATE_900,
        spaceBefore=16,
        spaceAfter=12,
    )

    heading_style = ParagraphStyle(
        "DIAZOHeading",
        parent=styles["Heading3"],
        fontSize=12,
        leading=16,
        textColor=EMERALD_DARK,
        spaceBefore=8,
        spaceAfter=7,
    )

    normal_style = ParagraphStyle(
        "DIAZONormal",
        parent=styles["Normal"],
        fontSize=10.2,
        leading=15,
        textColor=SLATE_700,
        spaceAfter=6,
    )

    small_style = ParagraphStyle(
        "DIAZOSmall",
        parent=styles["Normal"],
        fontSize=8.5,
        leading=12,
        textColor=SLATE_500,
    )

    ai_style = ParagraphStyle(
        "DIAZOAI",
        parent=styles["Normal"],
        fontSize=10.5,
        leading=16,
        textColor=SLATE_700,
        leftIndent=6,
        rightIndent=6,
        spaceAfter=8,
    )

    callout_style = ParagraphStyle(
        "DIAZOCallout",
        parent=styles["Normal"],
        fontSize=10.5,
        leading=16,
        textColor=EMERALD_DARK,
        leftIndent=8,
        rightIndent=8,
    )

    # =====================================================
    # BASIC DATA
    # =====================================================

    data = report.summary_data or {}

    patient_name = data.get(
        "patient_name",
        "Patient",
    )

    # =====================================================
    # FRESH INSIGHTS
    # =====================================================

    insights = []

    if db:

        try:

            insights = _build_report_insights(
                db,
                report.patient_id,
            )

        except Exception:
            insights = []

    # =====================================================
    # PATIENT LANGUAGE
    # =====================================================

    language = "en"

    if db:

        try:

            patient = (
                db.query(User)
                .filter(
                    User.id == report.patient_id
                )
                .first()
            )

            if patient:
                language = (
                    getattr(
                        patient,
                        "preferred_language",
                        None,
                    )
                    or "en"
                )

        except Exception:
            language = "en"

    # =====================================================
    # PAGE 1 — HEADER / SNAPSHOT
    # =====================================================

    elements.append(
        Spacer(1, 20)
    )

    elements.append(
        Paragraph(
            "DIAZO",
            ParagraphStyle(
                "Brand",
                parent=title_style,
                fontSize=30,
                leading=34,
                textColor=EMERALD,
                spaceAfter=5,
            ),
        )
    )

    elements.append(
        Paragraph(
            "Weekly Health Report",
            title_style,
        )
    )

    elements.append(
        Paragraph(
            "Personalized summary of your recorded glucose, "
            "meals, activity, and detected patterns.",
            subtitle_style,
        )
    )

    # -----------------------------------------------------
    # Patient metadata
    # -----------------------------------------------------

    metadata = [
        [
            Paragraph(
                "<b>Patient</b>",
                normal_style,
            ),
            Paragraph(
                _safe_text(patient_name),
                normal_style,
            ),
        ],

        [
            Paragraph(
                "<b>Report Period</b>",
                normal_style,
            ),
            Paragraph(
                f"{report.period_start.strftime('%B %d, %Y')} "
                f"to "
                f"{report.period_end.strftime('%B %d, %Y')}",
                normal_style,
            ),
        ],

        [
            Paragraph(
                "<b>Generated</b>",
                normal_style,
            ),
            Paragraph(
                report.generated_at.strftime(
                    "%B %d, %Y at %I:%M %p"
                ),
                normal_style,
            ),
        ],
    ]

    metadata_table = Table(
        metadata,
        colWidths=[
            130,
            370,
        ],
    )

    metadata_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    EMERALD_LIGHT,
                ),

                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.7,
                    EMERALD_BORDER,
                ),

                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    SLATE_200,
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
            ]
        )
    )

    elements.append(
        metadata_table
    )

    elements.append(
        Spacer(1, 25)
    )

    # =====================================================
    # WEEKLY SNAPSHOT
    # =====================================================

    elements.append(
        Paragraph(
            "1. Weekly Health Snapshot",
            section_style,
        )
    )

    snapshot_data = [
        [
            "Metric",
            "Recorded Value",
        ],

        [
            "Average Glucose",
            f"{data.get('avg_glucose', 0):.1f} mg/dL",
        ],

        [
            "Lowest Recorded Glucose",
            (
                f"{data['min_glucose']:.1f} mg/dL"
                if data.get("min_glucose") is not None
                else "No data"
            ),
        ],

        [
            "Highest Recorded Glucose",
            (
                f"{data['max_glucose']:.1f} mg/dL"
                if data.get("max_glucose") is not None
                else "No data"
            ),
        ],

        [
            "Glucose Readings",
            str(
                data.get(
                    "glucose_readings_count",
                    0,
                )
            ),
        ],

        [
            "Glucose Logging Days",
            f"{data.get('glucose_days_logged', 0)} / {REPORT_DAYS}",
        ],

        [
            "Meal Logging Days",
            f"{data.get('meal_days_logged', 0)} / {REPORT_DAYS}",
        ],

        [
            "Meals Recorded",
            str(
                data.get(
                    "meal_count",
                    0,
                )
            ),
        ],

        [
            "Total Logged Carbohydrates",
            f"{data.get('total_carbs', 0):.1f} g",
        ],

        [
            "Activity Days",
            str(
                data.get(
                    "activity_days",
                    0,
                )
            ),
        ],

        [
            "Total Steps",
            f"{data.get('total_steps', 0):,}",
        ],

        [
            "Calories Burned",
            f"{data.get('total_calories_burned', 0):,.0f}",
        ],
    ]

    if data.get(
        "patient_weight_kg"
    ) is not None:

        snapshot_data.append(
            [
                "Current Weight",
                f"{data['patient_weight_kg']} kg",
            ]
        )

    elements.append(
        _styled_table(
            snapshot_data,
            [
                250,
                250,
            ],
            font_size=9.5,
        )
    )

    elements.append(
        Spacer(1, 20)
    )

    # =====================================================
    # DATA COVERAGE
    # =====================================================

    elements.append(
        Paragraph(
            "2. Tracking Coverage",
            section_style,
        )
    )

    glucose_days = data.get(
        "glucose_days_logged",
        0,
    )

    meal_days = data.get(
        "meal_days_logged",
        0,
    )

    glucose_pct = round(
        (glucose_days / REPORT_DAYS) * 100,
        1,
    )

    meal_pct = round(
        (meal_days / REPORT_DAYS) * 100,
        1,
    )

    coverage_data = [
        [
            "Tracking Type",
            "Days Logged",
            "Coverage",
        ],

        [
            "Glucose",
            f"{glucose_days} / {REPORT_DAYS}",
            f"{glucose_pct}%",
        ],

        [
            "Meals",
            f"{meal_days} / {REPORT_DAYS}",
            f"{meal_pct}%",
        ],

        [
            "Activity",
            str(
                data.get(
                    "activity_days",
                    0,
                )
            ),
            "Recorded days",
        ],
    ]

    elements.append(
        _styled_table(
            coverage_data,
            [
                230,
                140,
                130,
            ],
            font_size=9.5,
        )
    )

    elements.append(
        Spacer(1, 12)
    )

    elements.append(
        Paragraph(
            "Coverage reflects how consistently information was "
            "recorded during the reporting period. More consistent "
            "logging gives DIAZO a stronger data foundation for "
            "identifying recurring personal patterns.",
            normal_style,
        )
    )

    elements.append(
        PageBreak()
    )

    # =====================================================
    # PAGE 2 — AI OVERVIEW
    # =====================================================

    elements.append(
        Paragraph(
            "3. AI-Powered Weekly Overview",
            section_style,
        )
    )

    summary_input = _build_summary_data(
        data,
        insights,
    )

    weekly_summary_insight = {
        "insight_type": "weekly_summary",
        "source_model": "weekly_report",
        "confidence_score": 1.0,
        "raw_data": summary_input,
    }

    weekly_summary = ""

    try:

        weekly_summary = phrase_insight(
            weekly_summary_insight,
            language=language,
            detailed=True,
        )

    except Exception:

        weekly_summary = ""

    if not weekly_summary:

        weekly_summary = _build_fallback_summary(
            data
        )

    overview_table = Table(
        [
            [
                Paragraph(
                    _safe_paragraph_text(
                        weekly_summary
                    ),
                    ai_style,
                )
            ]
        ],
        colWidths=[
            500
        ],
    )

    overview_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    EMERALD_LIGHT,
                ),

                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.8,
                    EMERALD_BORDER,
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    14,
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    14,
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    14,
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    14,
                ),
            ]
        )
    )

    elements.append(
        overview_table
    )

    elements.append(
        Spacer(1, 25)
    )

    # =====================================================
    # PERSONALIZED AI INSIGHTS
    # =====================================================

    elements.append(
        Paragraph(
            "4. Personalized AI Insights",
            section_style,
        )
    )

    elements.append(
        Paragraph(
            "The following observations are generated from the "
            "recorded data for this reporting period. The numerical "
            "values are calculated by DIAZO's deterministic analytics "
            "engine; the AI is used to explain those results in "
            "plain language.",
            normal_style,
        )
    )

    if not insights:

        elements.append(
            Spacer(1, 12)
        )

        elements.append(
            Paragraph(
                "There are not yet enough matching data points to "
                "generate personalized pattern insights for this "
                "reporting period. Continue recording glucose, meals, "
                "and activity to build a stronger data history.",
                callout_style,
            )
        )

    else:

        for index, insight in enumerate(
            insights,
            start=1,
        ):

            insight_type = insight.get(
                "insight_type",
                "insight",
            )

            title = _insight_title(
                insight_type
            )

            confidence = _confidence_value(
                insight
            )

            # -------------------------------------------------
            # Generate detailed LLM explanation
            # -------------------------------------------------

            detailed_text = ""

            try:

                detailed_text = phrase_insight(
                    insight,
                    language=language,
                    detailed=True,
                )

            except Exception:

                detailed_text = ""

            if not detailed_text:

                try:

                    detailed_text = phrase_insight(
                        insight,
                        language=language,
                        detailed=False,
                    )

                except Exception:

                    detailed_text = ""

            if not detailed_text:

                detailed_text = (
                    "This insight is based on the recorded "
                    "data available during the reporting period."
                )

            # -------------------------------------------------
            # Insight heading
            # -------------------------------------------------

            insight_header = Table(
                [
                    [
                        Paragraph(
                            f"<b>{index}. "
                            f"{_safe_text(title)}</b>",
                            heading_style,
                        ),

                        Paragraph(
                            f"<b>{confidence}% confidence</b>",
                            small_style,
                        ),
                    ]
                ],
                colWidths=[
                    365,
                    135,
                ],
            )

            insight_header.setStyle(
                TableStyle(
                    [
                        (
                            "BACKGROUND",
                            (0, 0),
                            (-1, -1),
                            SLATE_50,
                        ),

                        (
                            "BOX",
                            (0, 0),
                            (-1, -1),
                            0.6,
                            SLATE_200,
                        ),

                        (
                            "VALIGN",
                            (0, 0),
                            (-1, -1),
                            "MIDDLE",
                        ),

                        (
                            "ALIGN",
                            (1, 0),
                            (1, 0),
                            "RIGHT",
                        ),

                        (
                            "LEFTPADDING",
                            (0, 0),
                            (-1, -1),
                            10,
                        ),

                        (
                            "RIGHTPADDING",
                            (0, 0),
                            (-1, -1),
                            10,
                        ),

                        (
                            "TOPPADDING",
                            (0, 0),
                            (-1, -1),
                            7,
                        ),

                        (
                            "BOTTOMPADDING",
                            (0, 0),
                            (-1, -1),
                            7,
                        ),
                    ]
                )
            )

            elements.append(
                insight_header
            )

            elements.append(
                Spacer(1, 8)
            )

            # -------------------------------------------------
            # AI explanation
            # -------------------------------------------------

            ai_box = Table(
                [
                    [
                        Paragraph(
                            "<b>AI Interpretation</b>",
                            heading_style,
                        )
                    ],

                    [
                        Paragraph(
                            _safe_paragraph_text(
                                detailed_text
                            ),
                            ai_style,
                        )
                    ],
                ],
                colWidths=[
                    500
                ],
            )

            ai_box.setStyle(
                TableStyle(
                    [
                        (
                            "BACKGROUND",
                            (0, 0),
                            (-1, 0),
                            EMERALD_LIGHT,
                        ),

                        (
                            "BACKGROUND",
                            (0, 1),
                            (-1, 1),
                            WHITE,
                        ),

                        (
                            "BOX",
                            (0, 0),
                            (-1, -1),
                            0.7,
                            EMERALD_BORDER,
                        ),

                        (
                            "LEFTPADDING",
                            (0, 0),
                            (-1, -1),
                            12,
                        ),

                        (
                            "RIGHTPADDING",
                            (0, 0),
                            (-1, -1),
                            12,
                        ),

                        (
                            "TOPPADDING",
                            (0, 0),
                            (-1, -1),
                            8,
                        ),

                        (
                            "BOTTOMPADDING",
                            (0, 0),
                            (-1, -1),
                            8,
                        ),
                    ]
                )
            )

            elements.append(
                ai_box
            )

            elements.append(
                Spacer(1, 10)
            )

            # -------------------------------------------------
            # Deterministic evidence
            # -------------------------------------------------

            raw = (
                insight.get(
                    "raw_data"
                )
                or {}
            )

            evidence = []

            if insight_type == "correlation":

                if raw.get(
                    "high_carb_avg"
                ) is not None:

                    evidence.append(
                        [
                            "Higher-carb group average",
                            f"{raw['high_carb_avg']:.1f} mg/dL",
                        ]
                    )

                if raw.get(
                    "low_carb_avg"
                ) is not None:

                    evidence.append(
                        [
                            "Lower-carb group average",
                            f"{raw['low_carb_avg']:.1f} mg/dL",
                        ]
                    )

                if raw.get(
                    "avg_glucose_increase"
                ) is not None:

                    evidence.append(
                        [
                            "Observed glucose difference",
                            f"{raw['avg_glucose_increase']:.1f} mg/dL",
                        ]
                    )

                if raw.get(
                    "threshold_g"
                ) is not None:

                    evidence.append(
                        [
                            "Carbohydrate threshold",
                            f"{raw['threshold_g']:.1f} g",
                        ]
                    )

                if raw.get(
                    "sample_count"
                ) is not None:

                    evidence.append(
                        [
                            "Data points analyzed",
                            str(
                                raw["sample_count"]
                            ),
                        ]
                    )

            elif insight_type == "adherence":

                evidence = [
                    [
                        "Tracking window",
                        f"{raw.get('window_days', REPORT_DAYS)} days",
                    ],

                    [
                        "Glucose days logged",
                        f"{raw.get('glucose_days_logged', 0)}",
                    ],

                    [
                        "Glucose logging rate",
                        f"{raw.get('glucose_adherence_pct', 0)}%",
                    ],

                    [
                        "Meal days logged",
                        f"{raw.get('meal_days_logged', 0)}",
                    ],

                    [
                        "Meal logging rate",
                        f"{raw.get('meal_adherence_pct', 0)}%",
                    ],
                ]

            elif insight_type == "activity_impact":

                if raw.get(
                    "avg_glucose_high_activity"
                ) is not None:

                    evidence.append(
                        [
                            "Higher-activity average glucose",
                            f"{raw['avg_glucose_high_activity']:.1f} mg/dL",
                        ]
                    )

                if raw.get(
                    "avg_glucose_low_activity"
                ) is not None:

                    evidence.append(
                        [
                            "Lower-activity average glucose",
                            f"{raw['avg_glucose_low_activity']:.1f} mg/dL",
                        ]
                    )

                if raw.get(
                    "glucose_difference"
                ) is not None:

                    evidence.append(
                        [
                            "Observed difference",
                            f"{raw['glucose_difference']:.1f} mg/dL",
                        ]
                    )

                if raw.get(
                    "step_threshold"
                ) is not None:

                    evidence.append(
                        [
                            "Activity threshold",
                            f"{raw['step_threshold']:,} steps",
                        ]
                    )

                if raw.get(
                    "sample_count"
                ) is not None:

                    evidence.append(
                        [
                            "Days analyzed",
                            str(
                                raw["sample_count"]
                            ),
                        ]
                    )

            elif insight_type == "spike_events":

                if raw.get(
                    "baseline_avg_glucose"
                ) is not None:

                    evidence.append(
                        [
                            "Baseline average glucose",
                            f"{raw['baseline_avg_glucose']:.1f} mg/dL",
                        ]
                    )

                if raw.get(
                    "total_spikes_found"
                ) is not None:

                    evidence.append(
                        [
                            "Spike events identified",
                            str(
                                raw["total_spikes_found"]
                            ),
                        ]
                    )

                if raw.get(
                    "sample_count"
                ) is not None:

                    evidence.append(
                        [
                            "Events shown in report",
                            str(
                                raw["sample_count"]
                            ),
                        ]
                    )

            if evidence:

                elements.append(
                    Paragraph(
                        "Supporting Data",
                        heading_style,
                    )
                )

                evidence_table = [
                    [
                        "Measure",
                        "Recorded Value",
                    ]
                ]

                evidence_table.extend(
                    evidence
                )

                elements.append(
                    _styled_table(
                        evidence_table,
                        [
                            330,
                            170,
                        ],
                        font_size=8.8,
                    )
                )

            # -------------------------------------------------
            # Spike event details
            # -------------------------------------------------

            if insight_type == "spike_events":

                events = raw.get(
                    "events"
                ) or []

                if events:

                    elements.append(
                        Paragraph(
                            "Spike Event Details",
                            heading_style,
                        )
                    )

                    spike_table_data = [
                        [
                            "Date",
                            "Meal",
                            "Carbs",
                            "Glucose",
                            "Above Baseline",
                        ]
                    ]

                    for event in events:

                        spike_table_data.append(
                            [
                                _safe_text(
                                    event.get(
                                        "date",
                                        "N/A",
                                    )
                                ),

                                _safe_text(
                                    event.get(
                                        "meal_type",
                                        "N/A",
                                    ).title()
                                ),

                                (
                                    f"{event['carbs_g']:.1f} g"
                                    if event.get(
                                        "carbs_g"
                                    ) is not None
                                    else "N/A"
                                ),

                                (
                                    f"{event['glucose_value']:.1f} mg/dL"
                                    if event.get(
                                        "glucose_value"
                                    ) is not None
                                    else "N/A"
                                ),

                                (
                                    f"{event['deviation_from_baseline']:.1f} mg/dL"
                                    if event.get(
                                        "deviation_from_baseline"
                                    ) is not None
                                    else "N/A"
                                ),
                            ]
                        )

                    elements.append(
                        _styled_table(
                            spike_table_data,
                            [
                                120,
                                100,
                                80,
                                100,
                                100,
                            ],
                            font_size=8,
                        )
                    )

            elements.append(
                Spacer(1, 24)
            )

    # =====================================================
    # INTERPRETATION NOTE
    # =====================================================

    elements.append(
        Paragraph(
            "How to Read These Insights",
            heading_style,
        )
    )

    elements.append(
        Paragraph(
            "These observations describe patterns in the data that "
            "was recorded during this reporting period. A pattern "
            "does not by itself establish a medical cause or diagnosis. "
            "Consistent logging over a longer period can make recurring "
            "patterns easier to identify and discuss with a healthcare "
            "professional.",
            normal_style,
        )
    )

    elements.append(
        PageBreak()
    )

    # =====================================================
    # PAGE 3 — DETAILED LOGS
    # =====================================================

    glucose_logs = []
    meal_logs = []
    activity_logs = []

    if db:

        try:

            # Use the actual report-generation week.
            # period_start / period_end are DATE columns, so create
            # explicit UTC boundaries.

            start_dt = datetime.combine(
                report.period_start,
                datetime.min.time(),
            ).replace(
                tzinfo=timezone.utc
            )

            end_dt = (
                datetime.combine(
                    report.period_end,
                    datetime.min.time(),
                ).replace(
                    tzinfo=timezone.utc
                )
                + timedelta(days=1)
            )

            glucose_logs = (
                db.query(GlucoseLog)
                .filter(
                    GlucoseLog.patient_id == report.patient_id,
                    GlucoseLog.timestamp >= start_dt,
                    GlucoseLog.timestamp < end_dt,
                )
                .order_by(
                    GlucoseLog.timestamp.desc()
                )
                .all()
            )

            meal_logs = (
                db.query(MealLog)
                .filter(
                    MealLog.patient_id == report.patient_id,
                    MealLog.timestamp >= start_dt,
                    MealLog.timestamp < end_dt,
                )
                .order_by(
                    MealLog.timestamp.desc()
                )
                .all()
            )

            activity_logs = (
                db.query(ActivityLog)
                .filter(
                    ActivityLog.patient_id == report.patient_id,
                    ActivityLog.date >= report.period_start,
                    ActivityLog.date <= report.period_end,
                )
                .order_by(
                    ActivityLog.date.desc()
                )
                .all()
            )

        except Exception:
            glucose_logs = []
            meal_logs = []
            activity_logs = []

    # -----------------------------------------------------
    # Glucose Logs
    # -----------------------------------------------------

    elements.append(
        Paragraph(
            "5. Detailed Glucose Log",
            section_style,
        )
    )

    if glucose_logs:

        glucose_table_data = [
            [
                "Date / Time",
                "Glucose",
                "Context",
            ]
        ]

        for log in glucose_logs:

            glucose_table_data.append(
                [
                    log.timestamp.strftime(
                        "%b %d, %I:%M %p"
                    ),

                    (
                        f"{float(log.value):.0f} mg/dL"
                        if log.value is not None
                        else "N/A"
                    ),

                    (
                        log.context_tag
                        .replace(
                            "_",
                            " ",
                        )
                        .title()
                        if log.context_tag
                        else "N/A"
                    ),
                ]
            )

        elements.append(
            _styled_table(
                glucose_table_data,
                [
                    190,
                    150,
                    160,
                ],
                font_size=8.5,
            )
        )

        elements.append(
            Spacer(1, 20)
        )

    else:

        elements.append(
            Paragraph(
                "No glucose readings were recorded during this "
                "reporting period.",
                normal_style,
            )
        )

    # -----------------------------------------------------
    # Meal Logs
    # -----------------------------------------------------

    elements.append(
        Paragraph(
            "6. Detailed Meal Log",
            section_style,
        )
    )

    if meal_logs:

        meal_table_data = [
            [
                "Date / Time",
                "Meal",
                "Carbs",
                "Calories",
            ]
        ]

        for log in meal_logs:

            meal_table_data.append(
                [
                    log.timestamp.strftime(
                        "%b %d, %I:%M %p"
                    ),

                    (
                        log.meal_type.title()
                        if log.meal_type
                        else "N/A"
                    ),

                    (
                        f"{float(log.estimated_carbs):.1f} g"
                        if log.estimated_carbs is not None
                        else "N/A"
                    ),

                    (
                        f"{float(log.estimated_calories):.0f}"
                        if getattr(
                            log,
                            "estimated_calories",
                            None,
                        ) is not None
                        else "N/A"
                    ),
                ]
            )

        elements.append(
            _styled_table(
                meal_table_data,
                [
                    180,
                    130,
                    100,
                    90,
                ],
                font_size=8.5,
            )
        )

        elements.append(
            Spacer(1, 20)
        )

    else:

        elements.append(
            Paragraph(
                "No meal records were recorded during this "
                "reporting period.",
                normal_style,
            )
        )

    # -----------------------------------------------------
    # Activity Logs
    # -----------------------------------------------------

    elements.append(
        Paragraph(
            "7. Detailed Activity Log",
            section_style,
        )
    )

    if activity_logs:

        activity_table_data = [
            [
                "Date",
                "Steps",
                "Calories Burned",
            ]
        ]

        for log in activity_logs:

            activity_table_data.append(
                [
                    str(
                        log.date
                    ),

                    f"{int(log.steps or 0):,}",

                    (
                        f"{float(log.calories_burned):,.0f}"
                        if log.calories_burned is not None
                        else "N/A"
                    ),
                ]
            )

        elements.append(
            _styled_table(
                activity_table_data,
                [
                    180,
                    160,
                    160,
                ],
                font_size=8.5,
            )
        )

    else:

        elements.append(
            Paragraph(
                "No activity records were recorded during this "
                "reporting period.",
                normal_style,
            )
        )

    elements.append(
        Spacer(1, 20)
    )

    # =====================================================
    # DATA QUALITY SECTION
    # =====================================================

    elements.append(
        Paragraph(
            "8. Data Quality & Interpretation",
            section_style,
        )
    )

    data_quality_points = []

    if glucose_days < REPORT_DAYS:

        data_quality_points.append(
            f"Glucose readings were recorded on "
            f"{glucose_days} of {REPORT_DAYS} days."
        )

    else:

        data_quality_points.append(
            "Glucose readings were recorded across the full "
            "reporting window."
        )

    if meal_days < REPORT_DAYS:

        data_quality_points.append(
            f"Meal records were recorded on "
            f"{meal_days} of {REPORT_DAYS} days."
        )

    else:

        data_quality_points.append(
            "Meal records were available across the full "
            "reporting window."
        )

    if len(glucose_logs) < 3:

        data_quality_points.append(
            "The glucose sample size is limited, so pattern "
            "detection may be restricted."
        )

    if len(meal_logs) < 3:

        data_quality_points.append(
            "The meal sample size is limited, so meal-related "
            "pattern detection may be restricted."
        )

    if len(activity_logs) < 2:

        data_quality_points.append(
            "Activity data is limited for this reporting period."
        )

    for point in data_quality_points:

        elements.append(
            Paragraph(
                f"• {_safe_text(point)}",
                normal_style,
            )
        )

    # =====================================================
    # FINAL PAGE — DISCLAIMER
    # =====================================================

    elements.append(
        PageBreak()
    )

    elements.append(
        Spacer(1, 40)
    )

    elements.append(
        Paragraph(
            "DIAZO Weekly Health Report",
            title_style,
        )
    )

    elements.append(
        Paragraph(
            "Important Information",
            section_style,
        )
    )

    disclaimer_box = Table(
        [
            [
                Paragraph(
                    """
                    <b>Educational and informational use only.</b><br/><br/>
                    This report summarizes information recorded in the
                    DIAZO application and presents patterns identified
                    by its deterministic analytics and language model.
                    It is not intended to diagnose, treat, cure, or
                    prevent any medical condition.<br/><br/>
                    The AI-generated explanations describe only the
                    information supplied to the system and should not
                    be interpreted as medical advice. Any health
                    concerns or changes in treatment should be discussed
                    with an appropriately qualified healthcare
                    professional.
                    """,
                    normal_style,
                )
            ]
        ],
        colWidths=[
            500
        ],
    )

    disclaimer_box.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    SLATE_50,
                ),

                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.8,
                    SLATE_200,
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    16,
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    16,
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    16,
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    16,
                ),
            ]
        )
    )

    elements.append(
        disclaimer_box
    )

    elements.append(
        Spacer(1, 30)
    )

    elements.append(
        Paragraph(
            "Generated by DIAZO Health Technologies",
            ParagraphStyle(
                "FinalFooter",
                parent=small_style,
                alignment=TA_CENTER,
            ),
        )
    )

    # =====================================================
    # BUILD
    # =====================================================

    doc.build(
        elements,
        onFirstPage=_draw_page_number,
        onLaterPages=_draw_page_number,
    )

    pdf_bytes = buffer.getvalue()

    buffer.close()

    return pdf_bytes