const memoryCache = new Map()

const now = () => Date.now()

const buildId = (namespace, key) => `${namespace}:${key}`

const safeStorage = () => {
  if (typeof window === 'undefined') return null
  return window.sessionStorage
}

export const makeCacheKey = (payload = {}) =>
  Object.entries(payload)
    .filter(([, value]) => value !== undefined && value !== null && value !== '')
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([key, value]) => `${key}=${Array.isArray(value) ? value.join('|') : String(value)}`)
    .join('&') || 'default'

export const readViewCache = (namespace, key, ttlMs = 5 * 60 * 1000) => {
  const id = buildId(namespace, key)
  const runtime = memoryCache.get(id)
  if (runtime && now() - runtime.timestamp < ttlMs) {
    return runtime.payload
  }

  const storage = safeStorage()
  if (!storage) return null

  try {
    const raw = storage.getItem(id)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    if (now() - Number(parsed?.timestamp || 0) >= ttlMs) {
      storage.removeItem(id)
      return null
    }
    memoryCache.set(id, parsed)
    return parsed.payload
  } catch {
    return null
  }
}

export const writeViewCache = (namespace, key, payload) => {
  const id = buildId(namespace, key)
  const cacheEntry = {
    timestamp: now(),
    payload,
  }
  memoryCache.set(id, cacheEntry)
  const storage = safeStorage()
  if (!storage) return
  try {
    storage.setItem(id, JSON.stringify(cacheEntry))
  } catch {
    // ignore storage quota errors
  }
}

export const clearViewCache = (namespace, key) => {
  const id = buildId(namespace, key)
  memoryCache.delete(id)
  safeStorage()?.removeItem(id)
}
