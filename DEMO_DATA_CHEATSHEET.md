# DIAZO — Demo Data Cheat Sheet

Goal: log enough data so every insight (Correlation, Adherence, Activity Impact) triggers with a clean result, plus a good-looking glucose chart.

---

## 1. Create ONE demo patient account
Onboard as: Type 2, moderate activity level (gives a mid-range calorie/step target, looks realistic).

---

## 2. Log 10 days of data (not just 7 — some insights use a 30-day window)

### Glucose logs — need 10+ readings, need a REAL carb correlation pattern
Log glucose ~2x per day for 10 days = 20 readings. Alternate deliberately between low-carb and high-carb meals so the correlation is real and clean:

| Day | Meal | Carbs (log in meal) | Glucose ~2hrs later |
|---|---|---|---|
| 1 | Breakfast (oats, low carb) | 25g | 95 |
| 1 | Dinner (rice, high carb) | 75g | 145 |
| 2 | Breakfast (eggs, low carb) | 15g | 90 |
| 2 | Dinner (pasta, high carb) | 80g | 150 |
| 3 | Breakfast (salad, low carb) | 20g | 92 |
| 3 | Dinner (biryani, high carb) | 90g | 155 |
| 4 | Breakfast (low carb) | 20g | 88 |
| 4 | Dinner (high carb) | 85g | 148 |
| 5 | Breakfast (low carb) | 18g | 91 |

**Pattern:** low-carb meals → glucose ~88-95, high-carb meals → glucose ~145-155. This gives a clean, honest ~55-60 mg/dL difference — well above the significance threshold (10), so "Correlation" insight triggers clearly and looks convincing.

### Meal logs — need matching entries for the above
For every glucose reading above, also log the corresponding meal (same day, ~2hrs before) with matching `estimated_carbs`. That's 9-10 meal logs total — gives good "meal adherence" numbers too.

### Activity logs — need 2+ days with step data, ideally a spread
| Day | Steps |
|---|---|
| 1 | 3,000 (low) |
| 2 | 9,000 (high) |
| 3 | 2,500 (low) |
| 4 | 8,500 (high) |
| 5 | 3,200 (low) |

Log at least 5 days like this — gives enough data points for "Activity Impact" to trigger with a real, visible difference (higher steps → noticeably lower glucose that day).

---

## 3. Log across DIFFERENT calendar days, not all in one sitting
The adherence metric counts unique days, not total logs. Spread entries across actual different dates (or manually adjust timestamps if your logging UI allows backdating) — logging 20 entries all "today" will still only count as 1 day of adherence.

**If your UI doesn't support backdating:** log real entries once a day for ~7-10 days in the lead-up to your demo instead of cramming everything at once.

---

## 4. What this gets you for the demo
- **Glucose chart**: a visibly wavy line (not flat), since values alternate 88-95 / 145-155
- **Correlation insight**: "Your average glucose was ~55-60 mg/dL higher after high-carb meals" — clean, dramatic, easy to explain to your panel
- **Adherence**: something like 70-100% if logged daily across the window — looks good
- **Activity Impact**: "Days with more steps had lower glucose" — a second, different kind of insight, shows range
- **Weekly Report**: populated with real numbers, PDF looks complete

---

## 5. Quick minimum version (if short on time)
If you can't spread across real days, the bare minimum for insights to trigger at all:
- 3+ meals, 3+ glucose readings (correlation minimum)
- 2+ matched meal-glucose pairs with a real carb difference
- 1+ day with activity logged (for activity impact — technically works with just 2 days total for the comparison to run, though weak confidence)

But the 10-day spread above gives a genuinely convincing, panel-ready demo rather than a bare-minimum "it works" result.
