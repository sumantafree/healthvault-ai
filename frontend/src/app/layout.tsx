import type { Metadata } from "next";
import { Toaster } from "sonner";
import QueryProvider from "./providers";
import "./globals.css";

export const metadata: Metadata = {
  title: { default: "HealthVault AI", template: "%s | HealthVault AI" },
  description: "Family Health Intelligence Platform — AI-powered health tracking and insights.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <QueryProvider>
          {children}
          <Toaster position="top-right" richColors expand={false} />
        </QueryProvider>
      </body>
    </html>
  );
}
