import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getSystemStats, getAllUsers, getAllLinks, deleteUser, assignCaregiver, deleteLink } from '../api/admin'
import { isLoggedIn, getSessionRole, logoutUser } from '../api/auth'

function AdminDashboard() {
  const navigate = useNavigate()
  const [stats, setStats] = useState(null)
  const [users, setUsers] = useState([])
  const [links, setLinks] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  
  // Force Link Form State
  const [caregiverEmail, setCaregiverEmail] = useState('')
  const [patientEmail, setPatientEmail] = useState('')
  const [linkLoading, setLinkLoading] = useState(false)

  useEffect(() => {
    if (!isLoggedIn() || getSessionRole() !== 'admin') {
      navigate('/login', { replace: true })
      return
    }
    loadData()
  }, [navigate])

  async function loadData() {
    try {
      setLoading(true)
      setError('')
      const [statsData, usersData, linksData] = await Promise.all([
        getSystemStats(),
        getAllUsers(),
        getAllLinks()
      ])
      setStats(statsData)
      setUsers(usersData)
      setLinks(linksData)
    } catch (err) {
      setError('Failed to load admin data. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  async function handleDeleteUser(userId, userEmail) {
    if (!window.confirm(`Are you sure you want to permanently delete the account for ${userEmail}? This action cannot be undone.`)) {
      return
    }
    try {
      await deleteUser(userId)
      setUsers((prev) => prev.filter((u) => u.id !== userId))
      setStats((prev) => prev ? { ...prev, total_users: prev.total_users - 1 } : null)
    } catch (err) {
      alert('Failed to delete user. They may have associated records preventing deletion.')
    }
  }

  async function handleDeleteLink(linkId) {
    if (!window.confirm('Are you sure you want to remove this care link?')) return
    try {
      await deleteLink(linkId)
      setLinks((prev) => prev.filter((l) => l.id !== linkId))
      setStats((prev) => prev ? { ...prev, total_care_links: prev.total_care_links - 1 } : null)
    } catch (err) {
      alert('Failed to delete link.')
    }
  }

  async function handleAssignLink(e) {
    e.preventDefault()
    setLinkLoading(true)
    try {
      const caregiver = users.find(u => u.email === caregiverEmail)
      const patient = users.find(u => u.email === patientEmail)
      
      if (!caregiver || !patient) {
        alert('Invalid email addresses selected.')
        return
      }

      await assignCaregiver({
        caregiver_id: caregiver.id,
        patient_id: patient.id,
        link_type: 'family'
      })
      
      alert('Successfully linked caregiver to patient!')
      setCaregiverEmail('')
      setPatientEmail('')
      loadData() // Refresh data
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to assign link.')
    } finally {
      setLinkLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-emerald-200 border-t-emerald-600"></div>
          <p className="text-sm font-medium text-gray-500">Loading system data...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-50/50">
      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 sm:py-10 space-y-8">
        
        {/* Header */}
        <header className="rounded-3xl bg-gradient-to-br from-slate-900 to-slate-800 px-6 py-8 text-white shadow-xl sm:px-8 animate-fade-in-up">
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-emerald-400/80">DIAZO · Admin Console</p>
          <div className="mt-4 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">System Overview</h1>
              <p className="mt-2 text-sm text-slate-300 max-w-md">Monitor user accounts, manage care links, and oversee system health.</p>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={loadData}
                className="flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/20 rounded-xl text-sm font-medium transition-all ring-1 ring-inset ring-white/10"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                <span>Refresh</span>
              </button>
              <button
                onClick={() => { logoutUser(); window.location.replace('/login') }}
                className="flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/20 rounded-xl text-sm font-medium transition-all ring-1 ring-inset ring-white/10"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
                <span>Logout</span>
              </button>
            </div>
          </div>
        </header>

        {error && (
          <div className="p-4 bg-red-50 border border-red-100 rounded-xl text-red-600 text-sm flex items-center gap-2 animate-fade-in-up">
            <svg className="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {error}
          </div>
        )}

        {/* Stats Grid */}
        {stats && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 animate-fade-in-up" style={{ animationDelay: '100ms' }}>
            <StatCard label="Total Users" value={stats.total_users} icon="users" color="emerald" />
            <StatCard label="Total Care Links" value={stats.total_care_links} icon="link" color="blue" />
            <StatCard label="Patients" value={stats.users_by_role?.patient || 0} icon="heart" color="rose" />
            <StatCard label="Caregivers" value={(stats.users_by_role?.caregiver || 0) + (stats.users_by_role?.doctor || 0)} icon="shield" color="amber" />
          </div>
        )}

        {/* Main Content Grid */}
        <div className="grid gap-6 lg:grid-cols-2 animate-fade-in-up" style={{ animationDelay: '200ms' }}>
          
          {/* Users Table */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 overflow-hidden">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-100 text-emerald-600">
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                </div>
                System Users
              </h2>
              <span className="text-xs font-medium text-gray-500 bg-slate-100 px-2 py-1 rounded-full">
                {users.length} total
              </span>
            </div>
            
            <div className="overflow-x-auto max-h-[400px] overflow-y-auto custom-scrollbar">
              {users.length === 0 ? (
                <div className="py-8 text-center text-sm text-gray-500">No users found in the system.</div>
              ) : (
                <table className="w-full text-sm text-left">
                  <thead className="text-xs text-gray-500 uppercase bg-slate-50 sticky top-0 z-10">
                    <tr>
                      <th className="px-4 py-3">Email</th>
                      <th className="px-4 py-3">Role</th>
                      <th className="px-4 py-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {users.map((user) => (
                      <tr key={user.id} className="hover:bg-slate-50 transition-colors">
                        <td className="px-4 py-3 font-medium text-gray-900">
                          {user.email}
                          {user.full_name && <span className="block text-xs text-gray-500 font-normal">{user.full_name}</span>}
                        </td>
                        <td className="px-4 py-3">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize
                            ${user.role === 'admin' ? 'bg-purple-100 text-purple-800' : 
                              user.role === 'caregiver' || user.role === 'doctor' ? 'bg-amber-100 text-amber-800' : 
                              'bg-emerald-100 text-emerald-800'}`}>
                            {user.role}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-right">
                          {user.role !== 'admin' && (
                            <button 
                              onClick={() => handleDeleteUser(user.id, user.email)}
                              className="text-red-500 hover:text-red-700 text-xs font-semibold transition-colors"
                            >
                              Delete
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>

          {/* Care Links Management */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 overflow-hidden flex flex-col">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-100 text-blue-600">
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                  </svg>
                </div>
                Care Links
              </h2>
              <span className="text-xs font-medium text-gray-500 bg-slate-100 px-2 py-1 rounded-full">
                {links.length} total
              </span>
            </div>

            {/* Force Link Form */}
            <form onSubmit={handleAssignLink} className="mb-6 p-4 bg-slate-50 rounded-xl border border-slate-200">
              <h3 className="text-sm font-semibold text-gray-900 mb-3">Manually Link Caregiver to Patient</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-3">
                <select 
                  value={caregiverEmail} 
                  onChange={(e) => setCaregiverEmail(e.target.value)}
                  required
                  className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                >
                  <option value="">Select Caregiver/Doctor</option>
                  {users.filter(u => u.role === 'caregiver' || u.role === 'doctor').map(u => (
                    <option key={u.id} value={u.email}>{u.email} ({u.full_name || 'No Name'})</option>
                  ))}
                </select>
                <select 
                  value={patientEmail} 
                  onChange={(e) => setPatientEmail(e.target.value)}
                  required
                  className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                >
                  <option value="">Select Patient</option>
                  {users.filter(u => u.role === 'patient').map(u => (
                    <option key={u.id} value={u.email}>{u.email} ({u.full_name || 'No Name'})</option>
                  ))}
                </select>
              </div>
              <button 
                type="submit" 
                disabled={linkLoading || !caregiverEmail || !patientEmail}
                className="w-full sm:w-auto px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-lg transition-colors disabled:opacity-50"
              >
                {linkLoading ? 'Linking...' : 'Force Link & Approve'}
              </button>
            </form>
            
            <div className="overflow-x-auto max-h-[300px] overflow-y-auto custom-scrollbar flex-1">
              {links.length === 0 ? (
                <div className="py-8 text-center text-sm text-gray-500">No care links established yet.</div>
              ) : (
                <table className="w-full text-sm text-left">
                  <thead className="text-xs text-gray-500 uppercase bg-slate-50 sticky top-0 z-10">
                    <tr>
                      <th className="px-4 py-3">Caregiver</th>
                      <th className="px-4 py-3">Patient</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {links.map((link) => (
                      <tr key={link.id} className="hover:bg-slate-50 transition-colors">
                        <td className="px-4 py-3">
                          <div className="font-medium text-gray-900 text-xs">{link.caregiver_email}</div>
                          <div className="text-[10px] text-gray-500">{link.caregiver_name}</div>
                        </td>
                        <td className="px-4 py-3">
                          <div className="font-medium text-gray-900 text-xs">{link.patient_email}</div>
                          <div className="text-[10px] text-gray-500">{link.patient_name}</div>
                        </td>
                        <td className="px-4 py-3">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize
                            ${link.status === 'approved' ? 'bg-emerald-100 text-emerald-800' : 
                              link.status === 'pending' ? 'bg-amber-100 text-amber-800' : 
                              'bg-red-100 text-red-800'}`}>
                            {link.status}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-right">
                          <button 
                            onClick={() => handleDeleteLink(link.id)}
                            className="text-red-500 hover:text-red-700 text-xs font-semibold transition-colors"
                          >
                            Remove
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}

// Helper Stat Card Component
function StatCard({ label, value, icon, color }) {
  const colors = {
    emerald: 'bg-emerald-50 text-emerald-600',
    blue: 'bg-blue-50 text-blue-600',
    rose: 'bg-rose-50 text-rose-600',
    amber: 'bg-amber-50 text-amber-600',
  }
  
  const icons = {
    users: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />,
    link: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />,
    heart: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />,
    shield: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />,
  }

  return (
    <div className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-center gap-2 mb-3">
        <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${colors[color]}`}>
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            {icons[icon]}
          </svg>
        </div>
        <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">{label}</p>
      </div>
      <p className="text-2xl font-bold tabular-nums text-slate-900">{value}</p>
    </div>
  )
}

export default AdminDashboard