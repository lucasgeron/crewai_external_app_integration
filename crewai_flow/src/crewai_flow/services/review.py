"""Reads the answer of the human review. Plain Python, no CrewAI."""

import re

from pydantic import ValidationError

from crewai_flow.types import ContactsSelection


def parse_review_response(feedback: str, valid_refs: list[int]) -> list[int]:
    """Turn the text of the review into the `ref` of the contacts to import.

    The normal answer is the JSON of `ContactsSelection` (what our frontend sends). A person may also
    answer in free text, for example in the AMP dashboard or by e-mail: "all" selects every contact,
    and any other text selects the refs written in it ("1, 3"). Text with no ref selects nothing.

    Unknown refs are ignored. The result follows the order of `valid_refs`.

    `valid_refs`: is injected here instead of read from self.state.contacts, to avoid unnecessary payloads.
    """
    try:
        # model_validate_json(feedback) parses the text as JSON, if the JSON contains
        # {"selected_refs": [1, 3]}, then the result becomes [1, 3].
        wanted = ContactsSelection.model_validate_json(feedback).selected_refs
    except ValidationError:  # fallback if the text is not JSON
        if feedback.strip().lower() == "all":
            wanted = valid_refs
        else:
            # find all numbers in the text, e.g: "1, 3" becomes [1, 3]
            wanted = [int(number) for number in re.findall(r"\d+", feedback)]
    return [ref for ref in valid_refs if ref in wanted]
