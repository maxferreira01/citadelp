/* API CITADEL — proxy do vite: /api/* → uvicorn :5533 */
export async function api(path, opts = {}) {
  const token = sessionStorage.getItem("citadel_token");
  const res = await fetch("/api" + path, {
    headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    ...opts,
  });
  if (!res.ok) {
    let detail = "";
    try { detail = (await res.json()).detail || ""; } catch { /* corpo não-JSON */ }
    throw new Error(detail || `HTTP ${res.status}`);
  }
  return res.json();
}
