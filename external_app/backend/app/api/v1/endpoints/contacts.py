"""HTTP routes for contacts. They call the repository layer and return HTTP errors."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_contact_or_404, get_db
from app.core import broker
from app.repositories import contact as repo
from app.repositories import kickoff as kickoff_repo
from app.models import Contact
from app.schemas.contact import ContactCreate, ContactRead, ContactUpdate

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.post(
    "",
    response_model=ContactRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a contact",
)
def create_contact(payload: ContactCreate, db: Session = Depends(get_db)):
    """Create a new contact. Returns 409 if the email already exists.

    The import flow creates its contacts here, one by one. So this is also where the backend learns, contact by
    contact, how an import is going: `track_import` passes the result to the run, and the page shows it live.
    """
    try:
        contact = save_new_contact(db, payload)
    except HTTPException as error:
        track_import(db, payload.email, error=f"{error.status_code}: {error.detail}")
        raise
    track_import(db, payload.email, external_app_id=contact.id)
    return contact


@router.get("", response_model=list[ContactRead], summary="List contacts")
def list_contacts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List contacts ordered by id.

    - **skip**: how many contacts to jump over (used for pages)
    - **limit**: maximum number of contacts to return
    """
    return repo.list_all(db, skip=skip, limit=limit)


@router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Destroy all contacts",
)
def destroy_all_contacts(db: Session = Depends(get_db)):
    """Delete ALL contacts and restart the ids from 1. This cannot be undone."""
    repo.delete_all(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{contact_id}", response_model=ContactRead, summary="Get one contact")
def get_contact(contact: Contact = Depends(get_contact_or_404)):
    """Get a single contact by id. Returns 404 if it does not exist."""
    return contact


@router.patch("/{contact_id}", response_model=ContactRead, summary="Update a contact")
def update_contact(
    payload: ContactUpdate,
    contact: Contact = Depends(get_contact_or_404),
    db: Session = Depends(get_db),
):
    """Update only the fields that were sent.

    Returns 404 if the contact does not exist, or 409 if the new email is taken.
    """
    if payload.email is not None:
        ensure_email_is_free(db, payload.email, current_id=contact.id)
    try:
        return repo.update(db, contact, payload)
    except IntegrityError:
        db.rollback()
        raise email_taken()


@router.delete(
    "/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a contact",
)
def delete_contact(
    contact: Contact = Depends(get_contact_or_404), db: Session = Depends(get_db)
):
    """Delete a contact. Returns 404 if it does not exist."""
    repo.delete(db, contact)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def save_new_contact(db: Session, payload: ContactCreate) -> Contact:
    """Save the contact, or raise a 409 if the email is taken."""
    ensure_email_is_free(db, payload.email)
    try:
        return repo.create(db, payload)
    except IntegrityError:
        # Two requests with the same email can pass the check above at the same time.
        # The unique index in the database is the final safety net.
        db.rollback()
        raise email_taken()


def track_import(db: Session, email: str, external_app_id: int | None = None, error: str | None = None) -> None:
    """If the contact is one of a run being imported, save its result in the run and tell the open pages."""
    if kickoff_repo.record_import(db, email, external_app_id, error):
        broker.notify()


def email_taken() -> HTTPException:
    """Build the 409 error used when the email is already in use."""
    return HTTPException(status.HTTP_409_CONFLICT, "Email already exists")


def ensure_email_is_free(db: Session, email: str, current_id: int | None = None) -> None:
    """Return a 409 error if another contact already uses this email."""
    other = repo.get_by_email(db, email)
    if other is not None and other.id != current_id:
        raise email_taken()
