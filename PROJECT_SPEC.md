# DIAZO — Project Specification (Frozen)

Diabetes tracking and management web app for patients and their family caregivers, with AI-driven personalized insights and risk assessment.

---

## 1. Final Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React.js (Vite), Tailwind CSS |
| Backend | FastAPI (Python) |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Database | PostgreSQL (Neon) |
| Authentication | JWT + OAuth2 Password Flow + bcrypt |
| AI/ML | Scikit-learn (primary), PyTorch (optional — forecasting) |
| LLM | Groq API (explanation phrasing only) |
| API Documentation | Swagger UI (built into FastAPI) |
| Deployment | Vercel (frontend), Render (backend) |
| Version Control | Git & GitHub |

---

## 2. Features

### Phase 1 — Authentication & Onboarding
- Email-based sign-up/login
- Roles: Patient, Caregiver, Admin
- Patient onboarding: diabetes type (Type 1/Type 2/Prediabetic/None), diagnosis duration, age, height, weight, activity level, medications (context only), dietary preferences, family history
- Caregiver onboarding: link via invite code or patient email
- Patient must approve caregiver link request (consent step)
- One caregiver can be linked to multiple patients (many-to-many)

### Phase 2 — AI-Generated Personalized Plan
- Calculated from onboarding data: target weight (if applicable), daily calorie/macro targets, baseline diet + activity routine, daily step goal
- Plan adjusts over time based on logged data

### Phase 3 — Daily Tracking
- Meal reminders (scheduled, repeat until logged) with caregiver notification on completion
- Activity tracking: steps, calories burned, vs. AI-set goal
- Meal logging: searchable food list + manual macro entry (photo-based estimation is a stretch goal)
- Glucose logging: manual entry, tagged with meal-context (before/after meal, etc.)

### Phase 4 — Analytics, ML & Recommendations
- **Analytics Engine**: deterministic trend/correlation/adherence detection from logs (pandas)
- **ML models** (optional layer): glucose correlation regression (scikit-learn), diabetes risk classification for non-diagnosed users (scikit-learn), glucose forecasting (PyTorch — stretch)
- **LLM (Groq)**: converts structured analytics/ML output into plain-language explanations only — never computes numbers or makes independent medical claims
- Every recommendation is traceable to the underlying data that produced it

### Phase 5 — Caregiver Dashboard
- Real-time notifications (meal logged, missed log) via WebSocket
- Read-only access to linked patients' trends (glucose, adherence, weight)
- Missed-log alert if patient hasn't logged in X hours
- Patient switcher (for caregivers linked to multiple patients)

### Phase 6 — Admin Dashboard
- View/manage users, caregiver-patient links
- Basic system stats
- Minimal scope — account/link oversight only

### Phase 7 — Reports
- Weekly summary: glucose trend, adherence, weight change (for doctor visits)
- Medication reminders: scheduling only, no dosage advice

---

## 3. Database Schema

**users**
`id, email, password_hash, role (patient/caregiver/admin), created_at`

**patient_profiles**
`id, user_id (FK), diabetes_type, diagnosis_duration, age, height, weight, activity_level, medications, dietary_prefs, family_history`

**caregiver_links**
`id, caregiver_id (FK), patient_id (FK), status (pending/approved/revoked), created_at`

**ai_plans**
`id, patient_id (FK), target_weight, daily_calorie_target, macro_targets (json), daily_step_goal, updated_at`

**meal_logs**
`id, patient_id (FK), timestamp, meal_type, food_items (json), estimated_carbs, estimated_calories, photo_url (nullable)`

**glucose_logs**
`id, patient_id (FK), timestamp, value, context_tag`

**activity_logs**
`id, patient_id (FK), date, steps, calories_burned`

**recommendations**
`id, patient_id (FK), insight_type (trend/correlation/risk), source_model (nullable), confidence_score (nullable), raw_data (json), llm_phrased_text, created_at`

**notifications**
`id, recipient_id (FK), type, message, read (bool), created_at`

**reports**
`id, patient_id (FK), period_start, period_end, summary_data (json), generated_at`

---

## 4. API Endpoints

```
/api/v1/auth          → register, login, refresh
/api/v1/patients       → onboarding, profile get/update
/api/v1/caregivers     → link-request, approve/revoke, list-linked-patients
/api/v1/logs           → meals, glucose, activity (scoped by role)
/api/v1/plans          → get current AI plan
/api/v1/ml             → risk-assessment, correlation, recommendations
/api/v1/reports        → weekly-summary
/api/v1/admin          → users, links, stats (admin-only)
/ws/notifications      → WebSocket, real-time caregiver alerts
```

All patient-scoped routes enforce ownership or approved-link access via a shared FastAPI dependency — never via frontend hiding alone.

---

## 5. Architecture Diagram

```
┌─────────────────────────────────────┐
│  React (Vite) + Tailwind — Web App   │
│  Patient view  |  Caregiver view      │
│  Admin view                           │
└──────────────────┬────────────────────┘
                    │ REST (JWT) + WebSocket
                    ▼
┌─────────────────────────────────────┐
│         FastAPI Backend               │
│  - Auth (JWT/OAuth2 + bcrypt)          │
│  - CRUD: onboarding, logs, plans        │
│  - WebSocket: caregiver notifications    │
│  - Scheduler: reminders, missed-log      │
│    alerts (APScheduler, dedicated module) │
│  - Analytics Engine (pandas)              │
│  - Intelligence: ML models                 │
│    (scikit-learn / PyTorch)                 │
│  - Groq API (explanation phrasing only)     │
│  - Alembic: schema migrations               │
└──────────────────┬────────────────────┘
                    │
                    ▼
         PostgreSQL (Neon) — all data
```

---

## 6. Folder Structure

```
diazo/
├── backend/
│   ├── app/
│   │   ├── api/                # route modules
│   │   ├── models/              # SQLAlchemy tables
│   │   ├── schemas/              # Pydantic request/response models
│   │   ├── intelligence/          # analytics_engine, risk_model, correlation_model,
│   │   │                           # forecasting_model (optional), explain, llm_explain
│   │   │                           # (renamed from ml/ — not everything here is ML;
│   │   │                           #  some is deterministic analytics)
│   │   ├── services/               # notification_service, reminder_service,
│   │   │                           # report_service, plan_service
│   │   ├── scheduler/                # jobs.py — APScheduler job definitions,
│   │   │                             # kept separate from services
│   │   ├── utils/                     # bmi.py, calories.py, macros.py, validators.py
│   │   ├── core/                       # config.py, security.py, dependencies.py,
│   │   │                               # database.py (engine + session)
│   │   └── main.py
│   ├── alembic/                          # migration scripts
│   ├── scripts/
│   │   └── synthetic_data_generator.py    # backend utility, not production data
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── pages/              # patient dashboard, caregiver dashboard, admin, onboarding
    │   ├── components/          # shared UI (charts, forms, cards)
    │   ├── api/                  # fetch wrappers
    │   └── App.jsx
    └── package.json
```

---

## 7. Development Roadmap

1. Backend foundation: auth, DB models, core schema
2. Logging endpoints: meals, glucose, activity
3. Synthetic data generator (realistic correlated patterns)
4. AI plan calculation (rule-based)
5. Analytics Engine (trend/correlation detection)
6. ML models: correlation regression, risk classification
7. Groq integration for explanation phrasing
8. Caregiver linking, dashboard, WebSocket notifications
9. Admin dashboard
10. Weekly report generation
11. Frontend UI polish (clean, health-app visual design)
12. Stretch: PyTorch forecasting model
13. Stretch: photo-based food logging

---

## 8. Ground Rules Going Forward

- No further architecture changes unless a genuine implementation blocker is hit
- Every feature/field must map to a real use case (see Phase-by-phase rationale discussed during planning)
- LLM (Groq) never computes or decides — only phrases already-derived insights
- Caregiver access is strictly read-only, enforced server-side
