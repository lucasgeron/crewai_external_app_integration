"""Kickoff schemas: the JSON used to save, list and answer the runs of the import flow."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# Where a run is (the same names as `outcome` in the state of the flow).
Outcome = Literal["initialized", "generated", "imported", "failed"]


class KickoffCreate(BaseModel):
    """Body to save a run."""

    kickoff_id: str = Field(
        min_length=1,
        max_length=64,
        description="The id returned by the flow's /kickoff",
        examples=["57b7406d-fc03-471e-a97b-838671ad8a96"],
    )


class KickoffRead(BaseModel):
    """A saved run. The `callback_url` of the review is never returned."""

    model_config = ConfigDict(from_attributes=True)

    kickoff_id: str
    outcome: Outcome
    error: str | None
    contacts: list[dict[str, Any]] | None
    selected_refs: list[int] | None
    # The human review (filled when the flow host sends the webhook): `answered_at` says if it was answered.
    request_id: str | None
    method_name: str | None
    answered_at: datetime | None
    created_at: datetime


class ReviewAnswer(BaseModel):
    """The human's answer. For the import flow it is JSON text: {"selected_refs": [1, 3]}."""

    feedback: str = Field(description="The answer sent to the flow")
