#!/bin/sh
# Runs automatically by the official nginx image before nginx starts
# (any executable *.sh in /docker-entrypoint.d/ is sourced by docker-entrypoint.sh).
# Writes runtime env vars into a static file the SPA loads before its bundle,
# so the same published image works for every self-hosted deployment without
# a rebuild — VITE_API_URL / VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY are
# read from the container environment, not baked in at `docker build` time.
set -eu

CONFIG_FILE="/usr/share/nginx/html/env-config.js"

cat > "$CONFIG_FILE" <<EOF
window.__ENV__ = {
  API_URL: "${VITE_API_URL:-}",
  SUPABASE_URL: "${VITE_SUPABASE_URL:-}",
  SUPABASE_ANON_KEY: "${VITE_SUPABASE_ANON_KEY:-}"
};
EOF
