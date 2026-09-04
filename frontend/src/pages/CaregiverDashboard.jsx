import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getMyPatients, sendLinkRequest } from '../api/caregivers'
import { isLoggedIn, getSessionRole, logoutUser } from '../api/auth'
import NotificationBell from '../components/NotificationBell'

function CaregiverDashboard() {
  const navigate = useNavigate()
  const [patients, setPatients] = useState([])
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(true)
  const [requesting, setRequesting] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    if (!isLoggedIn() || !['caregiver', 'doctor'].includes(getSessionRole())) {
      navigate('/login', { replace: true })
    } else {
      loadPatients()
    }
  }, [navigate])

  async function loadPatients() {
    try {
      const data = await getMyPatients()
      setPatients(data)
    } catch (err) {
      setError('Failed to load patient list.')
    } finally {
      setLoading(false)
    }
  }

  async function handleRequest(e) {
    e.preventDefault()
    setRequesting(true)
    setError('')
    setSuccess('')
    try {
      await sendLinkRequest(email, 'family')
      setSuccess(`Request sent to ${email}! They must approve it before you can see their data.`)
      setEmail('')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to send request. Check the email.')
    } finally {
      setRequesting(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <p className="text-gray-500">Loading dashboard...</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-50/50">
      <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 sm:py-10 space-y-8">

        {/* Header - WITHOUT the notification bell */}
        <header className="rounded-3xl bg-gradient-to-br from-blue-900 to-slate-900 px-6 py-8 text-white shadow-xl sm:px-8 animate-fade-in-up">
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-blue-300/80">DIAZO · Caregiver Portal</p>
          <div className="mt-4 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">Care Dashboard</h1>
              <p className="mt-2 text-sm text-slate-300 max-w-md">Monitor your patients and manage care links.</p>
            </div>
            <div className="flex items-center gap-3">
              {/* Logout only - Bell moved outside header */}
              <button
                onClick={() => { logoutUser(); window.location.replace('/login') }}
                className="flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/20 rounded-xl text-sm font-medium transition-all ring-1 ring-inset ring-white/10 w-fit"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
                Logout
              </button>
            </div>
          </div>
        </header>

        {/* Notification Bell - OUTSIDE header so it's not clipped */}
        <div className="flex justify-end -mt-16 mb-4 pr-2 relative" style={{ zIndex: 10000 }}>
          <NotificationBell />
        </div>

        {/* Request Access Section */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 animate-fade-in-up" style={{ animationDelay: '100ms' }}>
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-100 text-blue-600">
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
              </svg>
            </div>
            Connect with a Patient
          </h2>
          <form onSubmit={handleRequest} className="flex gap-3">
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="Enter patient's email address"
              className="flex-1 px-4 py-3 bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 transition-all text-gray-900 placeholder-gray-400"
            />
            <button
              type="submit"
              disabled={requesting}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl transition-all disabled:opacity-50"
            >
              {requesting ? 'Sending...' : 'Send Request'}
            </button>
          </form>
          {error && <div className="mt-3 p-3 bg-red-50 border border-red-100 rounded-xl text-red-600 text-sm">{error}</div>}
          {success && <div className="mt-3 p-3 bg-emerald-50 border border-emerald-100 rounded-xl text-emerald-700 text-sm">{success}</div>}
        </div>

        {/* Patients List */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 animate-fade-in-up" style={{ animationDelay: '200ms' }}>
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-100 text-emerald-600">
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
            My Patients ({patients.length})
          </h2>

          {patients.length === 0 ? (
            <div className="py-12 text-center">
              <div className="inline-flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-slate-400 mb-3">
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              </div>
              <p className="text-sm font-medium text-gray-900">No patients connected yet</p>
              <p className="mt-1 text-xs text-gray-500">Use the form above to request access to a patient.</p>
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {patients.map((link) => (
                <div
                  key={link.link_id}
                  onClick={() => navigate(`/caregiver/patient/${link.patient_id}`)}
                  className="p-4 border border-slate-200 rounded-xl hover:shadow-md hover:border-emerald-300 transition-all cursor-pointer bg-white group"
                >
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-700 font-bold group-hover:bg-emerald-200 transition-colors">
                      {(link.patient_name || link.patient_email).charAt(0).toUpperCase()}
                    </div>
                    <div className="overflow-hidden">
                      <p className="text-sm font-semibold text-gray-900 truncate">
                        {link.patient_name || 'Unknown Patient'}
                      </p>
                      <p className="text-xs text-gray-500 truncate">{link.patient_email}</p>
                    </div>
                  </div>
                  <div className="mt-3 pt-3 border-t border-slate-100 flex justify-between items-center">
                    <span className="text-xs font-medium text-emerald-600 bg-emerald-50 px-2 py-1 rounded-full capitalize">
                      {link.status}
                    </span>
                    <span className="text-xs text-gray-400 capitalize flex items-center gap-1">
                      {link.link_type}
                      <svg className="h-3 w-3 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

      </div>
    </div>
  )
}

export default CaregiverDashboard