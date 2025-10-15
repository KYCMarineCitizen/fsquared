from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ContactRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    site: str = Field(..., description="Public domain that originated the request.")
    company: str = Field(..., max_length=120)
    name: str = Field(..., max_length=120)
    email: EmailStr = Field(..., description="User-supplied reply-to address.")
    message: str = Field(..., max_length=4000)
    recaptcha_token: str | None = Field(default=None, alias="recaptchaToken")


class ContactResponse(BaseModel):
    success: bool
    message: str
