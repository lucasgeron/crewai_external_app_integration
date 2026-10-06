"""Contact model: the `contacts` table in SQLite."""

from datetime import datetime

from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, UTCDateTime


class Contact(Base):
    """A person we keep in our contact list."""

    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    # Email must be unique: two contacts cannot share the same email.
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    # Social links are optional, so they can be empty (None).
    instagram: Mapped[str | None] = mapped_column(String(255))
    facebook: Mapped[str | None] = mapped_column(String(255))
    linkedin: Mapped[str | None] = mapped_column(String(255))
    website: Mapped[str | None] = mapped_column(String(255))
    # The database fills created_at when the row is first saved.
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime, server_default=func.now()
    )
    # updated_at is set on creation and changes again on every update.
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime, server_default=func.now(), onupdate=func.now()
    )
