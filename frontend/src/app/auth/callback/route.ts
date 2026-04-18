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
    // Log the real reason in server logs, but don't leak to user
    console.error("auth callback exchange failed:", error.message);
  }

  // Anything went wrong → send them back to login with an error flag
  return NextResponse.redirect(`${origin}/login?error=auth_callback_failed`);
}
