import { useEffect } from 'react'
import { Navigate, Route, Routes, useNavigate } from 'react-router-dom'
import Landing from './pages/Landing.jsx'
import CaregiverDashboard from './pages/CaregiverDashboard.jsx'
import CaregiverOnboarding from './pages/CaregiverOnboarding.jsx' // <-- ADDED THIS
import Login from './pages/Login.jsx'
import Onboarding from './pages/Onboarding.jsx'
import PatientDashboard from './pages/PatientDashboard.jsx'
import AdminDashboard from './pages/AdminDashboard.jsx'
import GlucoseTracker from './pages/GlucoseTracker.jsx'
import CaregiverPatientView from './pages/CaregiverPatientView.jsx'
import { getSessionRole, isLoggedIn } from './api/auth.js'

function RequireAuth({ children, roles }) {
  const navigate = useNavigate()
  const isAuth = isLoggedIn()
  const role = getSessionRole()

  // This effect forces a redirect even if the browser loads the page from bfcache (back button)
  useEffect(() => {
    if (!isAuth) {
      navigate('/login', { replace: true })
    } else if (roles && !roles.includes(role)) {
      navigate('/', { replace: true })
    }
  }, [isAuth, role, roles, navigate])

  if (!isAuth) {
    return <Navigate to="/login" replace />
  }

  if (roles && !roles.includes(role)) {
    return <Navigate to="/" replace />
  }

  return children
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      
      {/* Patient Routes */}
      <Route
        path="/dashboard"
        element={
          <RequireAuth roles={['patient']}>
            <PatientDashboard />
          </RequireAuth>
        }
      />
      <Route
        path="/onboarding"
        element={
          <RequireAuth roles={['patient']}>
            <Onboarding />
          </RequireAuth>
        }
      />
      <Route
        path="/glucose-tracker"
        element={
          <RequireAuth roles={['patient']}>
            <GlucoseTracker />
          </RequireAuth>
        }
      />

      {/* Caregiver/Doctor Routes */}
      <Route
        path="/caregiver-onboarding"
        element={
          <RequireAuth roles={['caregiver', 'doctor']}>
            <CaregiverOnboarding />
          </RequireAuth>
        }
      />
      <Route
        path="/caregiver-dashboard"
        element={
          <RequireAuth roles={['caregiver', 'doctor']}>
            <CaregiverDashboard />
          </RequireAuth>
        }
      />

      {/* Admin Routes */}
      <Route
        path="/admin-dashboard"
        element={
          <RequireAuth roles={['admin']}>
            <AdminDashboard />
          </RequireAuth>
        }
      />
      
      <Route
  path="/caregiver/patient/:patientId"
  element={
    <RequireAuth roles={['caregiver', 'doctor']}>
      <CaregiverPatientView />
    </RequireAuth>
  }
/>



      {/* Catch-all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App