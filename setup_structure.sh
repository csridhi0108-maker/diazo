#!/bin/bash
# DIAZO — Project Scaffolding Script
# Creates the full folder + empty file structure as per PROJECT_SPEC.md
# Run this once from the parent directory where you want "diazo/" created.

set -e

ROOT="."

echo "Creating DIAZO project structure..."

# ---------- Backend ----------
mkdir -p "$ROOT/backend/app/api"
mkdir -p "$ROOT/backend/app/models"
mkdir -p "$ROOT/backend/app/schemas"
mkdir -p "$ROOT/backend/app/intelligence"
mkdir -p "$ROOT/backend/app/services"
mkdir -p "$ROOT/backend/app/scheduler"
mkdir -p "$ROOT/backend/app/utils"
mkdir -p "$ROOT/backend/app/core"
mkdir -p "$ROOT/backend/alembic/versions"
mkdir -p "$ROOT/backend/scripts"

# app/api
touch "$ROOT/backend/app/api/__init__.py"
touch "$ROOT/backend/app/api/auth.py"
touch "$ROOT/backend/app/api/patients.py"
touch "$ROOT/backend/app/api/caregivers.py"
touch "$ROOT/backend/app/api/logs.py"
touch "$ROOT/backend/app/api/plans.py"
touch "$ROOT/backend/app/api/ml.py"
touch "$ROOT/backend/app/api/reports.py"
touch "$ROOT/backend/app/api/admin.py"
touch "$ROOT/backend/app/api/notifications_ws.py"

# app/models
touch "$ROOT/backend/app/models/__init__.py"
touch "$ROOT/backend/app/models/user.py"
touch "$ROOT/backend/app/models/patient_profile.py"
touch "$ROOT/backend/app/models/caregiver_link.py"
touch "$ROOT/backend/app/models/ai_plan.py"
touch "$ROOT/backend/app/models/meal_log.py"
touch "$ROOT/backend/app/models/glucose_log.py"
touch "$ROOT/backend/app/models/activity_log.py"
touch "$ROOT/backend/app/models/recommendation.py"
touch "$ROOT/backend/app/models/notification.py"
touch "$ROOT/backend/app/models/report.py"

# app/schemas
touch "$ROOT/backend/app/schemas/__init__.py"
touch "$ROOT/backend/app/schemas/user.py"
touch "$ROOT/backend/app/schemas/patient.py"
touch "$ROOT/backend/app/schemas/caregiver.py"
touch "$ROOT/backend/app/schemas/log.py"
touch "$ROOT/backend/app/schemas/plan.py"
touch "$ROOT/backend/app/schemas/recommendation.py"
touch "$ROOT/backend/app/schemas/report.py"

# app/intelligence
touch "$ROOT/backend/app/intelligence/__init__.py"
touch "$ROOT/backend/app/intelligence/analytics_engine.py"
touch "$ROOT/backend/app/intelligence/risk_model.py"
touch "$ROOT/backend/app/intelligence/correlation_model.py"
touch "$ROOT/backend/app/intelligence/forecasting_model.py"
touch "$ROOT/backend/app/intelligence/explain.py"
touch "$ROOT/backend/app/intelligence/llm_explain.py"

# app/services
touch "$ROOT/backend/app/services/__init__.py"
touch "$ROOT/backend/app/services/notification_service.py"
touch "$ROOT/backend/app/services/reminder_service.py"
touch "$ROOT/backend/app/services/report_service.py"
touch "$ROOT/backend/app/services/plan_service.py"

# app/scheduler
touch "$ROOT/backend/app/scheduler/__init__.py"
touch "$ROOT/backend/app/scheduler/jobs.py"

# app/utils
touch "$ROOT/backend/app/utils/__init__.py"
touch "$ROOT/backend/app/utils/bmi.py"
touch "$ROOT/backend/app/utils/calories.py"
touch "$ROOT/backend/app/utils/macros.py"
touch "$ROOT/backend/app/utils/validators.py"

# app/core
touch "$ROOT/backend/app/core/__init__.py"
touch "$ROOT/backend/app/core/config.py"
touch "$ROOT/backend/app/core/security.py"
touch "$ROOT/backend/app/core/dependencies.py"
touch "$ROOT/backend/app/core/database.py"

# app root
touch "$ROOT/backend/app/__init__.py"
touch "$ROOT/backend/app/main.py"

# alembic
touch "$ROOT/backend/alembic/env.py"
touch "$ROOT/backend/alembic.ini"

# scripts
touch "$ROOT/backend/scripts/synthetic_data_generator.py"

# backend root
touch "$ROOT/backend/requirements.txt"
touch "$ROOT/backend/.env.example"

# ---------- Frontend ----------
mkdir -p "$ROOT/frontend/src/pages"
mkdir -p "$ROOT/frontend/src/components"
mkdir -p "$ROOT/frontend/src/api"

touch "$ROOT/frontend/src/pages/Onboarding.jsx"
touch "$ROOT/frontend/src/pages/PatientDashboard.jsx"
touch "$ROOT/frontend/src/pages/CaregiverDashboard.jsx"
touch "$ROOT/frontend/src/pages/AdminDashboard.jsx"
touch "$ROOT/frontend/src/pages/Login.jsx"

touch "$ROOT/frontend/src/components/GlucoseChart.jsx"
touch "$ROOT/frontend/src/components/MealLogForm.jsx"
touch "$ROOT/frontend/src/components/ActivityCard.jsx"
touch "$ROOT/frontend/src/components/RecommendationCard.jsx"
touch "$ROOT/frontend/src/components/PatientSwitcher.jsx"

touch "$ROOT/frontend/src/api/client.js"
touch "$ROOT/frontend/src/api/auth.js"
touch "$ROOT/frontend/src/api/logs.js"
touch "$ROOT/frontend/src/api/ml.js"

touch "$ROOT/frontend/src/App.jsx"
touch "$ROOT/frontend/src/main.jsx"
touch "$ROOT/frontend/package.json"
touch "$ROOT/frontend/vite.config.js"
touch "$ROOT/frontend/tailwind.config.js"
touch "$ROOT/frontend/.env.example"

# ---------- Root ----------
touch "$ROOT/.gitignore"
touch "$ROOT/README.md"

echo "Done. Project structure created under ./$ROOT"
find "$ROOT" -type f | sort