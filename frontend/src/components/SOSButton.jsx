import { useState } from 'react'
import { triggerEmergencySOS } from '../api/notifications'

function SOSButton() {
  const [sending, setSending] = useState(false)
  const [sent, setSent] = useState(false)
  const [error, setError] = useState('')

  async function handleClick() {
    if (!confirm('Send an emergency alert to your linked caregivers/doctors?')) return
    setSending(true)
    setError('')
    try {
      await triggerEmergencySOS()
      setSent(true)
      setTimeout(() => setSent(false), 5000)
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not send alert.')
    } finally {
      setSending(false)
    }
  }

  return (
    <div>
      <button
        onClick={handleClick}
        disabled={sending}
        className="bg-red-500 hover:bg-red-600 text-white font-semibold px-5 py-2.5 rounded-lg transition-colors disabled:opacity-50"
      >
        {sending ? 'Sending...' : sent ? 'Alert Sent ✓' : '🚨 Emergency SOS'}
      </button>
      {error && <p className="text-red-500 text-xs mt-1">{error}</p>}
    </div>
  )
}

export default SOSButton