import { store, clearAuth } from './store'

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.status = status
  }
}

async function request(path, { method = 'GET', body, raw = false } = {}) {
  const headers = {}
  if (store.token) headers.Authorization = `Bearer ${store.token}`
  let payload = body
  if (body && !(body instanceof FormData) && !raw) {
    headers['Content-Type'] = 'application/json'
    payload = JSON.stringify(body)
  }
  const res = await fetch(`/api${path}`, { method, headers, body: payload })
  const text = await res.text()
  let data = null
  try {
    data = text ? JSON.parse(text) : null
  } catch {
    data = text
  }
  if (!res.ok) {
    if (res.status === 401) {
      clearAuth()
    }
    const detail = data && data.detail ? data.detail : `请求失败（${res.status}）`
    throw new ApiError(typeof detail === 'string' ? detail : JSON.stringify(detail), res.status)
  }
  return data
}

export const api = {
  get: (path) => request(path),
  post: (path, body) => request(path, { method: 'POST', body }),
  put: (path, body) => request(path, { method: 'PUT', body }),
  patch: (path, body) => request(path, { method: 'PATCH', body }),
  del: (path) => request(path, { method: 'DELETE' }),
  upload: (file) => {
    const form = new FormData()
    form.append('file', file)
    return request('/upload', { method: 'POST', body: form })
  },
  uploadImage: (file, eps) => {
    const form = new FormData()
    form.append('file', file)
    form.append('eps', String(eps))
    return request('/admin/lab/image', { method: 'POST', body: form })
  }
}

export function timeAgo(iso) {
  const t = new Date(iso).getTime()
  const diff = Math.max(0, Date.now() - t)
  const min = Math.floor(diff / 60000)
  if (min < 1) return '刚刚'
  if (min < 60) return `${min} 分钟前`
  const h = Math.floor(min / 60)
  if (h < 24) return `${h} 小时前`
  return `${Math.floor(h / 24)} 天前`
}
