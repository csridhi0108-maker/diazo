# DIAZO

### AI-Powered Diabetes Health Monitoring & Personalization Platform

DIAZO is a full-stack diabetes health management platform designed to help patients continuously track their glucose, meals, physical activity, and health-related patterns while providing personalized, data-driven insights.

The platform combines deterministic analytics, AI-assisted natural-language explanations, personalized health planning, automated reports, multilingual support, real-time caregiver connectivity, emergency SOS alerts, and role-based access into a single healthcare-oriented application.

---

## Overview

Managing diabetes involves more than recording individual glucose readings. Patients need to understand:

- How their meals relate to glucose levels
- How physical activity correlates with their readings
- When unusual glucose events occur
- Whether they are consistently logging their health data
- What patterns are emerging over time
- How their recent data can be summarized clearly
- How caregivers can stay informed when appropriate

DIAZO addresses these requirements through a centralized health monitoring platform. Instead of allowing an LLM to independently interpret raw medical data, DIAZO follows a controlled intelligence pipeline:

```text
Patient Data
     │
     ▼
Deterministic Analytics
     │
     ▼
Structured Insights
     │
     ▼
Explain Layer
     │
     ▼
LLM Language Layer
     │
     ▼
Patient-Friendly Recommendations
     │
     ▼
Dashboard + Reports
```

This separation keeps numerical analysis deterministic while using the LLM primarily for communication and personalization.

## Key Features

### 1. Patient Dashboard

The patient dashboard provides a centralized view of the user's recent health information, bringing together:

- Today's personalized plan
- Recent glucose readings, meals, and activity
- AI-generated recommendations and health insights
- Report generation and Emergency SOS functionality
- Multilingual interface and pending caregiver request management

### 2. Glucose Tracking

Patients can record glucose readings with contextual information (Fasting, Before meal, After meal, Bedtime, Random). Each reading is stored with Patient ID, Timestamp, Glucose value, and Context tag for historical visualization and analytics.

### 3. Meal Logging

Patients can record meals with meal type, estimated carbohydrate intake, and timestamp. Supported categories include Breakfast, Lunch, Dinner, and Snack. This data is used by the analytics layer to investigate relationships between carbohydrate intake and glucose readings.

### 4. Physical Activity Tracking

DIAZO supports daily activity logging (Date, Step count, Calories burned). The system compares activity levels against daily average glucose measurements to identify potential patterns in the user's historical data.

### 5. Caregiver & Doctor Connectivity

DIAZO supports a consent-based caregiver linking system:

```text
Caregiver sends request (patient email)
        │
        ▼
Backend creates pending CareLink
        │
        ▼
Patient sees pending request on dashboard
        │
        ▼
Patient Approves / Rejects
        │
        ▼
Caregiver gains read-only access to patient data
```

- Caregivers can request access via patient email.
- Patients must explicitly approve or reject requests (HIPAA-aligned consent).
- Approved caregivers can view patient dashboards (read-only) and receive real-time SOS alerts.

### 6. Emergency SOS

The patient interface includes a one-click Emergency SOS feature:

```text
Patient clicks SOS
        │
        ▼
Backend finds all approved caregivers/doctors
        │
        ▼
Notification records created in DB + WebSocket push
        │
        ▼
Caregiver bell shows unread count
        │
        ▼
Caregiver clicks notification → navigates to patient dashboard
```

### 7. Real-Time Notifications

A WebSocket-backed notification system for connected users. Caregivers receive alerts for SOS events and meal logs, with unread counts, click-to-mark-as-read, and click-to-navigate features.

### 8. Admin Console

A full-featured admin panel for platform oversight, including:

- System-wide statistics
- User management
- Cascade deletion
- Care link management
- Force-link capabilities for administrative use

### 9. Automated Health Reports

DIAZO generates downloadable PDF health reports combining patient information, recent logs, adherence, detected patterns, spike events, personalized recommendations, and AI-generated explanations.

The report system uses the intelligence pipeline beyond a single overall summary. Where available, reports can incorporate:

- Carb–glucose relationships
- Activity–glucose relationships
- Logging adherence
- Specific glucose spike events
- Patient-specific baseline comparisons
- Personalized AI recommendations
- Structured insight data supporting generated explanations

This allows the PDF to function as a richer longitudinal health summary rather than simply a short narrative.

### 10. Multilingual Support

Internationalization support via `react-i18next`.

Currently supported languages:

- English
- Hindi (हिन्दी)
- Telugu (తెలుగు)

Language preferences persist through `localStorage`, and the patient's preferred language can also be used for patient-facing AI explanations.

---

## AI & Intelligence Layer

One of the core design principles of DIAZO is that the LLM is **not responsible for calculating medical statistics**.

```text
analytics_engine.py
        │
        ▼
      explain.py
        │
        ▼
   llm_explain.py
        │
        ▼
   Recommendation
```

### Deterministic Analytics Engine

Processes recent patient logs using Pandas:

- **Carb–Glucose Correlation:** Calculates average glucose for high/low carb meals, differences, thresholds, sample sizes, and confidence scores.
- **Adherence Analysis:** Tracks logging consistency (days with glucose/meal logs vs. tracking window).
- **Activity–Glucose Analysis:** Compares daily activity with daily average glucose.
- **Spike Event Detection:** Identifies specific glucose spikes relative to the patient's own baseline and associates them with preceding meals.

### Explain Layer

Sits between raw analytics and the LLM. It determines if a result is meaningful enough to become a user-facing insight and converts it into a standardized structure, including:

```text
correlation
adherence
activity_impact
spike_events
```

### LLM Explanation Layer

Uses Groq with a Llama-based LLM to provide natural-language explanations.

The LLM is strictly constrained to:

- Use only supplied structured data
- Preserve calculated numbers
- Avoid inventing values
- Avoid diagnoses
- Avoid medication or treatment recommendations
- Avoid unsupported medical claims
- Use simple, encouraging, non-judgmental language
- Phrase already-computed analytics rather than performing independent calculations

### Recommendation System

Generated insights are stored as recommendations containing:

- Patient ID
- Insight type
- Source model
- Confidence score
- Structured raw data
- LLM-generated explanation
- Creation timestamp

DIAZO avoids creating duplicate recommendation records when the underlying analytical data has not changed.

---

## Authentication & Authorization

DIAZO uses token-based authentication with role-based access control.

| Role | Purpose |
|---|---|
| **Patient** | Track health data, view insights/plans/reports, manage caregiver requests |
| **Caregiver** | Request access to patients, view approved dashboards, receive SOS alerts |
| **Doctor** | Access permitted patient information with clinical context |
| **Admin** | Full platform oversight, user management, force-link management |

### Security Features

- Password hashing (bcrypt)
- JWT access tokens + refresh tokens
- Backend-enforced authorization on protected endpoints
- Patient-scoped resource access
- OAuth2-compatible login flow
- `404` for a missing account
- `401` for an incorrect password

---

## Architecture

### Frontend

```text
frontend/
├── public/images/
├── src/
│   ├── api/              # Axios client + endpoint wrappers
│   ├── components/       # Reusable UI
│   ├── hooks/            # Custom hooks
│   ├── locales/          # i18n translation JSON files
│   ├── pages/            # Route-level components
│   ├── App.jsx           # Router + auth guards
│   ├── i18n.js           # i18next configuration
│   └── main.jsx          # Entry point
├── package.json
└── vite.config.js
```

### Backend

```text
backend/
├── app/
│   ├── api/              # REST + WebSocket routers
│   ├── core/             # Config, DB, security, dependencies, WS manager
│   ├── intelligence/     # Analytics + AI explanation pipeline
│   ├── models/           # SQLAlchemy ORM models
│   ├── schemas/          # Pydantic request/response schemas
│   ├── services/         # Business logic, reports, notifications
│   ├── scheduler/        # Background jobs
│   └── utils/            # Supporting utilities
├── alembic/              # Database migrations
└── requirements.txt
```

### API Organization

Endpoints are versioned under `/api/v1/`:

```text
/auth
/dashboard
/logs
/glucose-logs
/ml
/reports
/patients
/plans
/caregivers
/notifications
/admin
/hardware
```

### Database

PostgreSQL, hosted on Neon, with SQLAlchemy ORM and Alembic migrations.

Core entities include:

```text
User
PatientProfile
GlucoseLog
MealLog
ActivityLog
AIPlan
Recommendation
Report
CareLink
Notification
MealWeightReading
```

---

## Technology Stack

- **Frontend:** React 18, Vite, Tailwind CSS, React Router v6, Axios, react-i18next, WebSockets
- **Backend:** Python 3.11+, FastAPI, SQLAlchemy 2.0, Pydantic v2, Pandas, Alembic
- **AI / Intelligence:** Groq API, Llama-based LLM, Pandas-based deterministic analytics
- **Database:** PostgreSQL / Neon
- **Authentication:** JWT (HS256), OAuth2-compatible login
- **Real-time communication:** Native WebSockets

---

## Local Development

### Prerequisites

A local development environment requires:

- Git
- Python 3.11+
- Node.js and npm
- Access to the configured PostgreSQL/Neon database
- Required environment variables

### Backend

```bash
cd backend
python -m venv venv
```

**Linux/macOS:**

```bash
source venv/bin/activate
```

**Windows PowerShell:**

```powershell
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure:

```text
backend/.env
```

Then start FastAPI:

```bash
uvicorn app.main:app --reload
```

### Frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

---

## Production Deployment

For a client-facing deployment, DIAZO can use Vercel for the frontend and Render for the backend:

```text
React/Vite Frontend
        │
        ▼
      Vercel
        │
        ▼
   FastAPI Backend
        │
        ▼
      Render
        │
   ┌────┴────┐
   ▼         ▼
 Neon       Groq
```

The frontend should use the deployed Render backend URL rather than `localhost`.

The backend should allow the deployed Vercel frontend origin through its CORS configuration.

Production secrets such as:

```text
DATABASE_URL
GROQ_API_KEY
SECRET_KEY
```

should be configured through hosting-provider environment variables and must not be committed to GitHub.

---

## Data Flows

### Caregiver Linking Flow

```text
Caregiver enters patient email
        │
        ▼
Backend creates CareLink (pending)
        │
        ▼
Patient dashboard shows request
        │
        ▼
Patient clicks Approve / Reject
        │
        ▼
CareLink status becomes approved
        │
        ▼
Caregiver can view permitted patient dashboard
```

### Emergency SOS Flow

```text
Patient clicks SOS
        │
        ▼
POST /api/v1/notifications/emergency
        │
        ▼
Backend queries approved CareLinks
        │
        ▼
Notification rows + WebSocket push
        │
        ▼
Caregiver notification bell shows unread count
        │
        ▼
Caregiver clicks notification
        │
        ▼
Patient dashboard opens
```

### Recommendation Pipeline

```text
Logs
  │
  ▼
Analytics Engine
  │
  ▼
Explain Layer
  │
  ▼
Structured Insight
  │
  ▼
Groq / LLM
  │
  ▼
Patient-Friendly Text
  │
  ▼
Recommendation Record
  │
  ├──► Dashboard
  │
  └──► PDF Report
```

### Report Generation Flow

```text
Patient requests report
        │
        ▼
Report API
        │
        ▼
Report Service
        │
        ├── Patient information
        ├── Glucose data
        ├── Meal data
        ├── Activity data
        ├── Adherence
        ├── Analytics
        ├── Spike events
        ├── Personalized plan
        └── AI recommendations
        │
        ▼
Structured Report
        │
        ▼
PDF Generation
        │
        ▼
Patient downloads report
```

---

## Design Principles

1. **Deterministic calculations first** — Numerical analysis is performed by application code, not the LLM.
2. **LLM as a communication layer** — The LLM transforms structured results into accessible language.
3. **Backend-enforced authorization** — Frontend route visibility is not a security boundary.
4. **Patient-specific analysis** — Analytics are calculated relative to the patient's own historical data.
5. **Insufficient data is respected** — The system avoids generating insights when data is unavailable.
6. **Auditability** — Recommendations retain structured source data for traceability.
7. **Consent-first caregiver access** — Patients explicitly approve caregiver links.
8. **Real-time when it matters** — WebSockets are used for emergency alerts and live notifications.
9. **Structured intelligence** — Analytics, insight generation, and language generation remain separate responsibilities.
10. **No unsupported medical claims** — The AI explanation layer is restricted to supplied application data.

---

## Hardware Integration

The repository contains components for integration with external measurement devices, including ESP32-based smart-scale/hardware workflows.

Relevant backend components include:

```text
backend/app/api/hardware.py
backend/app/models/meal_weight_reading.py
backend/app/schemas/hardware.py
```

For detailed hardware/API information, refer to:

```text
ESP32 Integration.md
```

---

## Status

- ✅ Patient health tracking — glucose, meals, activity
- ✅ Personalized AI plans
- ✅ Deterministic health analytics
- ✅ AI-generated explanations using Groq / Llama
- ✅ Carb–glucose correlation analysis
- ✅ Activity–glucose analysis
- ✅ Logging adherence analysis
- ✅ Patient-specific glucose spike detection
- ✅ Recommendation persistence
- ✅ Duplicate recommendation prevention
- ✅ Detailed AI-assisted PDF reports
- ✅ Role-based authentication
- ✅ Consent-based caregiver connectivity
- ✅ Doctor connectivity
- ✅ Real-time notifications via WebSockets
- ✅ Emergency SOS alerts
- ✅ Admin console
- ✅ User management
- ✅ Care link management and force-link functionality
- ✅ Cascade deletion support
- ✅ English, Hindi, and Telugu localization
- ✅ Hardware / ESP32 integration foundations

---

## Future Expansion

- Advanced glucose forecasting
- CGM and insulin pump integrations
- Richer caregiver notifications with SMS/email fallback
- Clinical note-taking for doctors
- Expanded multilingual AI explanations
- Expanded longitudinal reports
- More patient-specific trend analysis
- Additional wearable and hardware integrations

---

## License

This project is maintained as a private project. Access and usage are restricted to authorized collaborators and stakeholders.
