#!/bin/bash
# HealthVault AI — Render.com frontend startup
set -e
exec node_modules/.bin/next start -p ${PORT:-3000}
