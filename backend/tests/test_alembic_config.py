import py_compile
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent


def test_env_py_compiles():
    py_compile.compile(str(BACKEND / "alembic" / "env.py"), doraise=True)


def test_alembic_script_directory_loads():
    pytest.importorskip("alembic")
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    cfg = Config(str(BACKEND / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND / "alembic"))
    script = ScriptDirectory.from_config(cfg)
    assert script.get_heads() == []  # 0.1.1 ships no migrations by design


def test_alembic_ini_holds_no_credentials():
    text = (BACKEND / "alembic.ini").read_text()
    lowered = text.lower()
    assert "postgresql" not in lowered and "password" not in lowered
