import client from './client'

// Patient: trigger emergency SOS
export async function triggerEmergencySOS() {
  const { data } = await client.post('/api/v1/notifications/emergency')
  return data
}

// Caregiver/Doctor: get my notifications
export async function getMyNotifications() {
  const { data } = await client.get('/api/v1/notifications/mine')
  return data
}

// Caregiver/Doctor: mark notification as read
export async function markNotificationRead(notificationId) {
  const { data } = await client.patch(`/api/v1/notifications/${notificationId}/read`)
  return data
}