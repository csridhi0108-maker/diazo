import client from './client.js'

export async function getFoodItems() {
  const { data } = await client.get('/api/v1/nutrition/foods')
  return data
}

export async function calculateNutrition({ food_id, weight_g }) {
  const { data } = await client.post('/api/v1/nutrition/calculate', { food_id, weight_g })
  return data
}
