import { useEffect, useRef } from 'react'
import { isLoggedIn } from '../api/auth'

export function useWebSocket(onMessage) {
  const wsRef = useRef(null)

  useEffect(() => {
    if (!isLoggedIn()) return

    const token = localStorage.getItem('access_token')
    const wsUrl = `ws://127.0.0.1:8000/ws/notifications?token=${token}`
    
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        onMessage(data)
      } catch (err) {
        console.error('Failed to parse WebSocket message', err)
      }
    }

    ws.onerror = (err) => {
      // Silently fail on error during unmount/logout
      if (ws.readyState !== WebSocket.CLOSED) {
        console.warn('WebSocket error', err)
      }
    }

    // Cleanup function: close the socket when component unmounts
    return () => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close()
      }
    }
  }, [onMessage])
}