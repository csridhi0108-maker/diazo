/**
 * Wrapper for the dashboard aggregation endpoint, patient profile,
 * recommendation recompute, and glucose logging endpoints.
 */

import client from './client'

export async function getDashboard(patientId) {
  const { data } = await client.get(`/api/v1/dashboard/${patientId}`)
  return data
}

export async function refreshRecommendations(patientId) {
  const { data } = await client.get(`/api/v1/ml/recommendations/${patientId}`)
  return data
}

export async function getMyProfile() {
  const { data } = await client.get('/api/v1/patients/me')
  return data
}

// --- NEW: Glucose Logging Functions ---

export async function getGlucoseLogs() {
  // NOTE: Adjust this endpoint if your backend uses a different path, 
  // e.g., '/api/v1/patients/me/glucose-logs'
  const { data } = await client.get('/api/v1/glucose-logs')
  return data
}

export async function createGlucoseLog(payload) {
  // NOTE: Adjust this endpoint if your backend uses a different path
  const { data } = await client.post('/api/v1/glucose-logs', payload)
  return data
}