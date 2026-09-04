import client from './client.js'

export function getSystemStats() {
  return client.get('/api/v1/admin/stats').then((res) => res.data)
}

export function getAllUsers() {
  return client.get('/api/v1/admin/users').then((res) => res.data)
}

export function getAllLinks() {
  return client.get('/api/v1/admin/links').then((res) => res.data)
}

export function deleteUser(userId) {
  return client.delete(`/api/v1/admin/users/${userId}`)
}

// NEW: Assign a caregiver to a patient
export function assignCaregiver(data) {
  return client.post('/api/v1/admin/assign-link', data).then((res) => res.data)
}

// NEW: Delete a care link
export function deleteLink(linkId) {
  return client.delete(`/api/v1/admin/links/${linkId}`)
}