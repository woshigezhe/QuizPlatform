import request from './request'

export function login(username, password, remember = false) {
  return request.post('/auth/login', { username, password, remember })
}

export function register(username, email, password) {
  return request.post('/auth/register', { username, email, password })
}

export function logout() {
  return request.post('/auth/logout')
}

export function getMe() {
  return request.get('/auth/me')
}