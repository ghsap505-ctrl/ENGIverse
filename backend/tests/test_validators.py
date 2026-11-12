import pytest

from app.core.validators import mask_database_url, parse_cors_origins, validate_database_url

OK = "postgresql+psycopg://user:s3cret-pass@db:5432/engiverse"


def test_valid_url_passes():
    validate_database_url(OK, production=False)


@pytest.mark.parametrize("url", [
    "postgresql://u:p@h:5432/d",             # wrong driver scheme
    "postgresql+psycopg://u@h:5432/d",       # no password
    "postgresql+psycopg://u:@h:5432/d",      # empty password
    "postgresql+psycopg://:p@h:5432/d",      # no user
    "postgresql+psycopg://u:p@:5432/d",      # no host
    "postgresql+psycopg://u:p@h:5432",       # no db name
    "postgresql+psycopg://u:p@h:99999999/d", # bad port
    "",
])
def test_invalid_urls_rejected(url):
    with pytest.raises(ValueError):
        validate_database_url(url, production=False)


@pytest.mark.parametrize("pw", ["change-this-password", "changeme123456789012", "password", "short-pw"])
def test_production_rejects_weak_or_placeholder_password(pw):
    with pytest.raises(ValueError):
        validate_database_url(f"postgresql+psycopg://u:{pw}@h:5432/d", production=True)


def test_production_accepts_strong_password():
    validate_database_url("postgresql+psycopg://u:Zx9kQ2mV7pLr4Tn8Wd3Y@h:5432/d", production=True)


def test_error_messages_never_contain_password():
    with pytest.raises(ValueError) as exc:
        validate_database_url("postgresql://u:topsecretvalue@h:5432/d", production=False)
    assert "topsecretvalue" not in str(exc.value)


def test_mask_hides_password():
    masked = mask_database_url(OK)
    assert "s3cret-pass" not in masked and "***" in masked and "db:5432" in masked


def test_cors_parsing():
    assert parse_cors_origins("") == []
    assert parse_cors_origins(" http://a.com , https://b.com:8443,http://a.com ") == [
        "http://a.com", "https://b.com:8443"]


@pytest.mark.parametrize("raw", ["*", "https://*.example.com", "http://a.com/", "http://a.com/path",
                                 "ftp://a.com", "a.com"])
def test_cors_rejects_bad_origins(raw):
    with pytest.raises(ValueError):
        parse_cors_origins(raw)
