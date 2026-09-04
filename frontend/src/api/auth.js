/**
 * Thin wrappers around the auth endpoints. Pages call these instead
 * of using `client` directly, so the request shape (e.g. login needs
 * form-data, not JSON, per the backend's OAuth2PasswordRequestForm)
 * only needs to be gotten right in one place.
 */

import client from './client'

export async function registerUser({ email, password, role, preferred_language = 'en' }) {
  const { data } = await client.post('/api/v1/auth/register', {
    email,
    password,
    role,
    preferred_language,
  })
  return data
}

export async function loginUser({ email, password }) {
  // Backend's /login expects OAuth2 form-data (username + password),
  // not JSON — see backend/app/api/auth.py's OAuth2PasswordRequestForm.
  const form = new URLSearchParams()
  form.append('username', email)
  form.append('password', password)

  const { data } = await client.post('/api/v1/auth/login', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })

  localStorage.setItem('access_token', data.access_token)
  localStorage.setItem('refresh_token', data.refresh_token)

  return data
}

export function logoutUser() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}

export function isLoggedIn() {
  return Boolean(localStorage.getItem('access_token'))
}

/**
 * Reads the role claim that the API places in the JWT. This is used only for
 * client-side navigation; the backend remains responsible for authorization.
 */
export function getSessionRole() {
  const token = localStorage.getItem('access_token')
  if (!token) return null

  try {
    const payload = token.split('.')[1]
    const normalized = payload.replace(/-/g, '+').replace(/_/g, '/')
    const decoded = JSON.parse(window.atob(normalized))
    return decoded.role ?? null
  } catch {
    return null
  }
}
