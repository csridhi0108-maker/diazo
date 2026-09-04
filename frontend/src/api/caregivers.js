import client from './client'

export async function getMyPatients() {
  const { data } = await client.get('/api/v1/caregivers/my-patients')
  return data
}

export async function sendLinkRequest(patientEmail, linkType) {
  const { data } = await client.post('/api/v1/caregivers/link-request', {
    patient_email: patientEmail,
    link_type: linkType,
  })
  return data
}

// Add these to the bottom of frontend/src/api/caregivers.js

export async function getPendingRequests() {
  const { data } = await client.get('/api/v1/caregivers/link-requests/pending')
  return data
}

export async function respondToRequest(linkId, approve) {
  const { data } = await client.patch(`/api/v1/caregivers/link-request/${linkId}`, {
    approve: approve, // true = approve, false = reject
  })
  return data
}

export async function getPatientDashboard(patientId) {
  const { data } = await client.get(`/api/v1/caregiver/patient/${patientId}/dashboard`)
  return data
}