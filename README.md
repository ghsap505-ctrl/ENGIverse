# ENGIverse
Universal Engineering Intelligence & Learning Ecosystem

**Version 0.1.2 — Verification Fixes.** React + TypeScript + Vite frontend, FastAPI
backend with centralised config / structured logging / uniform errors, PostgreSQL via
SQLAlchemy + Alembic infrastructure, hardened Docker setup. No authentication yet (0.2).

> **Status:** backend unit tests verified in this environment; full-stack verification remains incomplete. The build/test environment used to
> produce this release had no network, so `pytest`, `npm run build`, and Docker builds were NOT RUN.
> See `docs/0.1.2_VERIFICATION_REPORT.md` for exactly what was and was not executed. Run the
> verification steps below on your machine before relying on it. Development scaffold, not production-ready.

## Layout
```
backend/   FastAPI app (app/core, app/api/v1, app/db, app/modules), alembic/, tests/
frontend/  React + TS + Vite (nginx image for production)
docker-compose.yml       production-like (default)
docker-compose.dev.yml   development overrides
scripts/static_checks.py repository-level structural checks
```

## 1. Verify first (recommended order)
```bash
python3 scripts/static_checks.py                     # needs python3 + PyYAML; no network

# Backend tests (Python 3.12)
cd backend && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest                                      # unit tests; integration tests auto-skip

# Frontend: generate the lockfile ONCE, commit it, then build
cd ../frontend
npm install --package-lock-only && npm ci
npm run build                                         # tsc -b && vite build

# Compose validation
cd .. && cp .env.example .env                         # then set POSTGRES_PASSWORD
docker compose config -q
docker compose -f docker-compose.yml -f docker-compose.dev.yml config -q
```
Without `POSTGRES_PASSWORD`, `docker compose config` must fail — that is intended.

## 2. Run in development (Docker)
```bash
cp .env.example .env
# set a strong, URL-safe password:  openssl rand -hex 24   → POSTGRES_PASSWORD=
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```
- Frontend http://localhost:5173 · API http://localhost:8000/api/v1/health · Docs http://localhost:8000/docs
- Readiness (checks PostgreSQL): http://localhost:8000/api/v1/health/ready
- All ports bind to `127.0.0.1` only.

## 3. Run production-like (Docker)
```bash
docker compose up --build -d
```
Only the frontend is published (`127.0.0.1:8080`); nginx proxies `/api/` to the backend, so
no CORS is needed. The database and backend have no host ports. Put a TLS-terminating reverse
proxy in front; TLS is not configured in this repo. API docs are disabled in production.

## 4. Backend without Docker
```bash
cd backend && cp .env.example .env     # edit DATABASE_URL (password required)
uvicorn app.main:app --reload
alembic heads                           # no migrations yet; first ones arrive in 0.2
```

## 5. Database integration tests
```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d db
cd backend && TEST_DATABASE_URL="postgresql+psycopg://engiverse:<password>@localhost:5432/engiverse" \
  python -m pytest -m integration
```

## Configuration (backend, environment variables)
| Variable | Required | Notes |
|---|---|---|
| `DATABASE_URL` | **yes** | `postgresql+psycopg://user:password@host:port/db`; password mandatory; ≥16 chars & non-placeholder when `APP_ENV=production` |
| `APP_ENV` | no | `development` (default) / `test` / `production` |
| `CORS_ORIGINS` | no | comma-separated bare origins; wildcards rejected; empty = no CORS |
| `LOG_LEVEL`, `LOG_FORMAT` | no | `INFO`, `json` (or `text`) |
| `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_TIMEOUT`, `DB_POOL_RECYCLE`, `DB_CONNECT_TIMEOUT` | no | pool tuning |
| `DOCS_ENABLED` | no | default: on outside production, off in production |

Compose passes `POSTGRES_*` to the db and assembles `DATABASE_URL` for the backend, so the password lives in one place (`.env`).
