import { useState } from 'react'
import { upsertActivityLog } from '../api/logs.js'

const today = () => new Date().toISOString().slice(0, 10)

function ActivityCard({ onLogged }) {
  const [date, setDate] = useState(today)
  const [steps, setSteps] = useState('')
  const [caloriesBurned, setCaloriesBurned] = useState('')
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setSaving(true)
    try {
      const activity = await upsertActivityLog({
        date,
        steps: Number(steps),
        calories_burned: Number(caloriesBurned),
      })
      onLogged?.(activity)
    } catch (requestError) {
      setError(requestError.response?.data?.detail || 'Could not save your activity.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <section className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
      <div className="mb-4"><p className="text-xs font-semibold uppercase tracking-widest text-emerald-600">Movement</p><h2 className="mt-1 text-lg font-semibold text-slate-900">Log today’s activity</h2></div>
      <form onSubmit={handleSubmit} className="grid gap-3 sm:grid-cols-3">
        <label className="text-sm font-medium text-slate-700">Date
          <input type="date" value={date} onChange={(event) => setDate(event.target.value)} required className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2.5" />
        </label>
        <label className="text-sm font-medium text-slate-700">Steps
          <input type="number" min="0" value={steps} onChange={(event) => setSteps(event.target.value)} required className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2.5" />
        </label>
        <label className="text-sm font-medium text-slate-700">Calories burned
          <input type="number" min="0" step="0.1" value={caloriesBurned} onChange={(event) => setCaloriesBurned(event.target.value)} required className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2.5" />
        </label>
        {error && <p className="text-sm text-red-600 sm:col-span-3">{error}</p>}
        <button disabled={saving} className="w-fit rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:opacity-50">
          {saving ? 'Saving…' : 'Save activity'}
        </button>
      </form>
    </section>
  )
}

export default ActivityCard
