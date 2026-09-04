import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getPatientDashboard } from '../api/caregivers'
import { isLoggedIn, getSessionRole, logoutUser } from '../api/auth'
import GlucoseChart from '../components/GlucoseChart'

function CaregiverPatientView() {
  const { patientId } = useParams()
  const navigate = useNavigate()
  const [dashboard, setDashboard] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!isLoggedIn() || !['caregiver', 'doctor'].includes(getSessionRole())) {
      navigate('/login', { replace: true })
      return
    }
    loadPatientData()
  }, [patientId, navigate])

  async function loadPatientData() {
    try {
      const data = await getPatientDashboard(patientId)
      setDashboard(data)
    } catch (err) {
      setError('Could not load patient data. You may not have permission.')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-200 border-t-blue-600"></div>
          <p className="text-sm font-medium text-gray-500">Loading patient data...</p>
        </div>
      </div>
    )
  }

  if (error || !dashboard) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
        <div className="bg-white p-8 rounded-2xl shadow-sm text-center max-w-sm border border-red-100">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-red-50 mb-4">
            <svg className="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <p className="text-gray-700 font-medium">{error}</p>
          <button onClick={() => navigate('/caregiver-dashboard')} className="mt-4 text-sm text-blue-600 hover:text-blue-700 font-semibold">
            Back to Dashboard
          </button>
        </div>
      </div>
    )
  }

  const { patient_name, plan, recent_glucose_logs, recent_meal_logs, recent_activity_logs } = dashboard

  return (
    <div className="min-h-screen bg-slate-50/50">
      <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 sm:py-10 space-y-6">
        
        {/* Header */}
        <header className="rounded-3xl bg-gradient-to-br from-blue-900 to-slate-900 px-6 py-8 text-white shadow-xl sm:px-8">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-blue-300/80">DIAZO · Caregiver View</p>
              <h1 className="mt-2 text-3xl font-bold tracking-tight">
                {patient_name || 'Patient Dashboard'}
              </h1>
              <p className="mt-2 text-sm text-slate-300 max-w-md">View-only access to patient health data.</p>
            </div>
            <button
              onClick={() => navigate('/caregiver-dashboard')}
              className="flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/20 rounded-xl text-sm font-medium transition-all"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              <span>Back to Dashboard</span>
            </button>
          </div>
        </header>

        {/* Top Metrics */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <MetricCard label="Daily Calories" value={plan?.daily_calorie_target ?? '—'} unit="kcal target" />
          <MetricCard label="Carbohydrates" value={plan?.macro_targets?.carbs_g ?? '—'} unit="g target" />
          <MetricCard label="Step Goal" value={plan?.daily_step_goal ?? '—'} unit="steps" />
          <MetricCard label="Glucose Logs" value={recent_glucose_logs?.length ?? 0} unit="recent readings" />
        </div>

        {/* Glucose Trend */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
          <div className="flex items-center gap-2 mb-4">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-rose-100 text-rose-600">
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
              </svg>
            </div>
            <h2 className="text-lg font-semibold text-gray-900">Glucose Trend</h2>
          </div>
          <GlucoseChart logs={recent_glucose_logs || []} />
        </div>

        {/* Recent Meals & Activity */}
        <div className="grid gap-6 sm:grid-cols-2">
          <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Meals</h2>
            {recent_meal_logs?.length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-6">No meals logged yet</p>
            ) : (
              <ul className="space-y-3">
                {recent_meal_logs?.slice(0, 5).map((meal) => (
                  <li key={meal.id} className="flex items-center justify-between p-3 rounded-xl bg-slate-50">
                    <div>
                      <p className="text-sm font-medium text-gray-900 capitalize">{meal.meal_type}</p>
                      <p className="text-xs text-gray-500">{new Date(meal.logged_at).toLocaleDateString()}</p>
                    </div>
                    <span className="text-sm font-semibold text-gray-700">{meal.estimated_carbs ?? '—'}g carbs</span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h2>
            {recent_activity_logs?.length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-6">No activity logged yet</p>
            ) : (
              <ul className="space-y-3">
                {recent_activity_logs?.slice(0, 5).map((activity) => (
                  <li key={activity.id} className="flex items-center justify-between p-3 rounded-xl bg-slate-50">
                    <div>
                      <p className="text-sm font-medium text-gray-900">{activity.date}</p>
                      <p className="text-xs text-gray-500">Daily steps</p>
                    </div>
                    <span className="text-sm font-semibold text-gray-700">{activity.steps} steps</span>
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

function MetricCard({ label, value, unit }) {
  return (
    <div className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3">{label}</p>
      <p className="text-2xl font-bold tabular-nums text-slate-900">{value}</p>
      <p className="mt-1 text-xs text-slate-500">{unit}</p>
    </div>
  )
}

export default CaregiverPatientView