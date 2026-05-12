# Fork of letta-ai/letta

This repo is a **soft fork** of [`letta-ai/letta`](https://github.com/letta-ai/letta), maintained as `cognis-concierge` under the Cognis AI platform. License posture: Apache-2.0 core only. Upstream is single-tier Apache-2.0 — no `enterprise/`, `ee/`, `cloud/`, `pro/`, or `saas/` directories exist, so no strip recipe is required at fork time.

Cognis Concierge is the personal-AI / stateful-memory product (Phase 3). It surfaces Letta's memory primitives (archival memory, core memory blocks, agent state) wrapped in Cognis branding, Clerk auth, and Bridge-mediated multi-tenancy.

## Branches

| Branch | Purpose |
|---|---|
| `vendor/upstream` | Mirror of `letta-ai/letta:main`. NEVER edit. Rebased by the nightly bot. |
| `cognis/main` | Cognis work. Rebased monthly onto `vendor/upstream`. Default branch. |

## Commit prefixes (grep-friendly across rebases)

- `fork:` — surgical edits to upstream files (last resort; prefer Bridge integration)
- `brand:` — branding (logos, prompt overlays, default personas)
- `wire:` — Cognis integration plumbing (Clerk auth middleware, Bridge clients, LiteLLM provider wiring)
- `ci:` — GitHub Actions, license gate, rebase bot
- `docs:` — FORK.md, CLAUDE.md, CODEOWNERS, READMEs

## License-trap status

Verified 2026-05-12 at upstream SHA `bb52a890`:

- LICENSE is plain Apache-2.0 (no Commons Clause rider, no addendum)
- No `enterprise/`, `ee/`, `cloud/`, `pro/`, `saas/`, `platform/` trap directories at any depth
- `pyproject.toml` declares `license = {text = "Apache License"}` with optional-deps grouped by purpose only — no premium extra
- `TERMS.md` / `PRIVACY.md` / `AI_POLICY.md` are user-facing legal text for Letta's hosted product, not a code-license overlay

If upstream adds a `pro/` / `ee/` / equivalent directory in a future rebase, the strip happens in a **separate commit** before merging — same doctrine as `cognis-support`.

## Fork-diff target

≤3% of upstream LOC (default per fork-ops.md). Tracked on every PR via `git diff vendor/upstream...cognis/main --stat`. Hard cap 5% — build fails above that.

## Rebase cadence

- Nightly bot: `.github/workflows/upstream-rebase.yml` (schedule kept but the workflow is currently set up; flip `cron` only after first manual rebase has been verified to work cleanly against Letta's release pace)
- Auto-merge clean rebases via Mergify (configured at platform level once first rebase lands)
- Conflicts → bot opens issue labeled `rebase-conflict`; human review
- Shared `rerere-cache` committed to `cognis-platform/infra/rerere-cache/cognis-concierge/`

## Cognis-side surface

What lives on `cognis/main` (and ONLY here):

- `FORK.md`, `CLAUDE.md`, `CODEOWNERS` — fork meta
- `.github/workflows/license-gate.yml` — ScanCode allowlist enforcement
- `.github/workflows/upstream-rebase.yml` — nightly rebase bot
- (future) `letta/server/rest_api/middleware/cognis_auth.py` — Clerk JWT → org_id resolver, calling Bridge for tenant lookup
- (future) `letta/llm_api/cognis_provider.py` — thin wrapper pinning the OpenAI-compatible client at `llm.cognisai.com`
- (future) `letta/branding/` — Cognis logos + default system-prompt overlay

All product-level multi-tenant logic lives in `cognis-platform/apps/bridge`, NOT here.

## Upstream-PR policy

Contribute back to `letta-ai/letta` *before* merging to `cognis/main`:

- Bug fixes, perf patches, test improvements, type fixes, refactors that shrink fork diff

Keep in fork (do NOT upstream):

- Clerk / Stripe / LiteLLM-gateway / Cognis-branded code
- Cognis-specific multi-tenant primitives, billing meters, audit integration with Bridge

## References

- Fork-ops doctrine: `cognis-platform/docs/specs/fork-ops.md`
- Bridge integration spec: `cognis-platform/docs/specs/bridge-service.md`
- LLM gateway: `cognis-platform/docs/specs/ai-gateway.md`
