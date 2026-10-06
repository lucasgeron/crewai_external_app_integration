"""What the reviewer sends back."""

from pydantic import BaseModel


class ContactsSelection(BaseModel):
    """The answer of the human review: which contacts to import.

    It travels as JSON text in the `feedback` of the review (the AMP review API only carries a
    string), for example: {"selected_refs": [1, 3]}.
    """

    # The `ref` of the contacts to import. The others are discarded.
    selected_refs: list[int] = []
