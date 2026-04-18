// Supabase OAuth callback — exchanges the PKCE `code` for a session cookie,
// then redirects into the app. Must be a Route Handler (server-side) so the
// cookie is set on the response.
import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get("code");
  const next = searchParams.get("next") ?? "/dashboard";

  if (code) {
    const supabase = createClient();
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (!error) {
      return NextResponse.redirect(`${origin}${next}`);
    }
    // Surface the real error so we can debug — safe because it's just the
    // OAuth flow reason, not a secret.
    console.error("auth callback exchange failed:", error.message);
    const msg = encodeURIComponent(error.message || "unknown");
    return NextResponse.redirect(`${origin}/login?error=${msg}`);
  }

  return NextResponse.redirect(`${origin}/login?error=no_code_in_callback`);
}
