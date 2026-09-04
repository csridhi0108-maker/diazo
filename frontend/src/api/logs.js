import client from './client.js'

export async function createMealLog(payload) {
  const { data } = await client.post('/api/v1/logs/meals', payload)
  return data
}

export async function createGlucoseLog(payload) {
  const { data } = await client.post('/api/v1/logs/glucose', payload)
  return data
}

export async function upsertActivityLog(payload) {
  const { data } = await client.put('/api/v1/logs/activity', payload)
  return data
}
