/**
 * Central axios instance. Every API call in the app goes through
 * this, not raw axios/fetch — so token attachment and refresh-on-401
 * are handled in exactly one place.
 */

import axios from 'axios'

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

const client = axios.create({
  baseURL: API_BASE_URL,
})

// Attach the access token to every outgoing request, if we have one.
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// If a request comes back 401 (expired access token), try refreshing
// once and retrying the original request — so the user doesn't get
// logged out just because 30 minutes passed mid-session.
let isRefreshing = false
let refreshQueue = []

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      const refreshToken = localStorage.getItem('refresh_token')
      if (!refreshToken) {
        // No refresh token at all — genuinely logged out, send to login.
        localStorage.removeItem('access_token')
        window.location.href = '/login'
        return Promise.reject(error)
      }

      if (isRefreshing) {
        // Another request already triggered a refresh in-flight —
        // queue this one instead of firing a duplicate refresh call.
        return new Promise((resolve, reject) => {
          refreshQueue.push({ resolve, reject, originalRequest })
        })
      }

      isRefreshing = true
      try {
        const { data } = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
          refresh_token: refreshToken,
        })
        localStorage.setItem('access_token', data.access_token)
        localStorage.setItem('refresh_token', data.refresh_token)

        refreshQueue.forEach(({ resolve, originalRequest: req }) => {
          req.headers.Authorization = `Bearer ${data.access_token}`
          resolve(client(req))
        })
        refreshQueue = []

        originalRequest.headers.Authorization = `Bearer ${data.access_token}`
        return client(originalRequest)
      } catch (refreshError) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  }
)

export default client
