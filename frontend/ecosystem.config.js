// HealthVault AI — PM2 Process Manager Config for Next.js
// Usage:
//   pm2 start ecosystem.config.js
//   pm2 save
//   pm2 startup   (then run the command it prints)

module.exports = {
  apps: [
    {
      name:         "healthvault-app",
      script:       "node_modules/.bin/next",
      args:         "start",
      cwd:          "/var/www/healthvault-ai/frontend",
      instances:    1,              // increase for multi-core (or use "max")
      exec_mode:    "fork",
      autorestart:  true,
      watch:        false,
      max_memory_restart: "512M",

      env: {
        NODE_ENV:                    "production",
        PORT:                        3000,
        NEXT_PUBLIC_SUPABASE_URL:    "https://YOUR_PROJECT.supabase.co",
        NEXT_PUBLIC_SUPABASE_ANON_KEY: "YOUR_ANON_KEY",
        NEXT_PUBLIC_API_URL:         "https://api.yourdomain.com",
      },

      // Logging
      out_file:     "/var/log/healthvault/nextjs-out.log",
      error_file:   "/var/log/healthvault/nextjs-err.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss",
      merge_logs:   true,
    },
  ],
};
