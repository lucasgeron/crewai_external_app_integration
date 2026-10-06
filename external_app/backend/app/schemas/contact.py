"""Contact schemas: the shape of the JSON the API receives and returns.

Models describe database tables. Schemas describe the JSON that clients use.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ContactBase(BaseModel):
    """Fields shared by all contact schemas."""

    name: str = Field(description="Full name of the contact", examples=["Ana Silva"])
    email: EmailStr = Field(
        description="Email address. Must be valid and unique.",
        examples=["ana@example.com"],
    )
    instagram: str | None = Field(
        default=None, description="Instagram profile", examples=["@ana.silva"]
    )
    facebook: str | None = Field(
        default=None,
        description="Facebook profile",
        examples=["facebook.com/ana.silva"],
    )
    linkedin: str | None = Field(
        default=None,
        description="LinkedIn profile",
        examples=["linkedin.com/in/ana-silva"],
    )
    website: str | None = Field(
        default=None, description="Personal website", examples=["https://ana.dev"]
    )


class ContactCreate(ContactBase):
    """Data needed to create a contact. Only name and email are required."""


class ContactUpdate(BaseModel):
    """Data to update a contact. Send only the fields you want to change."""

    name: str | None = None
    email: EmailStr | None = None
    instagram: str | None = None
    facebook: str | None = None
    linkedin: str | None = None
    website: str | None = None


class ContactRead(ContactBase):
    """Contact data returned by the API."""

    # from_attributes lets Pydantic read data straight from a database model.
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
