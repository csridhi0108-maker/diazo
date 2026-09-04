import { useEffect, useState } from 'react'
import { generateReport, listReports } from '../api/reports'

function ReportsSection({ patientId }) {
  const [reports, setReports] = useState([])
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    load()
  }, [patientId])

  async function load() {
    try {
      const data = await listReports(patientId)
      setReports(data)
    } catch {
      // Silent — empty state handles it
    }
  }

  async function handleGenerate() {
    setGenerating(true)
    setError('')
    try {
      const report = await generateReport(patientId)
      setReports((prev) => [report, ...prev])
    } catch {
      setError('Could not generate report.')
    } finally {
      setGenerating(false)
    }
  }

  return (
    <div className="bg-white rounded-2xl shadow-sm p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-medium text-gray-800">Weekly Reports</h2>
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="text-sm bg-primary-500 hover:bg-primary-600 text-white font-medium px-3 py-1.5 rounded-lg transition-colors disabled:opacity-50"
        >
          {generating ? 'Generating...' : 'Generate report'}
        </button>
      </div>

      {error && <p className="text-red-500 text-sm mb-2">{error}</p>}

      {reports.length === 0 ? (
        <p className="text-gray-400 text-sm">No reports yet. Generate one to see a summary.</p>
      ) : (
        <div className="space-y-3">
          {reports.map((report) => (
            <div key={report.id} className="border border-gray-100 rounded-xl p-4">
              <p className="text-xs text-gray-400 mb-2">
                {report.period_start} — {report.period_end}
              </p>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <p>Avg glucose: <span className="font-medium">{report.summary_data.avg_glucose ?? '—'} mg/dL</span></p>
                <p>Trend: <span className="font-medium capitalize">{report.summary_data.glucose_trend}</span></p>
                <p>Glucose logging: <span className="font-medium">{report.summary_data.glucose_adherence_pct}%</span></p>
                <p>Meal logging: <span className="font-medium">{report.summary_data.meal_adherence_pct}%</span></p>
                <p>Current weight: <span className="font-medium">{report.summary_data.current_weight_kg ?? '—'} kg</span></p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default ReportsSection