"""Shared dependencies that routes can ask FastAPI to provide."""

from collections.abc import Iterator

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import Contact
from app.repositories import contact as contact_repo


def get_db() -> Iterator[Session]:
    """Give a database session to a route, then close it when the request ends."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_contact_or_404(contact_id: int, db: Session = Depends(get_db)) -> Contact:
    """Find a contact by id. Return a 404 error if it does not exist."""
    contact = contact_repo.get(db, contact_id)
    if contact is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Contact not found")
    return contact
