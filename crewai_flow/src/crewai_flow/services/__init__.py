"""Business logic of the flow: plain Python, no HTTP and no CrewAI."""

from crewai_flow.services.contact_generator import generate_contacts
from crewai_flow.services.review import parse_review_response

__all__ = ["generate_contacts", "parse_review_response"]
