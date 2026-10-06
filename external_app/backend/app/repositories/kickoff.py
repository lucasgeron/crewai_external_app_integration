"""Database operations for kickoffs (the runs of the flow).

This layer only talks to the database. It knows nothing about HTTP.
"""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete as sql_delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Kickoff


def get(db: Session, kickoff_id: str) -> Kickoff | None:
    """Return one kickoff by id, or None if it does not exist."""
    return db.get(Kickoff, kickoff_id)


def list_all(db: Session) -> list[Kickoff]:
    """Return every kickoff, newest first."""
    return list(db.scalars(select(Kickoff).order_by(Kickoff.created_at.desc())).all())


def get_or_create(db: Session, kickoff_id: str) -> Kickoff:
    """Return the kickoff, saving it first if it is new.

    Two requests can ask for the same new id at the same time: the frontend saving the run and the webhook
    of its review (which can arrive first). The primary key lets only one of them insert it.
    """
    kickoff = db.get(Kickoff, kickoff_id)
    if kickoff is None:
        try:
            kickoff = Kickoff(kickoff_id=kickoff_id)
            db.add(kickoff)
            db.commit()
        except IntegrityError:
            db.rollback()
            kickoff = db.get(Kickoff, kickoff_id)
    db.refresh(kickoff)
    return kickoff


def update(db: Session, kickoff: Kickoff, changes: dict) -> Kickoff:
    """Change only the fields that were sent, and return the kickoff."""
    for field, value in changes.items():
        setattr(kickoff, field, value)
    db.commit()
    db.refresh(kickoff)
    return kickoff


def save_review(
    db: Session, kickoff: Kickoff, request_id: str, method_name: str, callback_url: str, state: dict
) -> Kickoff:
    """Keep a review request and the state of the flow at the pause (what the reviewer has to see)."""
    return update(
        db,
        kickoff,
        {
            "request_id": request_id,
            "method_name": method_name,
            "callback_url": callback_url,
            "answered_at": None,
            "outcome": state.get("outcome") or "generated",
            "error": state.get("error") or None,
            "contacts": state.get("contacts"),
            "selected_refs": state.get("selected_refs"),
        },
    )


def finish(db: Session, kickoff: Kickoff, state: dict) -> Kickoff:
    """Save the final state of the flow: how it ended, why it failed, and the result of each contact."""
    return update(
        db,
        kickoff,
        {
            "outcome": state.get("outcome") or "imported",
            "error": state.get("error") or None,
            "contacts": state.get("contacts"),
            "selected_refs": state.get("selected_refs"),
        },
    )


def mark_answered(db: Session, kickoff: Kickoff, selected_refs: list[int] | None) -> Kickoff:
    """Remember that the answer was sent, and which contacts it selected (when we can read them)."""
    changes: dict[str, Any] = {"answered_at": datetime.now(timezone.utc)}
    if selected_refs is not None:
        changes["selected_refs"] = selected_refs
    return update(db, kickoff, changes)


def record_import(db: Session, email: str, external_app_id: int | None = None, error: str | None = None) -> bool:
    """Note what happened to a contact the flow just sent to `POST /contacts`. True if it belonged to a run.

    The flow imports the selected contacts one by one, and does not say which run each request is for. But the
    run is waiting for its import (it was answered and has not finished), and the contact is one of the selected
    ones that is still `pending`, with the same email. That is enough to find it.
    """
    answered = select(Kickoff).where(Kickoff.outcome == "generated", Kickoff.answered_at.is_not(None))
    for kickoff in db.scalars(answered):
        # `contacts` is a JSON column: SQLAlchemy only sees a change when the whole list is replaced by a new one.
        contacts = [dict(contact) for contact in kickoff.contacts or []]
        contact = next(
            (
                item
                for item in contacts
                if item["email"] == email
                and item["import_status"] == "pending"
                and item["ref"] in (kickoff.selected_refs or [])
            ),
            None,
        )
        if contact is not None:
            contact.update(
                import_status="failed" if error else "imported",
                external_app_id=external_app_id,
                import_error=error,
            )
            update(db, kickoff, {"contacts": contacts})
            return True
    return False


def delete(db: Session, kickoff: Kickoff) -> None:
    """Remove a kickoff from the database."""
    db.delete(kickoff)
    db.commit()


def delete_all(db: Session) -> None:
    """Remove every kickoff."""
    db.execute(sql_delete(Kickoff))
    db.commit()
