// Browser-side Supabase client (singleton)
//
// IMPORTANT: must be a true singleton. createBrowserClient() creates a new
// auth lock per instance — calling it on every render/request causes
// "Lock was not released within 5000ms" deadlocks that hang every API call.
import { createBrowserClient } from "@supabase/ssr";
import type { SupabaseClient } from "@supabase/supabase-js";

let _client: SupabaseClient | undefined;

export function createClient(): SupabaseClient {
  if (_client) return _client;
  _client = createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );
  return _client;
}
