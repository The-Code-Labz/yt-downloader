# ─── build stage ────────────────────────────────────────────────────────────
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install --no-audit --no-fund
COPY . .

# No VITE_* build args here on purpose: the actual API URL / Supabase project
# is injected at container *start* (see docker-entrypoint.d/40-env-config.sh),
# so this single image is reusable across every self-hosted deployment without
# a rebuild. import.meta.env.VITE_* stays as a dev-only fallback (see src/lib/runtime-env.ts).
RUN npm run build

# ─── runtime stage ──────────────────────────────────────────────────────────
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
COPY docker-entrypoint.d/40-env-config.sh /docker-entrypoint.d/40-env-config.sh
RUN chmod +x /docker-entrypoint.d/40-env-config.sh
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
