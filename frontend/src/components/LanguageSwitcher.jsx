import { useTranslation } from 'react-i18next'
import { changeLanguage } from '../i18n'

function LanguageSwitcher({ dark = false }) {
  const { i18n } = useTranslation()
  const currentLang = i18n.language || 'en'

  const languages = [
    { code: 'en', label: 'English' },
    { code: 'hi', label: 'हिन्दी' },
    { code: 'te', label: 'తెలుగు' },
  ]

  return (
    <select
      value={currentLang}
      onChange={(e) => changeLanguage(e.target.value)}
      aria-label="Select language"
      className={`
        appearance-none
        rounded-lg
        px-3 py-2
        text-sm
        font-medium
        cursor-pointer
        transition-all
        focus:outline-none
        focus:ring-2
        focus:ring-emerald-500/50
        ${
          dark
            ? 'bg-white/10 hover:bg-white/20 border border-white/20 text-white'
            : 'bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 shadow-sm'
        }
      `}
    >
      {languages.map((lang) => (
        <option
          key={lang.code}
          value={lang.code}
          className="text-gray-900 bg-white"
        >
          {lang.label}
        </option>
      ))}
    </select>
  )
}

export default LanguageSwitcher