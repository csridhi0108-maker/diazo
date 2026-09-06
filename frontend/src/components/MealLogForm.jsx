import { useEffect, useState } from 'react'
import { createMealLog } from '../api/logs.js'
import { getFoodItems, calculateNutrition } from '../api/nutrition.js'

function MealLogForm({ onLogged, scaleReading }) {
  const [mealType, setMealType] = useState('breakfast')

  // Scale flow: pick a food from the reference list, nutrition is
  // calculated server-side from the selected food + scale weight.
  const [foods, setFoods] = useState([])
  const [foodId, setFoodId] = useState('')
  const [preview, setPreview] = useState(null)
  const [previewLoading, setPreviewLoading] = useState(false)
  const [previewError, setPreviewError] = useState('')

  // Manual fallback — unchanged from before, used when no food is
  // selected from the dropdown (e.g. scale not connected yet, or the
  // food isn't in the reference list).
  const [foodDescription, setFoodDescription] = useState('')
  const [carbs, setCarbs] = useState('')
  const [calories, setCalories] = useState('')

  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    getFoodItems()
      .then(setFoods)
      .catch(() => {
        // Non-fatal — the manual fields below still work without the food list.
        setFoods([])
      })
  }, [])

  // Whenever the selected food or the live scale weight changes,
  // fetch a fresh nutrition preview (carbs/protein + within/above
  // target) so the patient sees the result before they log it.
  useEffect(() => {
    if (!foodId || !scaleReading?.weight_g) {
      setPreview(null)
      return
    }

    let cancelled = false
    setPreviewLoading(true)
    setPreviewError('')

    calculateNutrition({ food_id: foodId, weight_g: scaleReading.weight_g })
      .then((result) => {
        if (!cancelled) setPreview(result)
      })
      .catch((requestError) => {
        if (!cancelled) {
          setPreview(null)
          setPreviewError(requestError.response?.data?.detail || 'Could not calculate nutrition for this portion.')
        }
      })
      .finally(() => {
        if (!cancelled) setPreviewLoading(false)
      })

    return () => { cancelled = true }
  }, [foodId, scaleReading?.weight_g])

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setSaving(true)

    try {
      const usingScaleFlow = Boolean(foodId && scaleReading?.weight_g)

      const payload = usingScaleFlow
        ? {
            meal_type: mealType,
            food_id: foodId,
            weight_g: scaleReading.weight_g,
          }
        : {
            meal_type: mealType,
            food_items: foodDescription.trim() || scaleReading
              ? [{
                  description: foodDescription.trim() || 'Measured meal portion',
                  measured_weight_g: scaleReading?.weight_g ?? null,
                  scale_device_id: scaleReading?.device_id ?? null,
                }]
              : null,
            estimated_carbs: carbs === '' ? null : Number(carbs),
            estimated_calories: calories === '' ? null : Number(calories),
          }

      const meal = await createMealLog(payload)
      onLogged?.(meal)
      setFoodId('')
      setPreview(null)
      setFoodDescription('')
      setCarbs('')
      setCalories('')
    } catch (requestError) {
      setError(requestError.response?.data?.detail || 'Could not save this meal.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className={`rounded-xl border p-3 ${scaleReading ? 'border-emerald-200 bg-emerald-50' : 'border-dashed border-slate-200 bg-slate-50'}`}>
        {scaleReading ? (
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-emerald-700">Connected scale</p>
              <p className="mt-1 text-sm text-emerald-900">Latest portion measurement is ready to attach.</p>
            </div>
            <p className="text-2xl font-bold tabular-nums text-emerald-700">{scaleReading.weight_g} <span className="text-sm font-medium">g</span></p>
          </div>
        ) : (
          <p className="text-sm text-slate-500">Waiting for a connected meal scale. You can still log a meal manually.</p>
        )}
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <label className="text-sm font-medium text-slate-700">Meal
          <select value={mealType} onChange={(event) => setMealType(event.target.value)} className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 outline-none ring-emerald-500 focus:ring-2">
            {['breakfast', 'lunch', 'dinner', 'snack'].map((type) => <option key={type} value={type}>{type[0].toUpperCase() + type.slice(1)}</option>)}
          </select>
        </label>
        <label className="text-sm font-medium text-slate-700">Food {scaleReading ? '' : <span className="font-normal text-slate-400">(needs a connected scale)</span>}
          <select
            value={foodId}
            onChange={(event) => setFoodId(event.target.value)}
            disabled={!scaleReading || foods.length === 0}
            className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 outline-none ring-emerald-500 focus:ring-2 disabled:bg-slate-100 disabled:text-slate-400"
          >
            <option value="">— Select from list —</option>
            {foods.map((food) => <option key={food.id} value={food.id}>{food.name}</option>)}
          </select>
        </label>
      </div>

      {foodId && scaleReading && (
        <div className="rounded-xl border border-slate-200 bg-white p-3">
          {previewLoading && <p className="text-sm text-slate-500">Calculating…</p>}
          {previewError && <p className="text-sm text-red-600">{previewError}</p>}
          {preview && !previewLoading && (
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="text-sm text-slate-700">
                <p><span className="font-semibold">{preview.carbs_g}g</span> carbs · <span className="font-semibold">{preview.protein_g}g</span> protein
                  {preview.calories != null && <> · {preview.calories} kcal</>}
                </p>
                <p className="text-xs text-slate-400">{preview.food} · {preview.weight_g}g measured</p>
              </div>
              {preview.status === 'WITHIN_TARGET' && (
                <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700">🟢 Within target</span>
              )}
              {preview.status === 'ABOVE_TARGET' && (
                <span className="rounded-full bg-red-100 px-3 py-1 text-xs font-semibold text-red-700">🔴 Above target</span>
              )}
              {preview.status == null && (
                <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-500">No target set yet</span>
              )}
            </div>
          )}
        </div>
      )}

      {!foodId && (
        <>
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="text-sm font-medium text-slate-700">Carbs (g)
              <input type="number" min="0" step="0.1" value={carbs} onChange={(event) => setCarbs(event.target.value)} className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2.5 outline-none ring-emerald-500 focus:ring-2" />
            </label>
            <label className="text-sm font-medium text-slate-700">Calories
              <input type="number" min="0" step="1" value={calories} onChange={(event) => setCalories(event.target.value)} className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2.5 outline-none ring-emerald-500 focus:ring-2" />
            </label>
          </div>
          <label className="block text-sm font-medium text-slate-700">What did you eat? <span className="font-normal text-slate-400">(optional)</span>
            <input value={foodDescription} onChange={(event) => setFoodDescription(event.target.value)} placeholder="e.g. oats with banana" className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2.5 outline-none ring-emerald-500 focus:ring-2" />
          </label>
        </>
      )}

      {error && <p className="text-sm text-red-600">{error}</p>}
      <button disabled={saving} className="rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-700 disabled:opacity-50">
        {saving ? 'Saving…' : 'Log meal'}
      </button>
    </form>
  )
}

export default MealLogForm
