"""Creates fake contacts with plain Python. No LLM is needed for this step."""

import random
import re
import unicodedata

from faker import Faker

from crewai_flow.config import get_settings

_fake = Faker("pt_BR")

def generate_contacts(count: int) -> list[dict]:
    """Return `count` contacts shaped like the backend's ContactCreate schema."""
    contacts = []
    names = []
    for ref in range(1, count + 1):
        first = _fake.first_name()
        last = _fake.last_name()
        names.append((first, last))
        # Name, email and social links all come from the same first/last name.
        handle = f"{_slug(first)}.{_slug(last)}"
        # A random number keeps the emails unique (the API rejects repeated emails).
        unique = random.randint(1000, 9999)

        contacts.append(
            {
                "ref": ref,
                "name": f"{first} {last}",
                "email": f"{handle}{unique}@example.com",
                # Social links are optional, so some contacts will not have them.
                "instagram": f"@{handle}" if random.random() < 0.7 else None,
                "facebook": f"facebook.com/{handle}" if random.random() < 0.5 else None,
                "linkedin": (
                    f"linkedin.com/in/{handle}" if random.random() < 0.8 else None
                ),
                "website": (
                    f"https://{handle}.example.com" if random.random() < 0.4 else None
                ),
            }
        )

    # On purpose: the last contact is the first one again, with the same email and a
    # middle name added (needs 2+ contacts).
    # The API only accepts unique emails, so if you import both, the second one fails with 409.
    # This lets you see how a failure looks in the log and in the UI.
    if get_settings().flow_include_duplicate_email and count >= 2:
        # Same person again: the first contact's name with an extra middle name.
        first, last = names[0]
        contacts[-1]["name"] = f"{first} {_fake.first_name()} {last}"
        contacts[-1]["email"] = contacts[0]["email"]

    return contacts


def _slug(text: str) -> str:
    """Lowercase ASCII-only version of `text` ("João da Silva" -> "joaodasilva")."""
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", ascii_text.lower())
