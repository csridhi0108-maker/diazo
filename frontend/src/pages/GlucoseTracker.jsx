import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { isLoggedIn, getSessionRole, logoutUser } from '../api/auth'
import { getGlucoseLogs, createGlucoseLog } from '../api/dashboard'
import GlucoseChart from '../components/GlucoseChart'
import LanguageSwitcher from '../components/LanguageSwitcher'

function GlucoseTracker() {
  const navigate = useNavigate()
  const { t } = useTranslation()

  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  // Form State
  const [value, setValue] = useState('')
  const [context, setContext] = useState('fasting')
  const [logTime, setLogTime] = useState(
    new Date().toISOString().slice(0, 16)
  )

  // Security check
  useEffect(() => {
    if (!isLoggedIn() || getSessionRole() !== 'patient') {
      navigate('/login', { replace: true })
    }
  }, [navigate])

  // Fetch logs
  useEffect(() => {
    loadLogs()
  }, [])

  async function loadLogs() {
    try {
      setLoading(true)

      const data = await getGlucoseLogs()

      setLogs(data || [])
    } catch (err) {
      console.error('Failed to load logs', err)

      setError(t('glucose_load_error'))

      setLogs([])
    } finally {
      setLoading(false)
    }
  }

  async function handleAddLog(e) {
    e.preventDefault()

    setError('')
    setSaving(true)

    try {
      const newLog = await createGlucoseLog({
        value: Number(value),
        context_tag: context,
        timestamp: logTime || undefined
      })

      setLogs([newLog, ...logs])
      setValue('')
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        t('glucose_save_error')
      )
    } finally {
      setSaving(false)
    }
  }

  // Calculate Stats
  const stats =
    logs.length > 0
      ? {
          avg: Math.round(
            logs.reduce((acc, curr) => acc + curr.value, 0) /
              logs.length
          ),
          max: Math.max(...logs.map((l) => l.value)),
          min: Math.min(...logs.map((l) => l.value)),
          inRange: logs.filter(
            (l) => l.value >= 70 && l.value <= 180
          ).length
        }
      : {
          avg: 0,
          max: 0,
          min: 0,
          inRange: 0
        }

  const inRangePercentage =
    logs.length > 0
      ? Math.round(
          (stats.inRange / logs.length) * 100
        )
      : 0

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-emerald-200 border-t-emerald-600"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-50/50">
      <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 sm:py-10 space-y-6">

        {/* Header */}
        <header className="flex items-center justify-between animate-fade-in-up">

          <div className="flex items-center gap-4">

            <button
              onClick={() => navigate('/dashboard')}
              className="flex h-10 w-10 items-center justify-center rounded-xl bg-white border border-slate-200 text-slate-600 hover:bg-slate-50 transition-colors shadow-sm"
              aria-label={t('back')}
            >
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
                  d="M10 19l-7-7m0 0l7-7m-7 7h18"
                />
              </svg>
            </button>

            <div>
              <h1 className="text-2xl font-bold text-gray-900 sm:text-3xl">
                {t('glucose_tracker')}
              </h1>

              <p className="text-sm text-gray-500">
                {t('glucose_tracker_description')}
              </p>
            </div>
          </div>

          {/* Header Actions */}
          <div className="flex items-center gap-2">

            {/* Light-theme language switcher */}
            <div className="rounded-xl">
              <LanguageSwitcher light />
            </div>

            <button
              onClick={() => {
                logoutUser()
                window.location.replace('/login')
              }}
              className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-xl text-sm font-medium text-slate-600 hover:bg-slate-50 transition-all shadow-sm"
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

              <span className="hidden sm:inline">
                {t('logout')}
              </span>
            </button>

          </div>
        </header>

        {/* Stats Overview */}
        <div
          className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 animate-fade-in-up"
          style={{ animationDelay: '100ms' }}
        >
          <StatCard
            label={t('average')}
            value={stats.avg || '—'}
            unit="mg/dL"
            color="emerald"
          />

          <StatCard
            label={t('highest')}
            value={stats.max || '—'}
            unit="mg/dL"
            color="rose"
          />

          <StatCard
            label={t('lowest')}
            value={stats.min || '—'}
            unit="mg/dL"
            color="blue"
          />

          <StatCard
            label={t('time_in_range')}
            value={`${inRangePercentage}%`}
            unit="70-180 mg/dL"
            color="amber"
          />
        </div>

        <div className="grid gap-6 lg:grid-cols-3">

          {/* Left Column */}
          <div className="lg:col-span-2 space-y-6">

            {/* Add Reading Form */}
            <div
              className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 animate-fade-in-up"
              style={{ animationDelay: '150ms' }}
            >

              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">

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
                      d="M12 4v16m8-8H4"
                    />
                  </svg>
                </div>

                {t('log_new_reading')}
              </h2>

              <form
                onSubmit={handleAddLog}
                className="grid gap-4 sm:grid-cols-4"
              >

                {/* Value */}
                <div className="sm:col-span-1">

                  <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                    {t('value_mgdl')}
                  </label>

                  <input
                    type="number"
                    value={value}
                    onChange={(e) => setValue(e.target.value)}
                    required
                    min="20"
                    max="600"
                    placeholder="120"
                    className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all font-semibold text-gray-900"
                  />

                </div>

                {/* Context */}
                <div className="sm:col-span-1">

                  <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                    {t('context')}
                  </label>

                  <select
                    value={context}
                    onChange={(e) => setContext(e.target.value)}
                    className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all text-gray-900 appearance-none"
                  >
                    <option value="fasting">
                      {t('fasting')}
                    </option>

                    <option value="before_meal">
                      {t('before_meal')}
                    </option>

                    <option value="after_meal">
                      {t('after_meal')}
                    </option>

                    <option value="bedtime">
                      {t('bedtime')}
                    </option>

                    <option value="random">
                      {t('random')}
                    </option>
                  </select>

                </div>

                {/* Time */}
                <div className="sm:col-span-1">

                  <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                    {t('time')}
                  </label>

                  <input
                    type="datetime-local"
                    value={logTime}
                    onChange={(e) => setLogTime(e.target.value)}
                    required
                    className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all text-gray-900"
                  />

                </div>

                {/* Save Button */}
                <div className="sm:col-span-1 flex items-end">

                  <button
                    type="submit"
                    disabled={saving}
                    className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-2.5 rounded-xl transition-all shadow-md shadow-emerald-500/20 disabled:opacity-50 flex items-center justify-center gap-2"
                  >

                    {saving ? (
                      <svg
                        className="animate-spin h-4 w-4"
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
                    ) : (
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
                          d="M12 4v16m8-8H4"
                        />
                      </svg>
                    )}

                    {saving
                      ? t('saving')
                      : t('save_reading')}

                  </button>

                </div>
              </form>

              {/* Error */}
              {error && (
                <p className="mt-3 text-sm text-red-600 flex items-center gap-2">

                  <svg
                    className="w-4 h-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>

                  {error}

                </p>
              )}

            </div>

            {/* Glucose Chart */}
            <div
              className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 animate-fade-in-up"
              style={{ animationDelay: '200ms' }}
            >

              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                {t('trend_overview')}
              </h2>

              {logs.length === 0 ? (
                <div className="py-12 text-center text-gray-500 bg-slate-50 rounded-xl border border-dashed border-slate-200">
                  {t('no_glucose_readings')}
                </div>
              ) : (
                <GlucoseChart logs={logs} />
              )}

            </div>

          </div>

          {/* Right Column: History */}
          <div
            className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 animate-fade-in-up"
            style={{ animationDelay: '250ms' }}
          >

            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              {t('recent_history')}
            </h2>

            {logs.length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-8">
                {t('no_history')}
              </p>
            ) : (
              <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2 custom-scrollbar">

                {logs.map((log) => (
                  <div
                    key={log.id}
                    className="p-4 rounded-xl bg-slate-50 border border-slate-100 hover:border-emerald-200 transition-colors"
                  >

                    <div className="flex items-center justify-between mb-2">

                      <span
                        className={`text-xl font-bold ${
                          log.value > 180
                            ? 'text-rose-600'
                            : log.value < 70
                              ? 'text-blue-600'
                              : 'text-emerald-600'
                        }`}
                      >
                        {log.value}
                      </span>

                      <span className="text-xs text-gray-400">
                        mg/dL
                      </span>

                    </div>

                    <div className="flex items-center justify-between text-xs">

                      <span className="px-2 py-1 bg-white rounded-md text-gray-600 font-medium capitalize border border-slate-100">
                        {log.context_tag
                          ? t(log.context_tag)
                          : t('no_context')}
                      </span>

                      <span className="text-gray-500">
                        {new Date(
                          log.timestamp
                        ).toLocaleDateString()}{' '}

                        {new Date(
                          log.timestamp
                        ).toLocaleTimeString([], {
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </span>

                    </div>

                  </div>
                ))}

              </div>
            )}

          </div>

        </div>
      </div>
    </div>
  )
}


function StatCard({
  label,
  value,
  unit,
  color
}) {
  const colors = {
    emerald: 'bg-emerald-50 text-emerald-600',
    rose: 'bg-rose-50 text-rose-600',
    blue: 'bg-blue-50 text-blue-600',
    amber: 'bg-amber-50 text-amber-600'
  }

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-5 hover:shadow-md transition-shadow">

      <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">
        {label}
      </p>

      <div className="flex items-baseline gap-2">

        <p
          className={`text-3xl font-bold ${
            colors[color].split(' ')[1]
          }`}
        >
          {value}
        </p>

        <p className="text-xs text-slate-500">
          {unit}
        </p>

      </div>

    </div>
  )
}


export default GlucoseTracker