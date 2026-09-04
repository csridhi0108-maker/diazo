import { useNavigate } from 'react-router-dom'

function Landing() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="border-b border-gray-100 bg-white/80 backdrop-blur-md sticky top-0 z-50 animate-fade-in-up" style={{ animationDelay: '100ms' }}>
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-24 items-center justify-between">
            {/* Improved Logo - Bigger & Bolder */}
            <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate('/')}>
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 shadow-lg shadow-emerald-500/20">
                <svg className="h-7 w-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                </svg>
              </div>
              <span className="text-4xl font-extrabold tracking-tighter text-gray-900">DIAZO</span>
            </div>
            
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/login')}
                className="px-6 py-2.5 text-sm font-semibold text-gray-600 hover:text-emerald-600 transition-colors"
              >
                Sign in
              </button>
              <button
                onClick={() => navigate('/login?register=true')}
                className="px-6 py-2.5 text-sm font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl transition-all shadow-lg shadow-emerald-500/30 hover:shadow-emerald-500/40 hover:-translate-y-0.5"
              >
                Get started
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="relative bg-gradient-to-b from-emerald-50/50 to-white overflow-hidden">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGNpcmNsZSBjeD0iMSIgY3k9IjEiIHI9IjEiIGZpbGw9IiNlNWU3ZWIiLz48L3N2Zz4=')] opacity-40" />
        
        <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid gap-12 py-20 lg:grid-cols-2 lg:gap-16 lg:py-28 items-center">
            {/* Left Content */}
            <div className="flex flex-col justify-center">
              <h1 className="text-5xl font-bold tracking-tight text-gray-900 sm:text-6xl lg:text-7xl leading-[1.1] animate-fade-in-up" style={{ animationDelay: '150ms' }}>
                Smarter diabetes management,{' '}
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-600 to-teal-600">simpler life</span>
              </h1>
              <p className="mt-6 text-xl text-gray-600 leading-relaxed max-w-lg animate-fade-in-up" style={{ animationDelay: '250ms' }}>
                DIAZO combines intelligent insights with compassionate care. Track your glucose, 
                understand patterns, and stay connected with your healthcare team — all in one calm, 
                professional platform.
              </p>
              
              <div className="mt-10 flex flex-col gap-4 sm:flex-row sm:items-center animate-fade-in-up" style={{ animationDelay: '350ms' }}>
                <button
                  onClick={() => navigate('/login?register=true')}
                  className="inline-flex items-center justify-center px-8 py-4 text-base font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl transition-all shadow-xl shadow-emerald-500/30 hover:shadow-emerald-500/40 hover:-translate-y-0.5"
                >
                  Start your journey
                  <svg className="ml-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                  </svg>
                </button>
                
                {/* Enhanced Caregiver Button */}
                <button
                  onClick={() => navigate('/login')}
                  className="group relative inline-flex items-center justify-center gap-3 px-8 py-4 text-base font-semibold text-emerald-800 bg-gradient-to-br from-emerald-50 to-teal-50 hover:from-emerald-100 hover:to-teal-100 border border-emerald-200/60 rounded-xl transition-all duration-300 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-emerald-500/10"
                >
                  <div className="flex h-9 w-9 items-center justify-center rounded-full bg-white text-emerald-600 shadow-sm ring-1 ring-emerald-100 group-hover:scale-110 group-hover:text-emerald-700 transition-all duration-300">
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                    </svg>
                  </div>
                  <span>I'm a caregiver</span>
                  <svg className="h-4 w-4 text-emerald-400 opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition-all duration-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </button>
              </div>

              {/* Trust badges */}
              <div className="mt-12 flex flex-wrap items-center gap-6 text-sm font-medium text-gray-500 animate-fade-in-up" style={{ animationDelay: '450ms' }}>
                <div className="flex items-center gap-2">
                  <svg className="h-5 w-5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>AI-Powered Insights</span>
                </div>
                <div className="flex items-center gap-2">
                  <svg className="h-5 w-5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                  <span>Secure & private</span>
                </div>
                <div className="flex items-center gap-2">
                  <svg className="h-5 w-5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                  <span>Personalized Health Tracking</span>
                </div>
              </div>
            </div>

            {/* Right Content - Hero Image (Dimensions 100% Unchanged) */}
            <div className="relative w-full h-full min-h-[500px] lg:min-h-[500px] min-w-[759px] animate-fade-in-up" style={{ animationDelay: '300ms' }}>
              <div className="relative h-full w-full overflow-hidden rounded-[2.5rem] shadow-2xl shadow-emerald-900/10 border-4 border-white">
                <img
                  src="/images/elder.webp"
                  alt="Happy elderly couple managing their health"
                  className="absolute inset-0 h-full w-full object-cover"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="bg-white py-24 border-t border-gray-100">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16 animate-fade-in-up" style={{ animationDelay: '100ms' }}>
            <h2 className="text-3xl font-bold text-gray-900 sm:text-4xl tracking-tight">
              Everything you need for better health
            </h2>
            <p className="mt-4 text-xl text-gray-600">
              Professional tools designed with patients, caregivers, and doctors in mind
            </p>
          </div>

          <div className="grid gap-8 md:grid-cols-3">
            <FeatureCard
              delay="200ms"
              icon={
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              }
              title="Smart Tracking"
              description="Log meals, glucose levels, and activity with intelligent insights that help you understand patterns."
            />
            <FeatureCard
              delay="300ms"
              icon={
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
              }
              title="Family Connection"
              description="Keep loved ones informed and involved in your care journey with secure, consent-based sharing."
            />
            <FeatureCard
              delay="400ms"
              icon={
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              }
              title="Emergency SOS"
              description="One-button emergency alerts to notify your caregivers instantly when you need help."
            />
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-gray-50 border-t border-gray-200">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-12">
          <div className="flex flex-col items-center justify-center gap-4 animate-fade-in-up" style={{ animationDelay: '100ms' }}>
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-500 to-teal-600">
                <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                </svg>
              </div>
              <span className="text-xl font-bold text-gray-900">DIAZO</span>
            </div>
            <p className="text-sm text-gray-500">
              © 2026 DIAZO. Professional diabetes management for everyone.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}

function FeatureCard({ icon, title, description, delay }) {
  return (
    <div className="group rounded-2xl border border-gray-100 bg-white p-8 transition-all hover:shadow-xl hover:border-emerald-100 hover:-translate-y-1 animate-fade-in-up" style={{ animationDelay: delay }}>
      <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-50 text-emerald-600 group-hover:bg-emerald-600 group-hover:text-white transition-colors">
        {icon}
      </div>
      <h3 className="text-xl font-semibold text-gray-900 mb-3 tracking-tight">{title}</h3>
      <p className="text-gray-600 leading-relaxed">{description}</p>
    </div>
  )
}

export default Landing