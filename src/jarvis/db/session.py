"""SQLite engine factory with JARVIS connection pragmas (Backend_Schema §2)."""
from pathlib import Path
from typing import Any

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlmodel import SQLModel, create_engine

DEFAULT_DB_PATH = Path("data") / "jarvis.db"


def _apply_pragmas(dbapi_connection: Any, connection_record: Any) -> None:
    """Apply required PRAGMAs to every new connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()


def make_engine(db_path: str | Path = DEFAULT_DB_PATH) -> Engine:
    """Create a SQLite engine at `db_path` with WAL, FK enforcement, busy timeout."""
    if str(db_path) == ":memory:":
        url = "sqlite:///:memory:"
    else:
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        url = f"sqlite:///{path.as_posix()}"
    engine = create_engine(url, connect_args={"check_same_thread": False})
    event.listens_for(engine, "connect")(_apply_pragmas)
    
    from sqlalchemy import text
    with engine.connect() as conn:
        conn.execute(text("PRAGMA journal_mode=WAL"))
    return engine


def init_db(engine: Engine) -> None:
    """Create all tables and indexes defined in `jarvis.db.models`."""
    from jarvis.db import models  # noqa: F401  (register table metadata)

    SQLModel.metadata.create_all(engine)
