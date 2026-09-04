# DIAZO Progress Log

This log records the project state found at the start of the frontend integration work and every completed implementation step afterward.

## Starting state — 19 August 2026

### Available backend work

- FastAPI application loaded successfully with 35 routes.
- Backend modules and API endpoints existed for authentication, patient profiles, logs, plans, analytics/recommendations, caregiver linking, notifications, reports, and administration.
- The project roadmap and technical requirements are defined in `PROJECT_SPEC.md`.

### Frontend gaps identified

- Only `/login` and `/dashboard` were registered in `src/App.jsx`.
- `Onboarding.jsx`, `CaregiverDashboard.jsx`, `AdminDashboard.jsx`, `MealLogForm.jsx`, `ActivityCard.jsx`, `PatientSwitcher.jsx`, `logs.js`, and `ml.js` were empty or unavailable to the running app.
- `useWebSocket.js` contained an entirely commented-out implementation, causing the production build to fail because `PatientDashboard` imported `useWebSocket`.
- Login had no registration flow.
- The dashboard did not redirect a patient without a profile to onboarding.

## Completed work

### 1. Frontend routing and session foundation

Files changed:

- `frontend/src/api/auth.js`
- `frontend/src/App.jsx`

Changes:

- Added `getSessionRole()` to read the JWT role claim for client-side navigation.
- Added `RequireAuth` to protect patient-only routes.
- Added the `/onboarding` route.
- Added fallback navigation for unknown routes.

Note: backend authorization remains the source of truth; route protection only controls client navigation.

### 2. WebSocket dashboard repair

Files changed:

- `frontend/src/hooks/useWebSocket.js`

Changes:

- Restored the notification WebSocket hook from its commented-out state.
- Connects with the stored access token, parses valid server messages, and closes the connection on unmount.
- Uses a ref for the callback so dashboard re-renders do not create additional socket connections.

### 3. Patient onboarding

Files changed:

- `frontend/src/pages/Onboarding.jsx`
- `frontend/src/pages/PatientDashboard.jsx`

Changes:

- Implemented the patient onboarding form.
- Connected it to `POST /api/v1/patients/me`.
- Matched the form values to the backend contract:
  - Diabetes type: `type1`, `type2`, `prediabetic`, or `none`.
  - Sex: `female` or `male`.
  - Activity: `sedentary`, `moderate`, or `active`.
- Added automatic redirect from dashboard to onboarding when the patient profile does not exist.
- On successful onboarding, the user returns to the dashboard, where the backend-generated plan is available.

### 4. Registration and sign-in flow

Files changed:

- `frontend/src/pages/Login.jsx`

Changes:

- Added a patient account creation mode using `POST /api/v1/auth/register`.
- Automatically signs in after successful registration.
- Sends a newly registered patient to onboarding.
- Existing users continue to sign in and open the dashboard.

### 5. Daily meal logging

Files changed:

- `frontend/src/api/logs.js`
- `frontend/src/components/MealLogForm.jsx`
- `frontend/src/pages/PatientDashboard.jsx`

Changes:

- Added shared API wrappers for meal, glucose, and activity endpoints.
- Implemented the meal form for meal type, optional food description, carbohydrates, and calories.
- Connected meal submission to `POST /api/v1/logs/meals`.
- Updated the dashboard’s recent meals immediately after a successful log.

### 6. Daily activity logging

Files changed:

- `frontend/src/components/ActivityCard.jsx`
- `frontend/src/pages/PatientDashboard.jsx`

Changes:

- Implemented the daily activity form for date, steps, and calories burned.
- Connected it to the backend’s idempotent `PUT /api/v1/logs/activity` endpoint.
- Updates/replaces the activity entry for the submitted date in the dashboard immediately.

### 7. Local testing configuration

Files changed:

- `backend/.env`

Changes:

- Added `http://127.0.0.1:5173` to `CORS_ORIGINS` alongside `http://localhost:5173`.
- This fixes account-registration requests when Vite is opened through the numeric loopback address.

### 8. ESP32 meal-scale ingestion and live dashboard delivery

Files changed:

- `backend/app/models/meal_weight_reading.py`
- `backend/app/schemas/hardware.py`
- `backend/app/api/hardware.py`
- `backend/app/core/config.py`
- `backend/app/main.py`
- `backend/.env`
- `frontend/src/pages/PatientDashboard.jsx`
- `frontend/src/components/MealLogForm.jsx`
- `frontend/src/components/ActivityCard.jsx`

Changes:

- Added `POST /api/v1/hardware/meal-weight-readings` for ESP32 meal scales.
- Protects the endpoint with the server-side `ESP32_DEVICE_API_KEY`; the endpoint is disabled until a non-empty secret is configured.
- Persists each received measurement in `meal_weight_readings` for auditability.
- Broadcasts an authenticated WebSocket event to the matching patient's browser: `meal_weight_reading` with `weight_g` and `device_id`.
- Updated the patient dashboard with a professional layout and a live "meal scale connected" status card.
- The meal form now attaches the latest scale reading to `food_items` when a meal is submitted.

## Verification

- The backend import check succeeded: FastAPI loaded 35 routes.
- The frontend production build succeeds with `npm run build`.
- Current build warning: the JavaScript bundle is larger than Vite’s 500 kB advisory threshold. This does not block the app; code splitting can be handled during UI polish.

## Next work

1. Add manual glucose logging to the patient dashboard.
2. Implement caregiver route/dashboard and patient switcher.
3. Implement admin route/dashboard.
4. Add role-aware dashboard destinations for caregiver and admin users.
5. Add end-to-end API tests and migrate schema creation from development `create_all` to Alembic migrations.
