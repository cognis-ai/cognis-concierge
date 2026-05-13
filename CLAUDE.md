# Cognis Concierge — repo context for Claude

This is a soft fork of `letta-ai/letta`. **The fork is not the product — `cognis-platform/apps/bridge` is.** Every hour spent editing Letta's FastAPI routers or SQLAlchemy ORM here costs 3× at next rebase.

## Branches

- `cognis/main` — default. Cognis work.
- `vendor/upstream` — mirror of letta-ai/letta:main. NEVER edit.

## Hard rules

1. **No license traps to restore.** Upstream is Apache-2.0 single-tier (verified at fork time, SHA `bb52a890`, 2026-05-12). If upstream introduces `pro/`, `ee/`, `cloud/`, `saas/`, or `platform/` directories in a future rebase, strip in a SEPARATE commit before merging — never restore them.
2. **Never edit upstream Python files.** Use:
   - FastAPI dependency-injection / middleware (the upstream extension point in `letta/server/rest_api/`)
   - Plugin / provider registration via `letta/plugins/` and `letta/llm_api/`
   - Bridge webhooks from `cognis-platform/apps/bridge`
   If you must touch an upstream file, the PR upstream is **mandatory** before merging to `cognis/main`.
3. **Fork-diff cap: 5% of upstream LOC.** Tracked per-PR. Target ≤3%.
4. **Commit prefixes only:** `fork:` / `brand:` / `wire:` / `ci:` / `docs:`.
5. **All Cognis-specific multi-tenant + billing logic goes in Bridge.** This repo holds: Cognis-branded prompts / logos, optional Clerk auth FastAPI dependency, and FORK.md/CLAUDE.md/CODEOWNERS.
6. **Never `pip install letta[<premium-extra>]`.** Today no such extra exists. If one appears upstream, CI license-gate must block it before merge.

## Build & test (upstream Letta tooling)

Letta uses `uv` + `hatchling` + Alembic + FastAPI + SQLAlchemy + Pydantic. Standard upstream commands:

- `uv sync` — install deps from `uv.lock`
- `uv run pytest` — run tests
- `uv run alembic upgrade head` — apply DB migrations
- `uv run letta server` — local server
- `docker compose -f dev-compose.yaml up` — full dev stack (Postgres+pgvector)

See upstream README + CONTRIBUTING.md for details. Do NOT add a separate package manager (no Poetry, no pip-tools) — stay on `uv`.

## What lives here

Currently (post-bootstrap + Phase 3 wire):
- `FORK.md`, `CLAUDE.md`, `CODEOWNERS` — fork meta
- `.github/workflows/license-gate.yml` — ScanCode + trap-dir gate
- `.github/workflows/upstream-rebase.yml` — nightly rebase bot (schedule kept; flip after first manual rebase)
- `letta/server/rest_api/middleware/cognis_auth.py` — **Cognis-side auth entrypoint.** FastAPI dependency that verifies a Clerk JWT (RS256 + JWKS), maps the `org_id` claim to a Letta `organization_id` via `organizations.cognis_org_id`, and sets `request.state.{actor_id,organization_id,cognis_org_id}` for downstream routes. Mounted on all `/v1/*` routers except `/v1/health` in `app.py`. No-op if `JWT_PUBLIC_KEY_URL` is unset (local dev preserves upstream parity).
- `letta/branding/cognis_brand.py` — env-driven Cognis brand constants (name / tagline / logo / support email). Importable as `letta.branding.cognis_brand`. Consumed by future UI / template wiring.
- `alembic/versions/c0951a13aa55_add_cognis_org_id_to_organization.py` — additive nullable `cognis_org_id` column on `organizations` + partial unique index.

Planned (Phase 3 follow-up):
- `letta/llm_api/cognis_provider.py` — OpenAI-compatible provider pinned at `llm.cognisai.com` (the LiteLLM proxy) — only if needed; current direction is env-only override (see deployment env below).
- Cognis system-prompt overlay + default persona under `letta/branding/`
- `tools/check_no_proprietary.py` (copied from `cognis-platform/infra/fork-templates/`)

## Auth pattern with Bridge

Default = Pattern A (Bridge proxy). Cognis portal calls Bridge, Bridge holds Letta admin credentials, Bridge proxies API calls to Concierge with `Authorization: Bearer <letta-admin-key>`. Token never reaches the browser.

Pattern B (FastAPI dependency in this repo) — `letta/server/rest_api/middleware/cognis_auth.py`. Active when direct Concierge UI access is required for "memory inspection" / debug surface. Enable by setting `JWT_PUBLIC_KEY_URL` (Clerk JWKS) and optionally `JWT_ISSUER` / `JWT_AUDIENCE`.

## Deployment env (production rules)

LLM provider base URLs MUST be set via env at deployment time — never hard-coded in source — per `cognis-platform/docs/specs/cost-policy.md`. Concrete envs Letta already honors via `letta/settings.py`:

- `OPENAI_API_BASE` — point at `https://llm.cognisai.com/openai/v1` (LiteLLM proxy)
- `ANTHROPIC_BASE_URL` — point at the LiteLLM Anthropic-shape endpoint
- `GEMINI_BASE_URL`, `AZURE_BASE_URL`, `VLLM_API_BASE`, `SGLANG_API_BASE`, `LMSTUDIO_BASE_URL` — set as appropriate

Cognis production deploys MUST:

- Use **Postgres** (NOT SQLite) — APScheduler leader election relies on Postgres advisory locks.
- **NOT** set `SENTRY_DSN`, `DD_API_KEY`, `LANGSMITH_API_KEY` — gated out per `cost-policy.md`. The Sentry / Datadog / Langsmith dependencies ship in `pyproject.toml` because Letta packages them, but they stay inert without env vars.
- Set `JWT_PUBLIC_KEY_URL` (Clerk JWKS) to activate `cognis_auth.py`.

## What NOT to do

- Don't run Letta's hosted-product onboarding scripts (Letta Cloud configs are not for us)
- Don't add NestJS / Bridge logic here — that's in `cognis-platform/apps/bridge`
- Don't touch `vendor/upstream` directly — it's a mirror branch
- Don't commit credentials; `.env.example` is the only env file that ships
- Don't `pip install litellm[enterprise]` (platform-wide rule from cognis-platform/CLAUDE.md)
- Don't bypass `@cognis/llm-client` for LLM calls in the future Bridge wire-up — the Concierge server can call OpenAI-compatible endpoints, but the endpoint URL MUST be `llm.cognisai.com`, never a raw provider
