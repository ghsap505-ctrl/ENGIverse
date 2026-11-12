# syntax=docker/dockerfile:1
# Targets:  dev  (reload, test deps, source bind-mountable)
#           prod (runtime deps only, non-root, no reload, healthcheck)
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
RUN groupadd --system --gid 10001 app \
 && useradd  --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app

# ---------------------------------------------------------------- dev
FROM base AS dev
COPY requirements.txt requirements-dev.txt ./
RUN pip install -r requirements-dev.txt
COPY --chown=app:app . .
USER app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ---------------------------------------------------------------- prod
FROM base AS prod
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY --chown=app:app app ./app
COPY --chown=app:app alembic ./alembic
COPY --chown=app:app alembic.ini ./
USER app
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=4s --start-period=15s --retries=5 \
  CMD ["python", "-c", "import sys,urllib.request as u; sys.exit(0 if u.urlopen('http://127.0.0.1:8000/api/v1/health', timeout=3).status == 200 else 1)"]
# One process per container; scale horizontally with more replicas (stateless API).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--no-server-header"]
