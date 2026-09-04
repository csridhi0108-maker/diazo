import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { getMyNotifications, markNotificationRead } from '../api/notifications'
import { useWebSocket } from '../hooks/useWebSocket'

function NotificationBell() {
  const [notifications, setNotifications] = useState([])
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef(null)
  const navigate = useNavigate()

  useEffect(() => {
    loadNotifications()
  }, [])

  useWebSocket((message) => {
    if (message.id && (message.message || message.type)) {
      setNotifications((prev) => [
        { 
          ...message, 
          is_read: false,
          created_at: message.created_at || new Date().toISOString()
        },
        ...prev
      ])
    }
  })

  async function loadNotifications() {
    try {
      const data = await getMyNotifications()
      const mappedData = data.map(n => ({
        ...n,
        is_read: n.read || n.is_read || false,
        message: n.message || 'New notification',
        created_at: n.created_at || new Date().toISOString(),
        type: n.type || 'general'
      }))
      setNotifications(mappedData)
    } catch (err) {
      console.error('Failed to load notifications:', err)
    }
  }

  async function handleMarkRead(id) {
    try {
      await markNotificationRead(id)
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      )
    } catch (err) {
      console.error('Failed to mark notification as read:', err)
    }
  }

  function handleNotificationClick(n) {
    handleMarkRead(n.id)
    setIsOpen(false)
    if (n.patient_id) {
      navigate(`/caregiver/patient/${n.patient_id}`)
    }
  }

  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const unreadCount = notifications.filter((n) => !n.is_read).length

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/20 rounded-xl text-sm font-medium transition-all ring-1 ring-inset ring-white/10"
      >
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        <span className="hidden sm:inline">Alerts</span>
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-xs font-bold text-white animate-pulse">
            {unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div 
          className="absolute right-0 mt-2 w-80 bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden z-[9999]"
          style={{ zIndex: 9999 }}
        >
          <div className="px-4 py-3 bg-slate-50 border-b border-slate-200 flex justify-between items-center">
            <h3 className="text-sm font-semibold text-gray-900">Notifications</h3>
            {unreadCount > 0 && (
              <span className="text-xs text-red-600 font-medium">{unreadCount} unread</span>
            )}
          </div>

          <div className="max-h-96 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="px-4 py-8 text-center">
                <p className="text-sm text-gray-500">No notifications yet</p>
              </div>
            ) : (
              <ul className="divide-y divide-slate-100">
                {notifications.map((n) => (
                  <li
                    key={n.id}
                    onClick={() => handleNotificationClick(n)}
                    className={`px-4 py-3 hover:bg-slate-100 transition-colors cursor-pointer ${
                      !n.is_read ? (n.type === 'emergency' ? 'bg-red-50' : 'bg-blue-50') : ''
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className={`flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center ${
                        n.type === 'emergency' ? 'bg-red-100 text-red-600' : 'bg-blue-100 text-blue-600'
                      }`}>
                        {n.type === 'emergency' ? (
                          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                          </svg>
                        ) : (
                          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                          </svg>
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className={`text-sm font-medium ${
                          n.type === 'emergency' ? 'text-red-600' : 'text-gray-900'
                        }`}>
                          {n.type === 'emergency' ? '🚨 EMERGENCY ALERT' : 'New Alert'}
                        </p>
                        <p className="text-xs text-gray-600 mt-0.5 line-clamp-2">
                          {n.message || 'No message'}
                        </p>
                        <p className="text-xs text-gray-400 mt-1">
                          {new Date(n.created_at).toLocaleString()}
                        </p>
                      </div>
                      {!n.is_read && (
                        <span className="flex-shrink-0 h-2 w-2 bg-blue-500 rounded-full"></span>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default NotificationBell