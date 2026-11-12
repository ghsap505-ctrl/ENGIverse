"""Pure (stdlib-only) validation helpers used by the settings model.

Kept free of third-party imports so they can be unit-tested and reasoned about
in isolation. Error messages NEVER include the offending value, because the
value may be a credential.
"""
import re
from urllib.parse import urlsplit, unquote

REQUIRED_DB_SCHEME = "postgresql+psycopg"
MIN_PRODUCTION_DB_PASSWORD_LENGTH = 16
PLACEHOLDER_PASSWORDS = frozenset(
    {"change-this-password", "changeme", "change-me", "password", "postgres",
     "secret", "admin", "engiverse", "example", "test"}
)
_ORIGIN_RE = re.compile(r"^https?://[A-Za-z0-9.\-]+(:\d{1,5})?$|^https?://\[[0-9a-fA-F:]+\](:\d{1,5})?$")


def validate_database_url(url: str, *, production: bool) -> None:
    """Raise ValueError if the URL is unusable. Never echoes the URL."""
    parts = urlsplit(url)
    if parts.scheme != REQUIRED_DB_SCHEME:
        raise ValueError(f"DATABASE_URL must use the '{REQUIRED_DB_SCHEME}' scheme")
    if not parts.hostname:
        raise ValueError("DATABASE_URL must include a host")
    try:
        parts.port  # noqa: B018  (property access validates the port)
    except ValueError:
        raise ValueError("DATABASE_URL has an invalid port") from None
    if not parts.username:
        raise ValueError("DATABASE_URL must include a database user")
    password = unquote(parts.password or "")
    if not password:
        raise ValueError("DATABASE_URL must include an explicit database password")
    if not parts.path.strip("/"):
        raise ValueError("DATABASE_URL must include a database name")
    if production:
        lowered = password.lower()
        if lowered in PLACEHOLDER_PASSWORDS or lowered.startswith("change"):
            raise ValueError("DATABASE_URL uses a placeholder password; set a real secret")
        if len(password) < MIN_PRODUCTION_DB_PASSWORD_LENGTH:
            raise ValueError(
                f"Database password must be at least {MIN_PRODUCTION_DB_PASSWORD_LENGTH} "
                "characters in production"
            )


def mask_database_url(url: str) -> str:
    """Return the URL with the password replaced by '***' (safe to log)."""
    parts = urlsplit(url)
    if parts.password is None:
        return url
    host = parts.hostname or ""
    if ":" in host:  # IPv6 literal
        host = f"[{host}]"
    netloc = f"{parts.username}:***@{host}"
    if parts.port:
        netloc += f":{parts.port}"
    return parts._replace(netloc=netloc).geturl()


def parse_cors_origins(raw: str) -> list[str]:
    """Parse a comma-separated origin list. Wildcards and paths are rejected."""
    origins: list[str] = []
    for item in raw.split(","):
        origin = item.strip()
        if not origin:
            continue
        if origin == "*" or "*" in origin:
            raise ValueError("CORS_ORIGINS must not contain wildcards (credentials are enabled)")
        if not _ORIGIN_RE.match(origin):
            raise ValueError(
                "CORS_ORIGINS entries must be bare origins like https://example.com "
                "(scheme + host [+ port], no path or trailing slash)"
            )
        if origin not in origins:
            origins.append(origin)
    return origins
