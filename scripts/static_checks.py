#!/usr/bin/env python3
"""Static repository checks (no network, no Docker, no installed deps needed).

These are STRUCTURAL checks. They do not replace `pytest`, `npm run build`,
`docker compose config` or image builds; they catch regressions of the specific
issues found in the 0.1 audit. Requires: Python 3.12 + PyYAML.
"""
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))


# 1. Python syntax
excluded_parts = {"__pycache__", "node_modules", ".pytest_cache", ".vite", "dist", "build"}
py_files = [p for p in ROOT.rglob("*.py")
            if not any(part in excluded_parts or part.startswith(".venv") for part in p.parts)]
bad = []
for p in py_files:
    try:
        compile(p.read_text(), str(p), "exec")  # syntax only; writes no .pyc
    except SyntaxError as e:
        bad.append(f"{p.relative_to(ROOT)}:{e.lineno}: {e.msg}")
check(f"python syntax ({len(py_files)} files)", not bad, "; ".join(bad))

# 2. Frontend: exact pins, vite types
pkg = json.loads((ROOT / "frontend/package.json").read_text())
floating = {k: v for sec in ("dependencies", "devDependencies") for k, v in pkg[sec].items()
            if not re.fullmatch(r"\d+\.\d+\.\d+", v)}
check("frontend deps are exact versions (no latest/^/~)", not floating, str(floating))
tsc = json.loads((ROOT / "frontend/tsconfig.json").read_text())
check("tsconfig strict + vite/client types",
      tsc["compilerOptions"].get("strict") is True
      and "vite/client" in tsc["compilerOptions"].get("types", []))
check("vite-env.d.ts present", (ROOT / "frontend/src/vite-env.d.ts").exists())
check("frontend package-lock.json present", (ROOT / "frontend/package-lock.json").exists(),
      "generate with `npm install --package-lock-only` on a networked machine")
backend_version = re.search(r'^version\s*=\s*"([^"]+)"',
                            (ROOT / "backend/pyproject.toml").read_text(), re.MULTILINE)
check("backend project version is 0.1.2", backend_version is not None
      and backend_version.group(1) == "0.1.2", str(backend_version.group(1) if backend_version else None))
check("frontend package version is 0.1.2", pkg.get("version") == "0.1.2",
      str(pkg.get("version")))
app_ts = (ROOT / "frontend/src/App.tsx").read_text()
check("frontend displays version 0.1.2", "v0.1.2" in app_ts, "v0.1.2 not found")

# 3. Backend requirements pinned and split
for f in ("requirements.txt", "requirements-dev.txt"):
    lines = [l.strip() for l in (ROOT / "backend" / f).read_text().splitlines()
             if l.strip() and not l.startswith(("#", "-r"))]
    unpinned = [l for l in lines if "==" not in l]
    check(f"backend/{f} fully pinned", not unpinned, str(unpinned))
rt = (ROOT / "backend/requirements.txt").read_text().lower()
check("runtime requirements exclude pytest/httpx", "pytest" not in rt and "httpx" not in rt)

# 4. Compose security
base = yaml.safe_load((ROOT / "docker-compose.yml").read_text())
dev = yaml.safe_load((ROOT / "docker-compose.dev.yml").read_text())
svc = base["services"]
check("base: db publishes no ports", "ports" not in svc["db"])
check("base: backend publishes no ports", "ports" not in svc["backend"])
check("base: POSTGRES_PASSWORD is required (':?')",
      ":?" in svc["db"]["environment"]["POSTGRES_PASSWORD"]
      and ":?" in svc["backend"]["environment"]["DATABASE_URL"])
check("base: frontend binds host port to loopback by default",
      all("${FRONTEND_BIND:-127.0.0.1}" in p for p in svc["frontend"]["ports"]))
check("base: backend has healthcheck", "healthcheck" in svc["backend"])
check("base: backend hardened (read_only, cap_drop, no-new-privileges)",
      svc["backend"].get("read_only") is True and svc["backend"].get("cap_drop") == ["ALL"]
      and "no-new-privileges:true" in svc["backend"].get("security_opt", []))
check("base: db on internal-only network", svc["db"]["networks"] == ["internal"]
      and base["networks"]["internal"].get("internal") is True)
check("base: build targets are prod",
      svc["backend"]["build"]["target"] == "prod" and svc["frontend"]["build"]["target"] == "prod")
dev_ports = [p for s in dev["services"].values() for p in s.get("ports", [])]
check("dev: every published port binds 127.0.0.1", all(p.startswith("127.0.0.1:") for p in dev_ports),
      str(dev_ports))
check("dev: build targets are dev",
      dev["services"]["backend"]["build"]["target"] == "dev"
      and dev["services"]["frontend"]["build"]["target"] == "dev")

# 5. Dockerfiles / dockerignore
bd = (ROOT / "backend/Dockerfile").read_text()
check("backend Dockerfile: non-root USER in dev and prod stages",
      bd.count("USER app") == 2 and "--reload" in bd.split("AS prod")[0]
      and "--reload" not in bd.split("AS prod")[1])
check("backend Dockerfile: prod has HEALTHCHECK", "HEALTHCHECK" in bd.split("AS prod")[1])
check("frontend Dockerfile: prod uses unprivileged nginx", "nginx-unprivileged" in
      (ROOT / "frontend/Dockerfile").read_text())
fd = (ROOT / "frontend/Dockerfile").read_text()
check("frontend Dockerfile: copies lockfile and uses npm ci",
      "COPY package.json package-lock.json ./" in fd and "npm ci" in fd,
      "Docker build must use the committed lockfile")
for d in ("backend", "frontend"):
    check(f"{d}/.dockerignore present and excludes .env",
          (ROOT / d / ".dockerignore").exists() and ".env" in (ROOT / d / ".dockerignore").read_text())

# 6. No default credentials anywhere in shipped config/code
needle = "change-this-password"
allowed = {"backend/app/core/validators.py", "backend/tests/test_validators.py",
           "backend/tests/test_config.py", "docs/0.1.1_CHANGE_REPORT.md",
           "scripts/static_checks.py"}
hits = [str(p.relative_to(ROOT)) for p in ROOT.rglob("*")
        if p.is_file() and p.suffix in {".py", ".yml", ".yaml", ".md", ".example", ".json", ".ts", ".tsx"}
        and needle in p.read_text(errors="ignore") and str(p.relative_to(ROOT)) not in allowed]
check("no default DB password in config/docs/code", not hits, str(hits))
check(".env not shipped", not (ROOT / ".env").exists())

width = max(len(n) for n, _, _ in results)
failed = 0
for name, ok, detail in results:
    print(f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}  {'' if ok else detail}")
    failed += (not ok)
print(f"\n{len(results) - failed} passed, {failed} failed")
sys.exit(1 if failed else 0)
