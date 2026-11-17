export class ApiError extends Error {}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  const token = sessionStorage.getItem("erp_token");
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(path, { ...options, headers });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = (body as { detail?: unknown }).detail;
    const message = typeof detail === "string" ? detail : "No se pudo completar la operación.";
    if (response.status === 401 && !path.endsWith("/api/auth/login")) {
      sessionStorage.removeItem("erp_token");
      if (window.location.pathname !== "/login") window.location.assign("/login");
    }
    throw new ApiError(message);
  }
  return body as T;
}

export function money(value: number) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(value || 0);
}
