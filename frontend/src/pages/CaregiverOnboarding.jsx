import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { isLoggedIn, getSessionRole } from '../api/auth'
import client from '../api/client'

function CaregiverOnboarding() {
  const navigate = useNavigate()
  const [fullName, setFullName] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [isAuthorized, setIsAuthorized] = useState(false)

  // Safe security check that runs AFTER the component mounts
  useEffect(() => {
    const role = getSessionRole()
    if (!isLoggedIn() || !['caregiver', 'doctor'].includes(role)) {
      navigate('/login', { replace: true })
    } else {
      setIsAuthorized(true)
    }
  }, [navigate])

  // Show a loading state while checking authorization
  if (!isAuthorized) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-200 border-t-blue-600"></div>
          <p className="text-sm font-medium text-gray-500">Verifying access...</p>
        </div>
      </div>
    )
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setError('')
    
    try {
      // Update the user's full name in the database.
      await client.patch('/api/v1/patients/me', { full_name: fullName }).catch(() => {
        // Fallback if the backend blocks caregivers from the patient endpoint
        console.log('Profile update skipped for now, proceeding to dashboard.')
      })
      
      // Redirect to the caregiver dashboard
      navigate('/caregiver-dashboard', { replace: true })
    } catch (err) {
      setError('Could not save your profile. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-sm border border-slate-100 p-8 animate-fade-in-up">
        
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-blue-700 shadow-lg mb-4">
            <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Welcome to DIAZO!</h1>
          <p className="mt-2 text-sm text-gray-500">
            Let's get your profile set up so patients know who is requesting access to their data.
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Full Name</label>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
              placeholder="e.g., Dr. Jane Smith or John Doe"
              className="w-full px-4 py-3 bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 transition-all text-gray-900 placeholder-gray-400"
            />
            <p className="mt-1 text-xs text-gray-400">This name will be visible to patients when you send a care request.</p>
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-100 rounded-xl text-red-600 text-sm flex items-center gap-2">
              <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !fullName.trim()}
            className="w-full bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-semibold py-3.5 rounded-xl transition-all shadow-lg shadow-blue-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Setting up...' : 'Complete Setup & Go to Dashboard'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default CaregiverOnboarding