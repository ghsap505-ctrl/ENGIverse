// Same-origin by default: in production nginx proxies /api to the backend,
// so no CORS and no absolute URL is needed. Dev compose overrides this.
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'

export async function getHealth() {
  const response = await fetch(`${API_BASE}/health`)
  if (!response.ok) throw new Error(`API error: ${response.status}`)
  return response.json() as Promise<{ status: string; service: string; version: string }>
}
