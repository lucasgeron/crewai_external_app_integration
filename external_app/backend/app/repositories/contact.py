"""Database operations for contacts (Create, Read, Update, Delete).

This layer only talks to the database. It knows nothing about HTTP.
"""

from sqlalchemy import delete as sql_delete, select
from sqlalchemy.orm import Session

from app.models import Contact
from app.schemas.contact import ContactCreate, ContactUpdate


def get(db: Session, contact_id: int) -> Contact | None:
    """Return one contact by id, or None if it does not exist."""
    return db.get(Contact, contact_id)


def get_by_email(db: Session, email: str) -> Contact | None:
    """Return one contact by email, or None if it does not exist."""
    return db.scalar(select(Contact).where(Contact.email == email))


def list_all(db: Session, skip: int = 0, limit: int = 100) -> list[Contact]:
    """Return contacts ordered by id, with simple paging."""
    stmt = select(Contact).order_by(Contact.id).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


def create(db: Session, data: ContactCreate) -> Contact:
    """Save a new contact and return it."""
    contact = Contact(**data.model_dump())
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


def update(db: Session, contact: Contact, data: ContactUpdate) -> Contact:
    """Change only the fields that were sent, and return the contact."""
    # exclude_unset keeps only the fields the client really sent.
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(contact, field, value)
    db.commit()
    db.refresh(contact)
    return contact


def delete(db: Session, contact: Contact) -> None:
    """Remove a contact from the database."""
    db.delete(contact)
    db.commit()


def delete_all(db: Session) -> None:
    """Remove every contact. SQLite reuses ids, so the next contact gets the id 1 again."""
    db.execute(sql_delete(Contact))
    db.commit()
