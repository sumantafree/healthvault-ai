// HealthVault AI — Authenticated API Client
// Automatically injects Supabase JWT into every request.
import axios, { type AxiosInstance } from "axios";
import { createClient } from "@/lib/supabase/client";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function createApiClient(): AxiosInstance {
  const instance = axios.create({
    baseURL: `${API_URL}/api/v1`,
    headers: { "Content-Type": "application/json" },
  });

  // Inject Bearer token before every request
  instance.interceptors.request.use(async (config) => {
    const supabase = createClient();
    const { data } = await supabase.auth.getSession();
    if (data.session?.access_token) {
      config.headers.Authorization = `Bearer ${data.session.access_token}`;
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
