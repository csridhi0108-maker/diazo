import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  getDashboard,
  getMyProfile,
  refreshRecommendations,
} from '../api/dashboard'
import { isLoggedIn, getSessionRole, logoutUser } from '../api/auth'
import { getPendingRequests, respondToRequest } from '../api/caregivers'
import { triggerEmergencySOS } from '../api/notifications'
import GlucoseChart from '../components/GlucoseChart'
import RecommendationCard from '../components/RecommendationCard'
import MealLogForm from '../components/MealLogForm'
import ActivityCard from '../components/ActivityCard'
import LanguageSwitcher from '../components/LanguageSwitcher'
import { useWebSocket } from '../hooks/useWebSocket'
import { generateAndDownloadReport } from '../api/reports'

function PatientDashboard() {
  const { t } = useTranslation()

  const [dashboard, setDashboard] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [scaleReading, setScaleReading] = useState(null)

  const [pendingRequests, setPendingRequests] = useState([])
  const [requestLoading, setRequestLoading] = useState(false)

  const navigate = useNavigate()

  useEffect(() => {
    const checkAuth = () => {
      if (!isLoggedIn() || getSessionRole() !== 'patient') {
        navigate('/login', { replace: true })
        return false
      }

      return true
    }

    if (!checkAuth()) return

    const handlePageShow = (event) => {
      if (event.persisted) {
        if (!isLoggedIn() || getSessionRole() !== 'patient') {
          window.location.replace('/login')
        }
      }
    }

    window.addEventListener('pageshow', handlePageShow)

    return () => window.removeEventListener('pageshow', handlePageShow)
  }, [navigate])

  useEffect(() => {
    loadDashboard()
    loadPendingRequests()
  }, [])

  useWebSocket((message) => {
    if (message.type === 'meal_weight_reading') {
      setScaleReading(message)
    }
  })

  async function loadDashboard() {
    try {
      setError('')

      const profile = await getMyProfile()

      if (profile.full_name) {
        localStorage.setItem('patient_name', profile.full_name)
      }

      const data = await getDashboard(profile.user_id || profile.id)

      setDashboard(data)

      try {
        const freshRecommendations = await refreshRecommendations(
          data.patient_id
        )

        setDashboard((prev) => ({
          ...prev,
          recommendations: freshRecommendations,
        }))
      } catch (err) {
        console.error('Failed to refresh AI insights:', err)
      }
    } catch (err) {
      if (err.response?.status === 404) {
        navigate('/onboarding', { replace: true })
        return
      } else if (err.response?.status === 401) {
        navigate('/login', { replace: true })
        return
      } else {
        setError(t('dashboard_load_error'))
      }
    } finally {
      setLoading(false)
    }
  }

  async function loadPendingRequests() {
    try {
      const requests = await getPendingRequests()
      setPendingRequests(requests)
    } catch (err) {
      console.error('Failed to load pending requests:', err)
    }
  }

  async function handleRequestResponse(linkId, approve) {
    setRequestLoading(true)

    try {
      await respondToRequest(linkId, approve)

      setPendingRequests((prev) =>
        prev.filter((req) => req.link_id !== linkId)
      )
    } catch (err) {
      console.error('Failed to respond to request:', err)
      alert(t('request_process_error'))
    } finally {
      setRequestLoading(false)
    }
  }

  async function handleRefreshInsights() {
    if (!dashboard) return

    setRefreshing(true)

    try {
      const fresh = await refreshRecommendations(dashboard.patient_id)

      setDashboard((prev) => ({
        ...prev,
        recommendations: fresh,
      }))
    } catch {
      setError(t('refresh_insights_error'))
    } finally {
      setRefreshing(false)
    }
  }

  async function handleSOS() {
    if (!window.confirm(t('sos_confirmation'))) {
      return
    }

    try {
      await triggerEmergencySOS()
      alert(t('sos_success'))
    } catch (err) {
      alert(
        `${t('sos_failed')}: ${
          err.response?.data?.detail || t('unknown_error')
        }`
      )
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-emerald-200 border-t-emerald-600"></div>

          <p className="text-sm font-medium text-gray-500">
            {t('loading_health_data')}
          </p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
        <div className="bg-white p-8 rounded-2xl shadow-sm text-center max-w-sm border border-red-100">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-red-50 mb-4">
            <svg
              className="h-6 w-6 text-red-600"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16.333c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          </div>

          <p className="text-gray-700 font-medium">
            {error}
          </p>

          <button
            onClick={() => window.location.reload()}
            className="mt-4 text-sm text-emerald-600 hover:text-emerald-700 font-semibold"
          >
            {t('try_again')}
          </button>
        </div>
      </div>
    )
  }

  const {
    plan,
    recent_glucose_logs,
    recent_meal_logs,
    recent_activity_logs,
    recommendations: rawRecommendations,
  } = dashboard || {}

  const recommendations = rawRecommendations
    ? Array.from(
        new Map(
          rawRecommendations.map((r) => [r.insight_type, r])
        ).values()
      )
    : []

  const storedName = localStorage.getItem('patient_name')

  const displayName = storedName
    ? storedName.split(' ')[0]
    : t('there')

  return (
    <div className="min-h-screen bg-slate-50/50">
      <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 sm:py-10 space-y-6">

        {/* Header */}
        <header className="rounded-3xl bg-gradient-to-br from-emerald-700 to-teal-700 px-6 py-8 text-white shadow-xl shadow-emerald-900/10 sm:px-8 animate-fade-in-up">

          <p className="text-xs font-bold uppercase tracking-[0.2em] text-emerald-100/80">
            {t('daily_care')}
          </p>

          <div className="mt-4 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">
                {t('welcome_back')}, {displayName}!
              </h1>

              <p className="mt-2 text-sm text-emerald-100/80 max-w-md">
                {t('dashboard_description')}
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3">

              {/* Language Switcher */}
              <LanguageSwitcher />

              {/* Glucose Tracker */}
              <button
                onClick={() => navigate('/glucose-tracker')}
                className="flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/20 rounded-xl text-sm font-medium transition-all ring-1 ring-inset ring-white/10 backdrop-blur-sm"
              >
                <svg
                  className="h-4 w-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                  />
                </svg>

                <span>{t('glucose_tracker')}</span>
              </button>

              {/* SOS */}
              <button
                onClick={handleSOS}
                className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-xl text-sm font-semibold transition-all shadow-lg shadow-red-900/20 hover:shadow-red-900/40"
              >
                <svg
                  className="h-4 w-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16.333c-.77-1.333.192 3 1.732 3z"
                  />
                </svg>

                <span>{t('emergency_sos')}</span>
              </button>

              {/* Logout */}
              <button
                onClick={() => {
                  logoutUser()
                  window.location.replace('/login')
                }}
                className="flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/20 rounded-xl text-sm font-medium transition-all ring-1 ring-inset ring-white/10 backdrop-blur-sm"
              >
                <svg
                  className="h-4 w-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                  />
                </svg>

                <span>{t('logout')}</span>
              </button>
            </div>
          </div>
        </header>

        {/* Pending Care Requests */}
        {pendingRequests.length > 0 && (
          <div className="rounded-2xl border border-amber-200 bg-amber-50/50 p-6 animate-fade-in-up shadow-sm">

            <div className="flex items-center gap-3 mb-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-amber-100 text-amber-600">
                <svg
                  className="h-5 w-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                  />
                </svg>
              </div>

              <div>
                <h2 className="text-lg font-semibold text-amber-900">
                  {t('pending_care_requests')}
                </h2>

                <p className="text-sm text-amber-700">
                  {t('care_request_description')}
                </p>
              </div>
            </div>

            <div className="space-y-3">
              {pendingRequests.map((req) => (
                <div
                  key={req.link_id}
                  className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-4 bg-white rounded-xl border border-amber-100 shadow-sm"
                >
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-full bg-slate-100 flex items-center justify-center text-slate-600 font-bold">
                      {(req.caregiver_name || req.caregiver_email)
                        .charAt(0)
                        .toUpperCase()}
                    </div>

                    <div>
                      <p className="text-sm font-semibold text-gray-900">
                        {req.caregiver_name || t('unknown_caregiver')}
                      </p>

                      <p className="text-xs text-gray-500">
                        {req.caregiver_email}
                      </p>

                      <p className="text-xs text-amber-600 font-medium mt-0.5 capitalize">
                        {req.link_type} {t('link')}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 sm:ml-auto">

                    <button
                      onClick={() =>
                        handleRequestResponse(req.link_id, false)
                      }
                      disabled={requestLoading}
                      className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-red-600 bg-red-50 hover:bg-red-100 rounded-lg transition-colors disabled:opacity-50"
                    >
                      <svg
                        className="h-4 w-4"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M6 18L18 6M6 6l12 12"
                        />
                      </svg>

                      {t('reject')}
                    </button>

                    <button
                      onClick={() =>
                        handleRequestResponse(req.link_id, true)
                      }
                      disabled={requestLoading}
                      className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-emerald-700 bg-emerald-100 hover:bg-emerald-200 rounded-lg transition-colors disabled:opacity-50"
                    >
                      <svg
                        className="h-4 w-4"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M5 13l4 4L19 7"
                        />
                      </svg>

                      {t('approve')}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ESP32 Scale Reading */}
        {scaleReading && (
          <div className="flex flex-col gap-3 rounded-2xl border border-emerald-200 bg-emerald-50 px-5 py-4 sm:flex-row sm:items-center sm:justify-between animate-fade-in-up shadow-sm">

            <div className="flex items-start gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
                <svg
                  className="h-5 w-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3"
                  />
                </svg>
              </div>

              <div>
                <p className="text-sm font-semibold text-emerald-900">
                  {t('smart_scale_connected')}
                </p>

                <p className="text-sm text-emerald-700">
                  {t('scale_measurement_ready')}
                </p>
              </div>
            </div>

            <p className="text-2xl font-bold tabular-nums text-emerald-700 sm:text-3xl">
              {scaleReading.weight_g} g
            </p>
          </div>
        )}

        {/* Top Metrics */}
        <div
          className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 animate-fade-in-up"
          style={{ animationDelay: '100ms' }}
        >
          <MetricCard
            icon={
              <svg
                className="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9.879 16.121A3 3 0 1012.015 11L11 14H9c0 .768.293 1.536.879 2.121z"
                />
              </svg>
            }
            label={t('daily_calories')}
            value={plan?.daily_calorie_target ?? '—'}
            unit={t('kcal_target')}
          />

          <MetricCard
            icon={
              <svg
                className="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
                />
              </svg>
            }
            label={t('carbohydrates')}
            value={plan?.macro_targets?.carbs_g ?? '—'}
            unit={t('g_target')}
          />

          <MetricCard
            icon={
              <svg
                className="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
            }
            label={t('step_goal')}
            value={plan?.daily_step_goal ?? '—'}
            unit={t('steps')}
          />

          <MetricCard
            icon={
              <svg
                className="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                />
              </svg>
            }
            label={t('glucose_logs')}
            value={recent_glucose_logs?.length ?? 0}
            unit={t('recent_readings')}
          />
        </div>

        {/* Today's Plan */}
        {plan && (
          <div
            className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 animate-fade-in-up"
            style={{ animationDelay: '150ms' }}
          >
            <div className="flex items-center gap-2 mb-10">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-100 text-emerald-600">
                <svg
                  className="h-4 w-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                  />
                </svg>
              </div>

              <h2 className="text-lg font-semibold text-gray-900">
                {t('todays_plan')}
              </h2>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <StatBlock
                label={t('calories')}
                value={plan.daily_calorie_target}
                unit="kcal"
              />

              <StatBlock
                label={t('carbs')}
                value={plan.macro_targets.carbs_g}
                unit="g"
              />

              <StatBlock
                label={t('protein')}
                value={plan.macro_targets.protein_g}
                unit="g"
              />

              <StatBlock
                label={t('steps')}
                value={plan.daily_step_goal}
                unit=""
              />
            </div>
          </div>
        )}

        {/* Glucose + AI Insights */}
        <div className="grid gap-6 lg:grid-cols-3">

          {/* Glucose Trend */}
          <div
            className="lg:col-span-2 bg-white rounded-2xl shadow-sm border border-slate-100 p-6 animate-fade-in-up"
            style={{ animationDelay: '200ms' }}
          >
            <div className="flex items-center gap-2 mb-4">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-rose-100 text-rose-600">
                <svg
                  className="h-4 w-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"
                  />
                </svg>
              </div>

              <h2 className="text-lg font-semibold text-gray-900">
                {t('glucose_trend')}
              </h2>
            </div>

            <GlucoseChart logs={recent_glucose_logs || []} />
          </div>

          {/* AI Insights */}
          <div
            className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 animate-fade-in-up"
            style={{ animationDelay: '250ms' }}
          >
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-100 text-amber-600">
                  <svg
                    className="h-4 w-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M13 10V3L4 14h7v7l9-11h-7z"
                    />
                  </svg>
                </div>

                <h2 className="text-lg font-semibold text-gray-900">
                  {t('insights')}
                </h2>
              </div>

              <button
                onClick={handleRefreshInsights}
                disabled={refreshing}
                className="text-xs font-semibold text-emerald-600 hover:text-emerald-700 disabled:opacity-50 flex items-center gap-1"
              >
                {refreshing ? (
                  <span className="h-3 w-3 animate-spin rounded-full border-2 border-emerald-600 border-t-transparent"></span>
                ) : (
                  <svg
                    className="h-3.5 w-3.5"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                    />
                  </svg>
                )}

                {refreshing
                  ? t('refreshing')
                  : t('refresh')}
              </button>
            </div>

            {recommendations.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-slate-400">
                  <svg
                    className="h-6 w-6"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                    />
                  </svg>
                </div>

                <p className="text-sm font-medium text-gray-900">
                  {t('no_insights_yet')}
                </p>

                <p className="mt-1 text-xs text-gray-500 max-w-[200px]">
                  {t('insights_logging_hint')}
                </p>
              </div>
            ) : (
              <div className="space-y-3 max-h-[400px] overflow-y-auto pr-1 custom-scrollbar">
                {recommendations.map((rec) => (
                  <RecommendationCard
                    key={rec.id}
                    recommendation={rec}
                  />
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Reports */}
        <div
          className="animate-fade-in-up"
          style={{ animationDelay: '300ms' }}
        >
          <ReportsSection patientId={dashboard?.patient_id} />
        </div>

        {/* Quick Actions */}
        <div
          className="grid gap-6 lg:grid-cols-2 animate-fade-in-up"
          style={{ animationDelay: '350ms' }}
        >

          {/* Log Meal */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
            <div className="flex items-center gap-2 mb-4">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-100 text-blue-600">
                <svg
                  className="h-4 w-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 6v6m0 0v6m0-6h6m-6 0H6"
                  />
                </svg>
              </div>

              <h2 className="text-lg font-semibold text-gray-900">
                {t('log_meal')}
              </h2>
            </div>

            <MealLogForm
              onLogged={(meal) =>
                setDashboard((previous) => ({
                  ...previous,
                  recent_meal_logs: [
                    meal,
                    ...previous.recent_meal_logs,
                  ],
                }))
              }
              scaleReading={scaleReading}
            />
          </div>

          {/* Log Activity */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
            <div className="flex items-center gap-2 mb-4">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-orange-100 text-orange-600">
                <svg
                  className="h-4 w-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 10V3L4 14h7v7l9-11h-7z"
                  />
                </svg>
              </div>

              <h2 className="text-lg font-semibold text-gray-900">
                {t('log_activity')}
              </h2>
            </div>

            <ActivityCard
              onLogged={(activity) =>
                setDashboard((previous) => ({
                  ...previous,
                  recent_activity_logs: [
                    activity,
                    ...previous.recent_activity_logs.filter(
                      (item) => item.date !== activity.date
                    ),
                  ],
                }))
              }
            />
          </div>
        </div>

        {/* Recent Lists */}
        <div
          className="grid gap-6 sm:grid-cols-2 animate-fade-in-up"
          style={{ animationDelay: '400ms' }}
        >

          {/* Recent Meals */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <svg
                className="h-5 w-5 text-gray-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>

              {t('recent_meals')}
            </h2>

            {recent_meal_logs?.length === 0 ? (
              <div className="py-6 text-center">
                <p className="text-sm text-gray-500">
                  {t('no_meals_logged')}
                </p>
              </div>
            ) : (
              <ul className="space-y-3">
                {recent_meal_logs?.slice(0, 5).map((meal) => (
                  <li
                    key={meal.id}
                    className="flex items-center justify-between p-3 rounded-xl bg-slate-50 hover:bg-slate-100 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-white text-emerald-600 shadow-sm">
                        <svg
                          className="h-4 w-4"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"
                          />
                        </svg>
                      </div>

                      <div>
                        <p className="text-sm font-medium text-gray-900 capitalize">
                          {meal.meal_type}
                        </p>

                        <p className="text-xs text-gray-500">
                          {new Date(
                            meal.logged_at || Date.now()
                          ).toLocaleDateString()}
                        </p>
                      </div>
                    </div>

                    <span className="text-sm font-semibold text-gray-700">
                      {meal.estimated_carbs ?? '—'} {t('g_carbs')}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Recent Activity */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <svg
                className="h-5 w-5 text-gray-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>

              {t('recent_activity')}
            </h2>

            {recent_activity_logs?.length === 0 ? (
              <div className="py-6 text-center">
                <p className="text-sm text-gray-500">
                  {t('no_activity_logged')}
                </p>
              </div>
            ) : (
              <ul className="space-y-3">
                {recent_activity_logs?.slice(0, 5).map((activity) => (
                  <li
                    key={activity.id}
                    className="flex items-center justify-between p-3 rounded-xl bg-slate-50 hover:bg-slate-100 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-white text-orange-600 shadow-sm">
                        <svg
                          className="h-4 w-4"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M13 10V3L4 14h7v7l-9-11h-7z"
                          />
                        </svg>
                      </div>

                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {activity.date}
                        </p>

                        <p className="text-xs text-gray-500">
                          {t('daily_activity')}
                        </p>
                      </div>
                    </div>

                    <span className="text-sm font-semibold text-gray-700">
                      {activity.steps} {t('steps')}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}


/* =========================================================
   Metric Card
========================================================= */

function MetricCard({ icon, label, value, unit }) {
  return (
    <div className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-center gap-2 mb-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600">
          {icon}
        </div>

        <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          {label}
        </p>
      </div>

      <p className="text-2xl font-bold tabular-nums text-slate-900">
        {value}
      </p>

      <p className="mt-1 text-xs text-slate-500">
        {unit}
      </p>
    </div>
  )
}


/* =========================================================
   Reports Section
========================================================= */

function ReportsSection({ patientId }) {
  const { t } = useTranslation()
  const [generating, setGenerating] = useState(false)

  async function handleGenerateReport() {
    setGenerating(true)

    try {
      await generateAndDownloadReport(patientId)
    } catch (err) {
      console.error('Failed to generate report', err)
      alert(t('report_generation_error'))
    } finally {
      setGenerating(false)
    }
  }

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">

      <h2 className="text-lg font-semibold text-gray-900 mb-4">
        {t('weekly_reports')}
      </h2>

      <p className="text-sm text-gray-500 mb-4">
        {t('weekly_reports_description')}
      </p>

      <button
        onClick={handleGenerateReport}
        disabled={generating}
        className="w-full bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-400 text-white font-semibold py-3 rounded-xl transition-all flex items-center justify-center gap-2"
      >
        {generating ? (
          <>
            <svg
              className="animate-spin h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />

              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              />
            </svg>

            {t('generating_downloading')}
          </>
        ) : (
          <>
            <svg
              className="h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>

            {t('download_weekly_report')}
          </>
        )}
      </button>
    </div>
  )
}


/* =========================================================
   Stat Block
========================================================= */

function StatBlock({ label, value, unit }) {
  return (
    <div className="rounded-xl border border-slate-100 bg-slate-50/50 p-4">
      <p className="text-xs font-medium text-gray-500 mb-1">
        {label}
      </p>

      <p className="text-xl font-bold text-gray-900">
        {value}{' '}

        <span className="text-sm font-normal text-gray-500">
          {unit}
        </span>
      </p>
    </div>
  )
}

export default PatientDashboard