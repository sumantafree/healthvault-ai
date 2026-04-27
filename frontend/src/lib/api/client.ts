// HealthVault AI — Authenticated API Client
// Reads the Supabase access token directly from cookies to avoid the GoTrue
// auth lock contention that hangs `supabase.auth.getSession()` on some
// React Strict Mode + Next.js App Router setups.
import axios, { type AxiosInstance } from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/**
 * Pull the current access token from `sb-<projectref>-auth-token` cookies.
 * `@supabase/ssr` 0.5+ stores the session as a JSON blob (sometimes split
 * across `.0` / `.1` chunks, sometimes `base64-`-prefixed).
 */
function readAccessTokenFromCookies(): string | null {
  if (typeof document === "undefined") return null;
  try {
    const chunks = document.cookie
      .split(";")
      .map((c) => c.trim())
      .filter((c) => c.includes("auth-token") && !c.includes("verifier"))
      .sort();
    if (chunks.length === 0) return null;
    let raw = "";
    for (const c of chunks) {
      raw += decodeURIComponent(c.split("=").slice(1).join("="));
    }
    if (raw.startsWith("base64-")) {
      raw = atob(raw.slice(7));
    }
    const parsed = JSON.parse(raw);
    return parsed?.access_token ?? null;
  } catch {
    return null;
  }
}

function createApiClient(): AxiosInstance {
  const instance = axios.create({
    baseURL: `${API_URL}/api/v1`,
    headers: { "Content-Type": "application/json" },
  });

  // Inject Bearer token before every request — synchronous, no awaits.
  instance.interceptors.request.use((config) => {
    const token = readAccessTokenFromCookies();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  // Unified error shape
  instance.interceptors.response.use(
    (res) => res,
    (err) => {
      const message =
        err.response?.data?.detail ?? err.message ?? "An error occurred.";
      return Promise.reject(new Error(message));
    }
  );

  return instance;
}

export const apiClient = createApiClient();
