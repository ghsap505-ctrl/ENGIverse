# Architecture — ENGIverse 0.1.1

Modular monolith. One deployable backend; domains are packages, not services.

```
backend/app/
  main.py            create_app(): middleware, CORS, error handlers, routers
  core/              config (pydantic-settings), validators, logging, errors, middleware, context
  api/v1/            HTTP layer: router.py aggregates module routers; health.py
  db/                base.py (Base + naming convention), session.py (engine/pool/get_db), models/
  modules/           future domains: identity, courses, tutor ... (no cross-module internals)
backend/alembic/     migrations; URL comes from Settings, never from alembic.ini
```

## Decisions
- **Config in one place, fail fast.** No secret defaults; app refuses to start without a DB password. Validation errors never echo values (`hide_input_in_errors`, messages exclude URLs).
- **Stdlib-only validators/logging** so security-critical parsing is testable without the framework.
- **Lazy engine.** Importing the app never connects to the DB; readiness (`/health/ready`) is separate from liveness (`/health`) so a DB blip does not restart healthy API containers.
- **Uniform error envelope** `{"error":{"code","message","request_id","details?"}}`; validation errors omit submitted input; 500s are generic.
- **Request IDs** accepted only if they match a strict pattern, else regenerated (log-injection safe). One structured access log per request, path only (no query string).
- **Stateless API process**; scale horizontally via replicas. Connection budget = replicas × workers × (pool_size + max_overflow) must stay below PostgreSQL `max_connections` (or add PgBouncer). No Redis yet: nothing in 0.1.1 justifies it.
- **Compose:** prod-like by default, dev via override. DB on an internal network, only nginx published.
- pgvector is not enabled; the stock `postgres:16-alpine` image lacks it. Switch the image when vector search lands.
