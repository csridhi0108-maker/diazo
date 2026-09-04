import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import client from '../api/client.js'

const initialForm = {
  full_name: '', // ADDED
  diabetes_type: 'type2',
  diagnosis_duration_months: '',
  sex: 'female',
  age: '',
  height_cm: '',
  weight_kg: '',
  activity_level: 'moderate',
  medications: '',
  dietary_prefs: '',
  family_history: false,
}

function Onboarding() {
  const [form, setForm] = useState(initialForm)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const navigate = useNavigate()

  function updateField(event) {
    const { name, type, checked, value } = event.target
    setForm((current) => ({ ...current, [name]: type === 'checkbox' ? checked : value }))
    // Clear error when user starts typing
    if (error) setError('')
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setSaving(true)

    try {
      await client.post('/api/v1/patients/me', {
        ...form,
        age: Number(form.age),
        height_cm: Number(form.height_cm),
        weight_kg: Number(form.weight_kg),
        diagnosis_duration_months: form.diagnosis_duration_months
          ? Number(form.diagnosis_duration_months)
          : null,
        medications: form.medications.trim() || null,
        dietary_prefs: form.dietary_prefs.trim() || null,
      })
      navigate('/dashboard', { replace: true })
    } catch (requestError) {
      setError(requestError.response?.data?.detail || 'We could not save your profile. Please check the details and try again.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50/50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-3xl">
        
        {/* Header */}
        <div className="text-center mb-10 animate-fade-in-up">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 shadow-lg shadow-emerald-500/20 mb-6">
            <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
            Let’s personalize your plan
          </h1>
          <p className="mt-3 text-lg text-gray-500 max-w-2xl mx-auto">
            These details help DIAZO’s AI create safe, accurate, and personalized daily targets for your health journey.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-8">
          
          {/* Section 1: Diagnosis & Basics */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 sm:p-8 animate-fade-in-up" style={{ animationDelay: '100ms' }}>
            <h2 className="text-lg font-semibold text-gray-900 mb-6 flex items-center gap-2">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-100 text-emerald-600 text-sm font-bold">1</span>
              Diagnosis & Basics
            </h2>
            <div className="grid gap-6 sm:grid-cols-2">
              
              {/* NEW: Full Name Field */}
              <InputField 
                label="Full Name" 
                name="full_name" 
                value={form.full_name} 
                onChange={updateField} 
                placeholder="e.g., John Doe"
                icon={<svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>}
                className="sm:col-span-2"
                required
              />

              <SelectField 
                label="Diabetes Type" 
                name="diabetes_type" 
                value={form.diabetes_type} 
                onChange={updateField} 
                icon={<svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" /></svg>}
                options={[
                  ['type1', 'Type 1'], 
                  ['type2', 'Type 2'], 
                  ['prediabetic', 'Prediabetic'], 
                  ['none', 'None / Other']
                ]} 
              />
              <SelectField 
                label="Sex" 
                name="sex" 
                value={form.sex} 
                onChange={updateField} 
                icon={<svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>}
                options={[
                  ['female', 'Female'], 
                  ['male', 'Male'],
                  ['other', 'Other']
                ]} 
              />
              <InputField 
                label="Age" 
                name="age" 
                value={form.age} 
                onChange={updateField} 
                type="number" 
                min="1" max="129" 
                placeholder="e.g., 45"
                required 
              />
              <InputField 
                label="Diagnosis Duration (Months)" 
                name="diagnosis_duration_months" 
                value={form.diagnosis_duration_months} 
                onChange={updateField} 
                type="number" 
                min="0" 
                placeholder="e.g., 24 (leave blank if unsure)"
              />
            </div>
          </div>

          {/* Section 2: Physical Metrics */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 sm:p-8 animate-fade-in-up" style={{ animationDelay: '200ms' }}>
            <h2 className="text-lg font-semibold text-gray-900 mb-6 flex items-center gap-2">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-100 text-emerald-600 text-sm font-bold">2</span>
              Physical Metrics
            </h2>
            <div className="grid gap-6 sm:grid-cols-2">
              <InputField 
                label="Height (cm)" 
                name="height_cm" 
                value={form.height_cm} 
                onChange={updateField} 
                type="number" 
                min="1" step="0.1" 
                placeholder="e.g., 170"
                icon={<svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>}
                required 
              />
              <InputField 
                label="Weight (kg)" 
                name="weight_kg" 
                value={form.weight_kg} 
                onChange={updateField} 
                type="number" 
                min="1" step="0.1" 
                placeholder="e.g., 75"
                icon={<svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" /></svg>}
                required 
              />
            </div>
          </div>

          {/* Section 3: Lifestyle & Preferences */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 sm:p-8 animate-fade-in-up" style={{ animationDelay: '300ms' }}>
            <h2 className="text-lg font-semibold text-gray-900 mb-6 flex items-center gap-2">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-100 text-emerald-600 text-sm font-bold">3</span>
              Lifestyle & Preferences
            </h2>
            <div className="space-y-6">
              <SelectField 
                label="Activity Level" 
                name="activity_level" 
                value={form.activity_level} 
                onChange={updateField} 
                icon={<svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>}
                options={[
                  ['sedentary', 'Mostly sedentary (little to no exercise)'], 
                  ['moderate', 'Moderately active (light exercise 1-3 days/week)'], 
                  ['active', 'Very active (intense exercise 4+ days/week)']
                ]} 
              />

              <div className="grid gap-6 sm:grid-cols-2">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Current Medications <span className="font-normal text-gray-400">(Optional)</span>
                  </label>
                  <div className="relative group">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                      <svg className="h-5 w-5 text-gray-400 group-focus-within:text-emerald-500 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                      </svg>
                    </div>
                    <input 
                      name="medications" 
                      value={form.medications} 
                      onChange={updateField} 
                      placeholder="e.g., Metformin 500mg"
                      className="w-full pl-11 pr-4 py-3 bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-4 focus:ring-emerald-500/10 focus:border-emerald-500 transition-all text-gray-900 placeholder-gray-400" 
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Dietary Preferences <span className="font-normal text-gray-400">(Optional)</span>
                  </label>
                  <div className="relative group">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                      <svg className="h-5 w-5 text-gray-400 group-focus-within:text-emerald-500 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
                      </svg>
                    </div>
                    <input 
                      name="dietary_prefs" 
                      value={form.dietary_prefs} 
                      onChange={updateField} 
                      placeholder="e.g., Vegetarian, Low-carb"
                      className="w-full pl-11 pr-4 py-3 bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-4 focus:ring-emerald-500/10 focus:border-emerald-500 transition-all text-gray-900 placeholder-gray-400" 
                    />
                  </div>
                </div>
              </div>

              <label className="flex items-start gap-3 p-4 rounded-xl border border-gray-200 bg-slate-50/50 cursor-pointer hover:bg-slate-50 transition-colors group">
                <input 
                  type="checkbox" 
                  name="family_history" 
                  checked={form.family_history} 
                  onChange={updateField} 
                  className="mt-1 h-5 w-5 rounded border-gray-300 text-emerald-600 focus:ring-emerald-500 transition-colors" 
                />
                <div>
                  <span className="block text-sm font-semibold text-gray-900 group-hover:text-emerald-700 transition-colors">Diabetes runs in my family</span>
                  <span className="block text-xs text-gray-500 mt-1">Checking this helps the AI understand your baseline risk factors.</span>
                </div>
              </label>
            </div>
          </div>

          {/* Error & Submit */}
          <div className="animate-fade-in-up" style={{ animationDelay: '400ms' }}>
            {error && (
              <div className="mb-4 p-4 bg-red-50 border border-red-100 rounded-xl text-red-600 text-sm flex items-start gap-3">
                <svg className="w-5 h-5 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {error}
              </div>
            )}
            
            <button 
              type="submit" 
              disabled={saving} 
              className="w-full bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white font-semibold py-4 rounded-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-emerald-500/20 hover:shadow-emerald-500/30 transform hover:-translate-y-0.5 flex items-center justify-center gap-2"
            >
              {saving ? (
                <>
                  <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Creating your personalized plan…
                </>
              ) : (
                <>
                  Create my plan
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                  </svg>
                </>
              )}
            </button>
            <p className="text-center text-xs text-gray-400 mt-4">
              Your data is encrypted and used solely to generate your personalized health insights.
            </p>
          </div>

        </form>
      </div>
    </div>
  )
}

// Polished Input Component (Updated to accept className)
function InputField({ label, icon, className = '', ...props }) {
  return (
    <div className={className}>
      <label className="block text-sm font-semibold text-gray-700 mb-2">{label}</label>
      <div className="relative group">
        {icon && (
          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
            <span className="text-gray-400 group-focus-within:text-emerald-500 transition-colors">
              {icon}
            </span>
          </div>
        )}
        <input 
          {...props} 
          className={`w-full ${icon ? 'pl-11' : 'pl-4'} pr-4 py-3 bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-4 focus:ring-emerald-500/10 focus:border-emerald-500 transition-all text-gray-900 placeholder-gray-400`} 
        />
      </div>
    </div>
  )
}

// Polished Select Component
function SelectField({ label, options, icon, ...props }) {
  return (
    <div>
      <label className="block text-sm font-semibold text-gray-700 mb-2">{label}</label>
      <div className="relative group">
        {icon && (
          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
            <span className="text-gray-400 group-focus-within:text-emerald-500 transition-colors">
              {icon}
            </span>
          </div>
        )}
        <select 
          {...props} 
          className={`w-full ${icon ? 'pl-11' : 'pl-4'} pr-10 py-3 bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-4 focus:ring-emerald-500/10 focus:border-emerald-500 transition-all text-gray-900 appearance-none cursor-pointer`}
        >
          {options.map(([value, text]) => (
            <option key={value} value={value}>{text}</option>
          ))}
        </select>
        <div className="absolute inset-y-0 right-0 pr-3.5 flex items-center pointer-events-none">
          <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>
    </div>
  )
}

export default Onboarding