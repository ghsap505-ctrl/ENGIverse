"""Domain modules (modular monolith).

Each domain (identity, courses, tutor, ...) will live in app/modules/<name>/
with its own models, schemas, service and router, exposing only a router to
app/api/v1/router.py. Modules must not import each other's internals.
"""
