"""Request/response shapes. /chat must match the grading format EXACTLY."""
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=200)
    thread_id: str = Field(min_length=1, max_length=200)
    message: str = Field(max_length=10_000)  # longer than our limit, so the guard can reply nicely


def chat_response(reply: str, tool_calls: list | None = None, tokens_in: int = 0, tokens_out: int = 0) -> dict:
    """{"reply": "...", "tool_calls": [], "tokens": {"in": 0, "out": 0}}

    A dict (not a Pydantic model) because "in" is a Python keyword and can't be a field name.
    """
    return {"reply": reply, "tool_calls": tool_calls or [], "tokens": {"in": tokens_in, "out": tokens_out}}


class LeadStageUpdate(BaseModel):
    stage: str = Field(pattern="^(new|qualified|visit_booked|closed)$")


class NewListing(BaseModel):
    type: str = Field(pattern="^(property|car)$")
    title: str = Field(min_length=3, max_length=200)
    city: str = Field(min_length=2, max_length=100)
    area: str = Field(min_length=2, max_length=100)
    size_label: str | None = None
    size_marla: float | None = None
    price_pkr: int = Field(gt=0)
    purpose: str = Field(default="sale", pattern="^(sale|rent)$")
    bedrooms: int | None = None
    description: str | None = None
    image_url: str | None = None
