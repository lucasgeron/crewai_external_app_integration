"""Client of the External App contacts API. No retry: one request, it worked or it did not."""

import httpx

from crewai_flow.config import get_settings
from crewai_flow.types import GeneratedContact

REQUEST_TIMEOUT_SECONDS = 10
# `ref` only exists inside the flow, the API does not know it.
_API_FIELDS = ("name", "email", "instagram", "facebook", "linkedin", "website")


def create_contact(contact: GeneratedContact) -> int:
    """Send one contact to `POST /contacts` and return the `id` the API gave it.

    Raises `ContactsApiError` when the API refuses it (for example 409, the email already exists) or
    when it can not be reached.
    """
    url = f"{get_settings().external_app_api_url.rstrip('/')}/api/v1/contacts"
    payload = contact.model_dump(include=set(_API_FIELDS), exclude_none=True)
    try:
        response = httpx.post(url, json=payload, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.json()["id"]
    except httpx.HTTPStatusError as error:
        raise ContactsApiError(f"{error.response.status_code}: {_detail(error.response)}") from error
    except (httpx.HTTPError, ValueError, KeyError) as error:
        raise ContactsApiError(f"request failed: {error!r}") from error


class ContactsApiError(Exception):
    """The contacts API did not accept the contact. The message is safe to show to the reviewer."""


def _detail(response: httpx.Response) -> str:
    """The `detail` of a FastAPI error, or the raw text when the body is not that."""
    try:
        return str(response.json()["detail"])
    except (ValueError, KeyError, TypeError):
        return response.text[:200]
