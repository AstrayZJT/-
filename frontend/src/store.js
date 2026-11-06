import { reactive } from 'vue'

const saved = localStorage.getItem('socialsim_auth')
const initial = saved ? JSON.parse(saved) : { token: '', user: null }

export const store = reactive({
  token: initial.token || '',
  user: initial.user || null,
  toast: null
})

export function setAuth(token, user) {
  store.token = token
  store.user = user
  localStorage.setItem('socialsim_auth', JSON.stringify({ token, user }))
}

export function clearAuth() {
  store.token = ''
  store.user = null
  localStorage.removeItem('socialsim_auth')
}

export function notify(message, type = 'info') {
  store.toast = { message, type, id: Date.now() }
  const id = store.toast.id
  setTimeout(() => {
    if (store.toast && store.toast.id === id) store.toast = null
  }, 2600)
}
