import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { loginUser, registerUser, getSessionRole } from '../api/auth'
import LanguageSwitcher from '../components/LanguageSwitcher'

function Login() {
  const { t } = useTranslation()
  const [searchParams] = useSearchParams()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [dateOfBirth, setDateOfBirth] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [isRegistering, setIsRegistering] = useState(false)
  const [isCaregiver, setIsCaregiver] = useState(false)

  const navigate = useNavigate()

  useEffect(() => {
    if (searchParams.get('register') === 'true') {
      setIsRegistering(true)
    }

    if (searchParams.get('caregiver') === 'true') {
      setIsCaregiver(true)
    }
  }, [searchParams])

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      if (isRegistering) {
        await registerUser({
          email,
          password,
          role: isCaregiver ? 'caregiver' : 'patient',
          date_of_birth: dateOfBirth || null
        })

        await loginUser({ email, password })

        const userRole = getSessionRole()

        if (userRole === 'caregiver' || userRole === 'doctor') {
          navigate('/caregiver-onboarding')
        } else {
          navigate('/onboarding')
        }
      } else {
        await loginUser({ email, password })

        const userRole = getSessionRole()

        if (userRole === 'admin') {
          navigate('/admin-dashboard')
        } else if (userRole === 'caregiver' || userRole === 'doctor') {
          navigate('/caregiver-dashboard')
        } else {
          navigate('/dashboard')
        }
      }
    } catch (err) {
      if (err.response?.status === 404) {
        setError(t('account_not_found'))
      } else if (err.response?.status === 401) {
        setError(t('incorrect_password'))
      } else {
        const detail = err.response?.data?.detail
        const detailStr = Array.isArray(detail)
          ? detail[0]?.msg
          : detail

        setError(
          detailStr || t('login_failed')
        )
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex bg-white">

      {/* Left Panel */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-emerald-900 via-teal-800 to-emerald-900 relative overflow-hidden">

        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGNpcmNsZSBjeD0iMSIgY3k9IjEiIHI9IjEiIGZpbGw9InJnYmEoMjU1LDI1NSwyNTUsMC4wNSkiLz48L3N2Zz4=')] opacity-30" />

        <div className="absolute top-0 left-0 w-96 h-96 bg-emerald-500/20 rounded-full blur-3xl -translate-x-1/2 -translate-y-1/2" />

        <div className="absolute bottom-0 right-0 w-96 h-96 bg-teal-500/20 rounded-full blur-3xl translate-x-1/2 translate-y-1/2" />

        <div className="relative z-10 flex flex-col justify-between w-full p-12 text-white animate-fade-in-up">

          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white/10 backdrop-blur-sm border border-white/20">
              <svg
                className="h-7 w-7 text-white"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2.5}
                  d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
                />
              </svg>
            </div>

            <span className="text-3xl font-extrabold tracking-tighter">
              DIAZO
            </span>
          </div>

          <div className="space-y-6 max-w-lg">
            <h2 className="text-4xl font-bold leading-tight tracking-tight">
              {t('compassionate_care')}
              <br />
              <span className="text-emerald-300">
                {t('powered_by_intelligence')}
              </span>
            </h2>

            <p className="text-lg text-emerald-100/80 leading-relaxed">
              {t('login_description')}
            </p>

            <div className="flex items-center gap-6 pt-4">

              <div className="flex items-center gap-2 text-sm text-emerald-200/80">
                <svg
                  className="h-5 w-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                  />
                </svg>
                {t('role_based_access')}
              </div>

              <div className="flex items-center gap-2 text-sm text-emerald-200/80">
                <svg
                  className="h-5 w-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                  />
                </svg>
                {t('secure_authentication')}
              </div>

            </div>
          </div>

          <div className="text-sm text-emerald-200/60">
            {t('copyright')}
          </div>
        </div>
      </div>

      {/* Right Panel */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 sm:p-12 bg-slate-50/50 relative">

        {/* Language Switcher */}
        <div className="absolute top-6 right-6">
          <LanguageSwitcher />
        </div>

        <div className="w-full max-w-md space-y-8">

          {/* Heading */}
          <div
            className="text-center animate-fade-in-up"
            style={{ animationDelay: '100ms' }}
          >
            <div className="lg:hidden flex justify-center mb-6">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 shadow-lg">
                <svg
                  className="h-7 w-7 text-white"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2.5}
                    d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
                  />
                </svg>
              </div>
            </div>

            <h1 className="text-3xl font-bold tracking-tight text-gray-900">
              {isRegistering
                ? isCaregiver
                  ? t('caregiver_registration')
                  : t('create_account')
                : t('welcome_back')}
            </h1>

            <p className="mt-2 text-sm text-gray-500">
              {isRegistering
                ? isCaregiver
                  ? t('caregiver_description')
                  : t('start_journey')
                : t('sign_in_dashboard')}
            </p>
          </div>

          {/* Caregiver Toggle */}
          {isRegistering && (
            <div
              className="flex justify-center animate-fade-in-up"
              style={{ animationDelay: '150ms' }}
            >
              <div className="inline-flex bg-slate-100 rounded-xl p-1">

                <button
                  type="button"
                  onClick={() => setIsCaregiver(false)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    !isCaregiver
                      ? 'bg-white text-emerald-600 shadow-sm'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  {t('im_patient')}
                </button>

                <button
                  type="button"
                  onClick={() => setIsCaregiver(true)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    isCaregiver
                      ? 'bg-white text-emerald-600 shadow-sm'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  {t('im_caregiver')}
                </button>

              </div>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">

            {/* Email */}
            <div
              className="animate-fade-in-up"
              style={{ animationDelay: '200ms' }}
            >
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                {t('email')}
              </label>

              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                  <svg
                    className="h-5 w-5 text-gray-400 group-focus-within:text-emerald-500 transition-colors"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207"
                    />
                  </svg>
                </div>

                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full pl-11 pr-4 py-3 bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-4 focus:ring-emerald-500/10 focus:border-emerald-500 transition-all text-gray-900 placeholder-gray-400"
                  placeholder={t('email_placeholder')}
                />
              </div>
            </div>

            {/* Date of Birth */}
            {isRegistering && !isCaregiver && (
              <div
                className="animate-fade-in-up"
                style={{ animationDelay: '250ms' }}
              >
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  {t('date_of_birth')}
                </label>

                <div className="relative group">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                    <svg
                      className="h-5 w-5 text-gray-400 group-focus-within:text-emerald-500 transition-colors"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                      />
                    </svg>
                  </div>

                  <input
                    type="date"
                    value={dateOfBirth}
                    onChange={(e) => setDateOfBirth(e.target.value)}
                    required
                    className="w-full pl-11 pr-4 py-3 bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-4 focus:ring-emerald-500/10 focus:border-emerald-500 transition-all text-gray-900"
                  />
                </div>
              </div>
            )}

            {/* Password */}
            <div
              className="animate-fade-in-up"
              style={{ animationDelay: '300ms' }}
            >
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                {t('password')}
              </label>

              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                  <svg
                    className="h-5 w-5 text-gray-400 group-focus-within:text-emerald-500 transition-colors"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                    />
                  </svg>
                </div>

                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="w-full pl-11 pr-4 py-3 bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-4 focus:ring-emerald-500/10 focus:border-emerald-500 transition-all text-gray-900 placeholder-gray-400"
                  placeholder="••••••••"
                />
              </div>
            </div>

            {/* Error */}
            {error && (
              <div className="p-4 bg-rose-50/80 border border-rose-100 rounded-xl text-rose-700 text-sm flex items-start gap-3 animate-fade-in-up shadow-sm backdrop-blur-sm">

                <div className="flex-shrink-0 mt-0.5">
                  <svg
                    className="w-5 h-5 text-rose-500"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                </div>

                <div className="flex-1">
                  <p className="font-semibold text-rose-800 mb-1">
                    {t('login_failed')}
                  </p>

                  <p className="text-rose-600 leading-relaxed">
                    {error}
                  </p>

                  {error.toLowerCase().includes('not found') && (
                    <button
                      type="button"
                      onClick={() => {
                        setIsRegistering(true)
                        setError('')
                      }}
                      className="mt-2 inline-flex items-center gap-1 text-xs font-semibold text-rose-700 hover:text-rose-800 transition-colors group"
                    >
                      {t('dont_have_account')}

                      <svg
                        className="w-3 h-3 group-hover:translate-x-0.5 transition-transform"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 5l7 7-7 7"
                        />
                      </svg>
                    </button>
                  )}
                </div>
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white font-semibold py-3.5 rounded-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-emerald-500/20 hover:shadow-emerald-500/30 transform hover:-translate-y-0.5 animate-fade-in-up"
              style={{ animationDelay: '350ms' }}
            >
              {loading
                ? (isRegistering
                    ? t('creating_account')
                    : t('signing_in'))
                : (isRegistering
                    ? t('sign_up')
                    : t('sign_in'))}
            </button>

          </form>

          {/* Toggle Login / Registration */}
          <div
            className="text-center animate-fade-in-up"
            style={{ animationDelay: '400ms' }}
          >
            <button
              type="button"
              onClick={() => {
                setIsRegistering((value) => !value)
                setError('')
                setIsCaregiver(false)
              }}
              className="text-sm font-medium text-emerald-600 hover:text-emerald-700 transition-colors"
            >
              {isRegistering
                ? t('already_have_account')
                : t('new_to_diazo')}
            </button>
          </div>

        </div>
      </div>
    </div>
  )
}

export default Login