const TOKEN_KEY = 'cfo_mentor_token'
const USER_KEY = 'cfo_mentor_user'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function getUser() {
  return localStorage.getItem(USER_KEY)
}

export function setUser(username) {
  localStorage.setItem(USER_KEY, username)
}

export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

export function isAuthenticated() {
  return !!getToken()
}
