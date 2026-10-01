# Web image: Next.js standalone build. API_INTERNAL_URL is baked at build time for the /api rewrite (dev/prod use http://api:8000).
FROM node:22-bookworm-slim AS deps
WORKDIR /app
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci --no-audit --no-fund

FROM node:22-bookworm-slim AS build
WORKDIR /app
ARG API_INTERNAL_URL=http://api:8000
ENV API_INTERNAL_URL=${API_INTERNAL_URL} NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /app/node_modules ./node_modules
COPY apps/web ./
COPY packages/shared ../packages/shared
COPY docs/previews ./public/previews
RUN npm run build

FROM node:22-bookworm-slim AS runner
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=3000 HOSTNAME=0.0.0.0
RUN useradd -m -u 10003 web
COPY --from=build --chown=web:web /app/.next/standalone ./
COPY --from=build --chown=web:web /app/.next/static ./.next/static
COPY --from=build --chown=web:web /app/public ./public
USER web
EXPOSE 3000
CMD ["node", "server.js"]
