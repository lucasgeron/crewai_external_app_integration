from typing import Literal
from crewai_flow.config.settings import get_settings
from pydantic import BaseModel, Field
from crewai_flow.types.contacts import GeneratedContact


class ImportContactsState(BaseModel):
    """The current state of the flow. CrewAI saves it for us when the flow pauses.

    CrewAI fills the state fields from the kickoff `inputs` (only `count` is expected). The flow
    returns this state when it ends.

    A host that sends a review webhook (CrewAI AMP) includes this state in it, so everything the
    reviewer needs to see (the contacts) must be here.
    """

    count: int = Field(
        default=get_settings().flow_default_count,
        description="How many contacts to generate (the input of the kickoff)",
    )
    contacts: list[GeneratedContact] = Field(
        default_factory=list, description="The generated contacts"
    )
    selected_refs: list[int] = Field(
        default_factory=list,
        description="The `ref` of each contact the reviewer chose to import",
    )
    outcome: Literal["initialized", "generated", "imported", "failed"] = Field(
        default="initialized",
        description="initialized until the flow ends, then imported (the reviewer chose the contacts) or failed",
    )
    error: str = Field(
        default="",
        description='Why the flow failed. Empty unless `outcome` is "failed"',
    )
