# Security baseline

Before production:
- Enforce HTTPS and secure cookie/session settings.
- Hash passwords with Argon2id; never store plaintext credentials.
- Keep provider API keys on the server and out of frontend bundles.
- Enforce per-user authorization on every course/document query.
- Validate file type, size, and content; store uploads outside the web root.
- Treat uploaded documents as untrusted data, never as system instructions.
- Sandbox code execution and simulation workloads with CPU, memory, and time limits.
- Add rate limiting, audit logging, backups, and dependency scanning.

## Status after 0.1.1
Done (statically verified, runtime unverified): no default DB credentials, password required,
DB not published, non-root containers, read-only root FS for runtime containers, configurable
CORS (no wildcards), baseline security headers (API + nginx CSP), request IDs, no-secret errors.
Still open: TLS, authentication/authorization (0.2), rate limiting (0.2), audit logging (0.2),
self-hosted fonts (CSP currently allows Google Fonts), dependency scanning, hash-locked Python
deps, backups, image digest pinning.
