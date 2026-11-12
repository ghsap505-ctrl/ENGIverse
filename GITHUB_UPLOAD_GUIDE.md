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
- Dependency lockfiles: none existed in the supplied 0.1.2 candidate; generate and commit the appropriate lockfile through the package manager after dependency resolution.

The `.env.example` files contain placeholders only. Copy them locally to `.env` and fill in secrets outside GitHub.
