# Playwright + Lighthouse runner for the web e2e suite (CI and `make test-web`).
FROM mcr.microsoft.com/playwright:v1.63.0-noble
WORKDIR /e2e
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY apps/web/playwright.config.ts ./
COPY apps/web/e2e ./e2e
ENV CI=1
CMD ["npx", "playwright", "test"]
