"""Import every model here so SQLAlchemy knows all tables when creating them."""

from app.models.contact import Contact
from app.models.kickoff import Kickoff

__all__ = ["Contact", "Kickoff"]
