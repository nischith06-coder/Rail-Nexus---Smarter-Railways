const BASE = import.meta.env.VITE_API_URL || '/api-proxy'

export async function api<T>(path:string, options:RequestInit={}) : Promise<T> {
  const res = await fetch(BASE + path, {headers:{'Content-Type':'application/json'}, ...options})
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export const API_BASE = BASE
