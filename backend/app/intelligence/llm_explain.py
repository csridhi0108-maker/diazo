"""
LLM Explanation Layer

The ONLY file in this codebase that calls the LLM (Groq).

Architecture:

    analytics_engine.py
            ↓
       explain.py
            ↓
     llm_explain.py
            ↓
    Recommendation / Report

The analytics engine is responsible for calculating numbers.

The explain layer is responsible for structuring those calculations.

This file is responsible ONLY for converting verified structured
results into clear, patient-friendly language.

The LLM must NEVER:
- calculate new statistics
- modify provided numbers
- diagnose conditions
- provide medication/treatment instructions
- invent missing information
- infer unsupported medical causes
"""


import json
import logging

from groq import Groq

from app.core.config import settings


logger = logging.getLogger(__name__)


# =========================================================
# GROQ CLIENT INITIALIZATION
# =========================================================

try:
    api_key = settings.clean_groq_api_key

    if api_key and api_key.strip():
        client = Groq(api_key=api_key)

        logger.info(
            "Groq client initialized successfully."
        )

    else:
        client = None

        logger.warning(
            "Groq API key is empty. "
            "Using deterministic fallback text."
        )

except Exception as e:

    client = None

    logger.error(
        f"Failed to initialize Groq client: {e}"
    )


# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are the patient-friendly health communication assistant
inside a diabetes tracking application called DIAZO.

Your job is ONLY to explain structured information that has
already been calculated by the application's deterministic
analytics engine.

You are NOT the analytics engine.

You MUST NOT:

- calculate statistics
- perform arithmetic
- modify numbers
- round numbers differently
- invent missing values
- fill gaps with assumptions
- diagnose diseases or medical conditions
- prescribe medication
- recommend medication changes
- give treatment instructions
- claim that one factor medically caused another
- invent medical explanations
- create facts that are not present in the structured data

You MUST:

- use only information supplied in the structured data
- preserve supplied numbers exactly
- clearly explain observed patterns
- use simple, patient-friendly language
- be compassionate and non-judgmental
- distinguish observations from medical advice
- mention when the available sample is limited
- use metric units when supplied
- personalize the explanation using the patient's actual
  logged information

---------------------------------------------------------
DASHBOARD INSIGHTS
---------------------------------------------------------

For normal dashboard recommendations:

- Maximum 3 short sentences.
- Focus on the most important observation.
- Keep the language concise and easy to understand.
- Do not overwhelm the patient with every available number.

---------------------------------------------------------
WEEKLY REPORT
---------------------------------------------------------

For detailed weekly-report explanations:

- Write 3 to 6 concise sentences.
- Explain the important patterns in the supplied data.
- Use specific numbers when they are available.
- Mention relevant dates, meals, glucose readings, activity
  levels, adherence, and spike events when supplied.
- Explain multiple different insights rather than repeating
  the same observation.
- Keep the explanation useful and personalized.
- Do not introduce information that is not present in the data.

---------------------------------------------------------
CARBOHYDRATE / GLUCOSE CORRELATION
---------------------------------------------------------

When explaining carbohydrate correlation:

- Use the supplied high-carb average.
- Use the supplied low-carb average.
- Use the supplied glucose difference.
- Use the supplied carbohydrate threshold.
- Mention the sample count when useful.
- Describe this as an observed pattern or association.
- Do NOT claim that carbohydrates caused the glucose change.

Preferred language:

"Your logged data showed..."

"The readings in the higher-carb group were..."

"An association was observed..."

Avoid:

"Carbohydrates caused your glucose to..."

---------------------------------------------------------
ACTIVITY / GLUCOSE
---------------------------------------------------------

When explaining activity:

- Mention the step threshold when available.
- Mention the glucose averages when useful.
- Mention the observed glucose difference.
- Mention the number of days/data points when available.
- Describe this as an observed association.
- Do not claim that exercise caused the glucose change.

---------------------------------------------------------
ADHERENCE
---------------------------------------------------------

For adherence:

- Explicitly use glucose_days_logged.
- Explicitly use meal_days_logged.
- Explicitly use window_days.
- Explicitly use glucose_adherence_pct.
- Explicitly use meal_adherence_pct.
- Never invent missing logging days.

---------------------------------------------------------
SPIKE EVENTS
---------------------------------------------------------

Spike events are specific observations from the patient's
logged data.

For each event, use the supplied:

- date
- meal_type
- carbs_g
- glucose_value
- deviation_from_baseline
- baseline_avg_glucose when available

Describe the event as something that was:

"recorded after"

"observed following"

"seen in the logged data after"

Do NOT say:

"the meal caused the spike"

"carbohydrates caused the spike"

"this means you have..."

Do not turn a spike event into a diagnosis.

---------------------------------------------------------
LIMITED DATA
---------------------------------------------------------

If the structured data contains a small sample count or limited
number of days, acknowledge that the observation is based on
limited logged data.

Do not invent a statistical significance calculation.

---------------------------------------------------------
LANGUAGE
---------------------------------------------------------

Respond entirely in the requested language.

The supported application languages are:

- English
- Hindi
- Telugu

Preserve numerical values and units even when translating.

---------------------------------------------------------
SAFETY
---------------------------------------------------------

This application provides educational lifestyle information.

It is NOT a substitute for professional medical advice.
"""


# =========================================================
# MAIN LLM FUNCTION
# =========================================================

def phrase_insight(
    insight: dict,
    language: str = "en",
    detailed: bool = False,
) -> str:
    """
    Convert a structured deterministic insight into
    patient-friendly language.

    Parameters
    ----------
    insight:
        Structured insight produced by explain.py.

    language:
        Requested output language.

    detailed:
        False:
            Short dashboard recommendation.

        True:
            More detailed explanation suitable for the
            weekly PDF report.

    The LLM is never allowed to perform calculations.
    """

    raw_data = (
        insight.get("raw_data")
        or {}
    )

    # -----------------------------------------------------
    # Groq unavailable
    # -----------------------------------------------------

    if not client:

        return _fallback_phrasing(
            insight,
            detailed=detailed,
        )

    # -----------------------------------------------------
    # Response mode
    # -----------------------------------------------------

    if detailed:

        response_instruction = """
This is being used inside a detailed weekly health report.

Write 3 to 6 concise sentences.

Explain the important information contained in the structured
data.

Where available, include:

- specific dates
- glucose values
- glucose averages
- meal types
- carbohydrate amounts
- activity levels
- step thresholds
- adherence counts
- adherence percentages
- spike deviations
- baseline glucose
- sample counts

Do not simply repeat the same sentence in different words.

Instead, connect the supplied observations into a coherent
personalized explanation.

Do NOT calculate anything yourself.
"""

        max_tokens = 350

    else:

        response_instruction = """
This is a dashboard recommendation.

Write no more than 3 short sentences.

Focus on the most useful observation.

Do not overwhelm the patient with unnecessary details.
"""

        max_tokens = 180

    # -----------------------------------------------------
    # Build user prompt
    # -----------------------------------------------------

    user_prompt = f"""
Insight Type:
{insight.get("insight_type", "unknown")}

Source Model:
{insight.get("source_model", "unknown")}

Confidence:
{insight.get("confidence_score", 0) * 100:.0f}%

Structured Data:
{json.dumps(raw_data, indent=2, default=str)}

Requested Language:
{language}

Detailed Mode:
{detailed}

{response_instruction}

IMPORTANT RULES:

1. Preserve every supplied number exactly.
2. Do not calculate new numbers.
3. Do not round numbers differently.
4. Do not invent missing values.
5. Do not diagnose.
6. Do not provide medication advice.
7. Do not provide treatment instructions.
8. Do not claim unsupported causation.
9. Only use information in Structured Data.
10. Return ONLY the patient-facing explanation.

---------------------------------------------------------
DATA-SPECIFIC INSTRUCTIONS
---------------------------------------------------------

For adherence insights, use:

- glucose_days_logged
- meal_days_logged
- window_days
- glucose_adherence_pct
- meal_adherence_pct

For activity insights, use:

- avg_glucose_high_activity
- avg_glucose_low_activity
- glucose_difference
- step_threshold
- sample_count

For correlation insights, use:

- avg_glucose_increase
- high_carb_avg
- low_carb_avg
- threshold_g
- sample_count

For spike_events, use:

- baseline_avg_glucose
- events
- total_spikes_found
- sample_count

For every spike event, when present, preserve:

- date
- timestamp
- meal_type
- carbs_g
- glucose_value
- deviation_from_baseline
- context_tag

Do not omit important specific events in detailed mode.

---------------------------------------------------------
PERSONALIZATION
---------------------------------------------------------

Use the patient's actual logged data to make the explanation
specific.

For example, if the data contains:

date = Friday, Aug 21
meal_type = lunch
carbs_g = 120
glucose_value = 160
deviation_from_baseline = 22.1

the explanation should refer to that specific logged event.

Do NOT generalize it into a generic statement about diet.

---------------------------------------------------------
LIMITED DATA
---------------------------------------------------------

If sample_count is small, communicate that the observation is
based on the available logged data.

Do not invent statistical significance.

---------------------------------------------------------
FINAL OUTPUT
---------------------------------------------------------

Return ONLY the patient-facing explanation.

Do not return:

- JSON
- bullet-point analysis
- internal reasoning
- confidence calculations
- headings such as "Analysis"
- disclaimers unless specifically appropriate
"""


    # =====================================================
    # CALL GROQ
    # =====================================================

    try:

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",

            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],

            temperature=0.3,

            max_tokens=max_tokens,
        )

        text = (
            response
            .choices[0]
            .message
            .content
            .strip()
        )

        if text:
            return text

    except Exception as e:

        logger.error(
            f"Groq API call failed: {e}"
        )

    # -----------------------------------------------------
    # Deterministic fallback
    # -----------------------------------------------------

    return _fallback_phrasing(
        insight,
        detailed=detailed,
    )


# =========================================================
# DETERMINISTIC FALLBACK
# =========================================================

def _fallback_phrasing(
    insight: dict,
    detailed: bool = False,
) -> str:
    """
    Deterministic fallback used when Groq is unavailable.

    IMPORTANT:

    This function uses ONLY values already present in raw_data.

    It does not calculate or infer new medical information.
    """

    data = (
        insight.get("raw_data")
        or {}
    )

    insight_type = (
        insight.get("insight_type")
    )

    # =====================================================
    # CORRELATION
    # =====================================================

    if insight_type == "correlation":

        diff = (
            data.get(
                "avg_glucose_increase"
            )
            if data.get(
                "avg_glucose_increase"
            ) is not None
            else data.get(
                "glucose_difference"
            )
        )

        threshold = (
            data.get(
                "threshold_g"
            )
            if data.get(
                "threshold_g"
            ) is not None
            else data.get(
                "high_carb_threshold_g"
            )
        )

        samples = (
            data.get(
                "sample_count"
            )
            if data.get(
                "sample_count"
            ) is not None
            else data.get(
                "sample_size"
            )
        )

        high_avg = data.get(
            "high_carb_avg"
        )

        low_avg = data.get(
            "low_carb_avg"
        )

        # -------------------------------------------------
        # Detailed correlation
        # -------------------------------------------------

        if detailed:

            parts = []

            if high_avg is not None:

                parts.append(
                    f"Readings following meals in the "
                    f"higher-carb group averaged "
                    f"{high_avg} mg/dL."
                )

            if low_avg is not None:

                parts.append(
                    f"Readings in the lower-carb group "
                    f"averaged {low_avg} mg/dL."
                )

            if diff is not None:

                parts.append(
                    f"The observed difference between "
                    f"the groups was {diff} mg/dL."
                )

            if threshold is not None:

                parts.append(
                    f"The higher-carb group used a "
                    f"{threshold} g carbohydrate threshold."
                )

            if samples is not None:

                parts.append(
                    f"This analysis included {samples} "
                    f"matched readings."
                )

            return " ".join(parts)

        # -------------------------------------------------
        # Short correlation
        # -------------------------------------------------

        if (
            diff is not None
            and threshold is not None
        ):

            text = (
                f"Your logged data showed an average "
                f"glucose difference of {diff} mg/dL "
                f"between the higher- and lower-carb "
                f"groups using a {threshold}g threshold"
            )

            if samples is not None:

                text += (
                    f", based on {samples} readings."
                )

            else:

                text += "."

            return text

    # =====================================================
    # ADHERENCE
    # =====================================================

    if insight_type == "adherence":

        g_days = (
            data.get(
                "glucose_days_logged"
            )
            if data.get(
                "glucose_days_logged"
            ) is not None
            else data.get(
                "days_with_glucose_log",
                0,
            )
        )

        m_days = (
            data.get(
                "meal_days_logged"
            )
            if data.get(
                "meal_days_logged"
            ) is not None
            else data.get(
                "days_with_meal_log",
                0,
            )
        )

        g_pct = data.get(
            "glucose_adherence_pct",
            0,
        )

        m_pct = data.get(
            "meal_adherence_pct",
            0,
        )

        window = data.get(
            "window_days",
            7,
        )

        if detailed:

            return (
                f"Glucose readings were logged on "
                f"{g_days} out of {window} days "
                f"({g_pct}%), while meals were logged "
                f"on {m_days} out of {window} days "
                f"({m_pct}%). This logging history "
                f"provides the available data for "
                f"identifying patterns during the "
                f"reporting period."
            )

        return (
            f"This week, you logged glucose on "
            f"{g_days} out of {window} days "
            f"({g_pct}%) and meals on {m_days} "
            f"days ({m_pct}%). Try to log regularly "
            f"to unlock deeper insights."
        )

    # =====================================================
    # ACTIVITY
    # =====================================================

    if insight_type == "activity_impact":

        high_avg = data.get(
            "avg_glucose_high_activity"
        )

        low_avg = data.get(
            "avg_glucose_low_activity"
        )

        diff = data.get(
            "glucose_difference"
        )

        threshold = data.get(
            "step_threshold"
        )

        samples = data.get(
            "sample_count"
        )

        if detailed:

            parts = []

            if threshold is not None:

                parts.append(
                    f"The activity comparison used "
                    f"a threshold of {threshold} steps."
                )

            if high_avg is not None:

                parts.append(
                    f"The higher-activity group had "
                    f"an average glucose of "
                    f"{high_avg} mg/dL."
                )

            if low_avg is not None:

                parts.append(
                    f"The lower-activity group had "
                    f"an average glucose of "
                    f"{low_avg} mg/dL."
                )

            if diff is not None:

                parts.append(
                    f"The observed glucose difference "
                    f"was {diff} mg/dL."
                )

            if samples is not None:

                parts.append(
                    f"The comparison included "
                    f"{samples} days."
                )

            return " ".join(parts)

        if (
            diff is not None
            and threshold is not None
        ):

            return (
                f"On days with more than {threshold} "
                f"steps, your average glucose was "
                f"{diff} mg/dL lower."
            )

    # =====================================================
    # SPIKE EVENTS
    # =====================================================

    if insight_type == "spike_events":

        baseline = data.get(
            "baseline_avg_glucose"
        )

        events = (
            data.get("events")
            or []
        )

        total_spikes = data.get(
            "total_spikes_found"
        )

        if not events:

            return (
                "No specific glucose spike events "
                "were identified from the available "
                "logged data."
            )

        # -------------------------------------------------
        # Detailed spike report
        # -------------------------------------------------

        if detailed:

            parts = []

            if baseline is not None:

                parts.append(
                    f"Your average glucose baseline "
                    f"for this analysis was "
                    f"{baseline} mg/dL."
                )

            if total_spikes is not None:

                parts.append(
                    f"The analysis identified "
                    f"{total_spikes} specific glucose "
                    f"spike event"
                    f"{'s' if total_spikes != 1 else ''}."
                )

            for event in events:

                date = event.get(
                    "date",
                    "an unspecified date",
                )

                meal_type = event.get(
                    "meal_type",
                    "meal",
                )

                carbs = event.get(
                    "carbs_g"
                )

                glucose = event.get(
                    "glucose_value"
                )

                deviation = event.get(
                    "deviation_from_baseline"
                )

                context_tag = event.get(
                    "context_tag"
                )

                event_text = (
                    f"On {date}, a glucose reading "
                    f"of {glucose} mg/dL was recorded "
                    f"following {meal_type}"
                )

                if carbs is not None:

                    event_text += (
                        f" containing {carbs} g "
                        f"of carbohydrates"
                    )

                if deviation is not None:

                    event_text += (
                        f"; this was {deviation} mg/dL "
                        f"above the recorded baseline"
                    )

                if context_tag == "after_meal":

                    event_text += (
                        " and the reading was tagged "
                        "as after-meal."
                    )

                else:

                    event_text += "."

                parts.append(
                    event_text
                )

            return " ".join(parts)

        # -------------------------------------------------
        # Short dashboard spike insight
        # -------------------------------------------------

        first_event = events[0]

        date = first_event.get(
            "date",
            "a recent date",
        )

        meal_type = first_event.get(
            "meal_type",
            "meal",
        )

        glucose = first_event.get(
            "glucose_value"
        )

        carbs = first_event.get(
            "carbs_g"
        )

        deviation = first_event.get(
            "deviation_from_baseline"
        )

        if (
            glucose is not None
            and deviation is not None
        ):

            text = (
                f"A glucose spike was recorded "
                f"on {date} following {meal_type}"
            )

            if carbs is not None:

                text += (
                    f" ({carbs}g carbs)"
                )

            text += (
                f", reaching {glucose} mg/dL, "
                f"which was {deviation} mg/dL "
                f"above your recorded baseline."
            )

            return text

        return (
            "A specific glucose spike was identified "
            "in your recent logged data."
        )

    # =====================================================
    # WEEKLY SUMMARY
    # =====================================================

    if insight_type == "weekly_summary":

        return (
            "Your weekly health summary is based on "
            "the glucose, meal, and activity data "
            "recorded during the reporting period."
        )

    # =====================================================
    # GENERIC FALLBACK
    # =====================================================

    return (
        f"Insight generated for {insight_type} "
        f"based on your recent logged data."
    )