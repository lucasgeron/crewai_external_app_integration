"""Contact data: what the flow generates."""

from typing import Literal

from pydantic import BaseModel


class GeneratedContact(BaseModel):
    """A contact created by the flow. The fields match the backend's ContactCreate schema."""

    ref: int
    name: str
    email: str
    instagram: str | None = None
    facebook: str | None = None
    linkedin: str | None = None
    website: str | None = None
    import_status: Literal["pending", "imported", "failed"] = "pending"
    """Result of sending the contact to the contacts API. `pending` until the flow tries to import it."""
    external_app_id: int | None = None
    """The `id` of the contact in the contacts API. Only set when `import_status` is "imported"."""
    import_error: str | None = None
    """Why the import failed. Only set when `import_status` is "failed"."""
