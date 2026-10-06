"""Kickoff model: the `kickoffs` table in SQLite. One row has everything about a run.

A kickoff is one run of the import flow (CrewAI AMP calls its id the `kickoff_id`). The flow host
has no "list my runs" endpoint, so we keep the runs here. The host keeps them up to date with webhooks: the
start and the end of the run and the review (both webhooks are in api/webhook.py).

The row also keeps what the flow told us (the generated contacts, the selection and the result of the
import) and the human review it asked for (see the webhook in api/webhook.py), so the import
page can list everything, even after a restart.
"""

from datetime import datetime

from sqlalchemy import JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, UTCDateTime


class Kickoff(Base):
    """One run of the import flow."""

    __tablename__ = "kickoffs"

    # The id created by the flow host. It is unique by nature, so it is the primary key.
    kickoff_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    # Where the run is, with the same names as `outcome` in the state of the flow: "initialized" when it
    # starts, "generated" when it waits for the reviewer (the webhook), then "imported" or "failed".
    outcome: Mapped[str] = mapped_column(String(16), default="initialized")
    # Why the flow failed (only when `outcome` is "failed").
    error: Mapped[str | None] = mapped_column(Text)
    # The contacts the flow generated, and the `ref` of the ones the reviewer selected to import.
    # They arrive with the webhook (the state of the flow at the pause) and again when the flow finishes.
    contacts: Mapped[list | None] = mapped_column(JSON)
    selected_refs: Mapped[list | None] = mapped_column(JSON)
    # The human review, filled by the webhook: the id of the request and the flow step that asked, and
    # where to send the answer (it can carry a secret, so the API never returns it). `answered_at` is
    # set when the answer is sent.
    request_id: Mapped[str | None] = mapped_column(String(128))
    method_name: Mapped[str | None] = mapped_column(String(255))
    callback_url: Mapped[str | None] = mapped_column(Text)
    answered_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime, server_default=func.now()
    )
