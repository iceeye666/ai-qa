import http from './http'

export const authApi = {
  login: (username, password) => http.post('/auth/login', { username, password }),
  register: (username, password, nickname) =>
    http.post('/auth/register', { username, password, nickname }),
  me: () => http.get('/auth/me')
}

export const chatApi = {
  ask: (payload) => http.post('/chat', payload),
  listConversations: (keyword) =>
    http.get('/conversations', { params: keyword ? { keyword } : {} }),
  createConversation: (title, modelKey) =>
    http.post('/conversations', { title, model_key: modelKey }),
  getConversation: (id) => http.get(`/conversations/${id}`),
  renameConversation: (id, title) => http.patch(`/conversations/${id}`, { title }),
  deleteConversation: (id) => http.delete(`/conversations/${id}`)
}

export const modelApi = {
  list: () => http.get('/models'),
  providers: () => http.get('/models/providers'),
  create: (data) => http.post('/models', data),
  update: (id, data) => http.put(`/models/${id}`, data),
  remove: (id) => http.delete(`/models/${id}`)
}

export const userApi = {
  list: () => http.get('/users'),
  create: (data) => http.post('/users', data),
  update: (id, data) => http.put(`/users/${id}`, data),
  remove: (id) => http.delete(`/users/${id}`)
}
