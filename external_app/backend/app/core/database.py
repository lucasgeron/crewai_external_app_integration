"""Database setup: connects the app to SQLite using SQLAlchemy.

SQLite is a database in a single file (by default `data/external_app.db`, inside this project). It
needs no server: the file is created by `Base.metadata.create_all` the first time the app starts, so it
is not versioned (see .gitignore). To start from zero, stop the app and delete the file.
"""

from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import DateTime, create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.types import TypeDecorator

from app.core.config import get_settings

url = make_url(get_settings().database_url)
if url.database:
    # SQLite does not create the folder of the file by itself.
    Path(url.database).parent.mkdir(parents=True, exist_ok=True)

# The engine is the connection to the database. FastAPI runs each request in its own thread, and
# SQLite refuses to share a connection between threads by default, so we allow it
# (each request still uses its own session).
engine = create_engine(get_settings().database_url, connect_args={"check_same_thread": False})

# A session is a short conversation with the database. We create one per request.
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class UTCDateTime(TypeDecorator):
    """A date and time that always comes back in UTC.

    SQLite has no time zone: it stores the time (CURRENT_TIMESTAMP is UTC) and gives it back without
    one. Without this the API would send "2026-10-06T14:27:19" and the browser would read it as
    local time. With it, the API sends "...Z" and the browser shows the right hour.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect):
        return value.astimezone(timezone.utc) if value is not None else None

    def process_result_value(self, value: datetime | None, dialect):
        return value.replace(tzinfo=timezone.utc) if value is not None else None


class Base(DeclarativeBase):
    """All database models inherit from this class."""
