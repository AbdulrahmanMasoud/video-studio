# Credentials and where to put them

Everything is configured through `.env` (copy of `.env.example`; never committed). Each key below says where to get it,
which services read it, and whether the product works without it.

| key | what it is | where to get it | needed for |
|---|---|---|---|
| `SECRET_KEY` | signs JWTs and email tokens | `openssl rand -hex 32` | **required in prod** (any value works in dev) |
| `ADMIN_API_KEY` | `X-Admin-Key` header for `/admin/*` | `openssl rand -hex 24` | admin endpoints |
| `WEB_ORIGIN`, `API_BASE_URL` | public URLs | your domain (prod: `https://app.example.com`) | cookies, CORS, links in emails, checkout redirects |
| `DATABASE_URL*`, `REDIS_URL` | Postgres / Redis | compose defaults; in prod point at your managed services | everything |
| `S3_*` | object storage | dev: MinIO defaults. prod: Cloudflare R2 (R2 → Manage R2 API tokens → create token with Object Read & Write; `S3_ENDPOINT_URL=https://<account_id>.r2.cloudflarestorage.com`, `S3_PUBLIC_ENDPOINT_URL` = same or your custom domain, `S3_FORCE_PATH_STYLE=0`) | uploads, outputs |
| `EMAIL_PROVIDER=resend`, `RESEND_API_KEY`, `EMAIL_FROM` | transactional email in prod | resend.com → API Keys; verify your sending domain, use a `From` on it | verification, reset, render done, payment failed |
| `PAYMENTS_PROVIDER=lemonsqueezy` | switches billing from mock to Lemon Squeezy | — | paid plans |
| `LEMONSQUEEZY_API_KEY` | API key | app.lemonsqueezy.com → Settings → API → **Create API key** (test mode keys only work while the store is in test mode) | creating checkouts, refreshing portal links |
| `LEMONSQUEEZY_STORE_ID` | numeric store id | Settings → Stores (the number in the URL, or `GET /v1/stores`) | checkouts |
| `LEMONSQUEEZY_VARIANT_STARTER` / `_PRO` / `_AGENCY` | numeric **variant** ids of the three subscription products | Products → open the product → the variant id is in the URL `…/products/<product>/variants/<variant>` (create 3 subscription products at $15 / $29 / $79 monthly) | checkouts, mapping webhooks to plans |
| `LEMONSQUEEZY_WEBHOOK_SECRET` | signing secret you choose when creating the webhook | Settings → Webhooks → **+** → URL `https://<api host>/billing/webhooks/lemonsqueezy`, secret = any random string (put the same value here), events: `subscription_created`, `subscription_updated`, `subscription_cancelled`, `subscription_resumed`, `subscription_expired`, `subscription_paused`, `subscription_unpaused`, `subscription_payment_success`, `subscription_payment_failed`, `subscription_payment_recovered`, `order_refunded` | verifying webhooks (unsigned requests are rejected with 401) |
| `ANTHROPIC_API_KEY` | default LLM provider | console.anthropic.com → API keys | AI storyboards (without any key the deterministic fallback planner is used) |
| `OPENAI_API_KEY` | OpenAI (also for `TTS_PROVIDER=openai`) | platform.openai.com → API keys | optional provider; AI voice |
| `GEMINI_API_KEY`, `OPENROUTER_API_KEY`, `GROQ_API_KEY`, `OLLAMA_BASE_URL` | other providers | Google AI Studio / openrouter.ai / console.groq.com / your Ollama host | optional; appear as "available" in `GET /admin/llm` |
| `LLM_MODEL_PLANNER`, `LLM_MODEL_FAST`, `LLM_MODEL_VISION`, `PLANNER_MODEL_FREE`, `PLANNER_MODEL_PAID`, `LLM_FALLBACK_CHAIN` | model routing (LiteLLM model strings) | optional; editable without redeploy via `PUT /admin/llm` | cost/quality routing |
| `SENTRY_DSN` | error reporting | sentry.io → project → DSN | optional (Phase 6) |

## Lemon Squeezy, step by step

1. Create the store (test mode is fine to start), then three **subscription** products: Starter $15/mo, Pro $29/mo, Agency $79/mo.
   Copy each product's default **variant id** into `LEMONSQUEEZY_VARIANT_STARTER/PRO/AGENCY`.
2. Settings → API → create an API key → `LEMONSQUEEZY_API_KEY`. Settings → Stores → store id → `LEMONSQUEEZY_STORE_ID`.
3. Settings → Webhooks → add `https://<api host>/billing/webhooks/lemonsqueezy` with the events listed above and a signing secret →
   `LEMONSQUEEZY_WEBHOOK_SECRET`. For local testing, expose the API with a tunnel (e.g. `ngrok http 8000`) and use that URL.
4. Set `PAYMENTS_PROVIDER=lemonsqueezy`, restart (`make up`). `GET /billing/checkout` now returns hosted checkout URLs; the customer portal
   link comes from the subscription. Credits renew on every `subscription_payment_success`; `subscription_expired` downgrades to free;
   `order_refunded` removes the plan's credits and downgrades.
5. Verify with the Lemon Squeezy dashboard "Send test event" button, then watch `webhook_events` (or `GET /admin/webhooks`).

While `PAYMENTS_PROVIDER=mock`, `POST /billing/mock/subscribe` and the billing page's test checkout switch plans instantly.

## Where the owner must act before launch

- Replace `SECRET_KEY`, `ADMIN_API_KEY`, the Postgres password and the S3 keys with real random values.
- Set `COOKIE_SECURE=1`, `APP_ENV=prod`, `WEB_ORIGIN=https://…` (email verification is enforced only in prod).
- Provide the legal texts for `/terms`, `/privacy`, `/refunds`.
