import { useState, useEffect, useRef } from 'react'
import { getMyNotifications, markNotificationRead } from '../api/notifications'
import { useWebSocket } from '../hooks/useWebSocket'

function NotificationBell() {
  const [notifications, setNotifications] = useState([])
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef(null)

  // Fetch notifications on mount
  useEffect(() => {
    loadNotifications()
  }, [])

  // Listen for real-time WebSocket notifications
  useWebSocket((message) => {
    if (message.type === 'emergency' || message.type === 'meal_logged') {
      // Add new notification to the top of the list
      setNotifications((prev) => [
        {
          id: message.id,
          type: message.type,
          message: message.message,
          patient_id: message.patient_id,
          created_at: message.created_at,
          read: false,
        },
        ...prev,
      ])
    }
  })

  async function loadNotifications() {
    try {
      const data = await getMyNotifications()
      setNotifications(data)
    } catch (err) {
      console.error('Failed to load notifications:', err)
    }
  }

  async function handleMarkRead(notificationId) {
    try {
      await markNotificationRead(notificationId)
      setNotifications((prev) =>
        prev.map((n) => (n.id === notificationId ? { ...n, read: true } : n))
      )
    } catch (err) {
      console.error('Failed to mark notification as read:', err)
    }
  }

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const unreadCount = notifications.filter((n) => !n.read).length

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Bell Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/20 rounded-xl text-sm font-medium transition-all ring-1 ring-inset ring-white/10"
      >
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        <span>Alerts</span>
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-xs font-bold text-white animate-pulse">
            {unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden z-50 animate-fade-in-up">
          <div className="px-4 py-3 bg-slate-50 border-b border-slate-200">
            <h3 className="text-sm font-semibold text-gray-900">Notifications</h3>
            <p className="text-xs text-gray-500 mt-0.5">
              {unreadCount > 0 ? `${unreadCount} unread` : 'All caught up'}
            </p>
          </div>

          <div className="max-h-96 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="px-4 py-8 text-center">
                <svg className="mx-auto h-12 w-12 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
                <p className="mt-2 text-sm text-gray-500">No notifications yet</p>
              </div>
            ) : (
              <ul className="divide-y divide-slate-100">
                {notifications.map((notif) => (
                  <li
                    key={notif.id}
                    className={`px-4 py-3 hover:bg-slate-50 transition-colors ${
                      !notif.read ? 'bg-amber-50/50' : ''
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className={`flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center ${
                        notif.type === 'emergency' ? 'bg-red-100 text-red-600' : 'bg-blue-100 text-blue-600'
                      }`}>
                        {notif.type === 'emergency' ? (
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
                        <p className={`text-sm ${!notif.read ? 'font-semibold text-gray-900' : 'text-gray-700'}`}>
                          {notif.type === 'emergency' ? ' EMERGENCY ALERT' : 'Meal Logged'}
                        </p>
                        <p className="text-xs text-gray-600 mt-0.5 line-clamp-2">{notif.message}</p>
                        <p className="text-xs text-gray-400 mt-1">
                          {new Date(notif.created_at).toLocaleString()}
                        </p>
                      </div>
                      {!notif.read && (
                        <button
                          onClick={() => handleMarkRead(notif.id)}
                          className="text-xs text-blue-600 hover:text-blue-700 font-medium"
                        >
                          Mark read
                        </button>
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