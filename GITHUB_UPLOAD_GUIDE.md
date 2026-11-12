# GitHub upload guide — ENGIverse 0.1.2

Upload the contents of this folder to the root of your private GitHub repository.
Do not upload local secrets, `.env` files, caches, virtual environments, `node_modules`, build outputs, or local database files.

## Included
- Backend application source, tests, requirements, and Alembic configuration
- Frontend source, package manifest, Vite/TypeScript/Tailwind configuration
- Dockerfiles and Docker Compose files
- Documentation, scripts, `.gitignore`, and safe `.env.example` templates

## Not included intentionally
- `.env` and any real credentials
- `.pytest_cache`, `__pycache__`, `.venv`, `node_modules`, `dist`, `build`
- Local database files, logs, private keys/certificates
- `frontend/package-lock.json` is committed and must be used with `npm ci` for reproducible installs.

The `.env.example` files contain placeholders only. Copy them locally to `.env` and fill in secrets outside GitHub.
