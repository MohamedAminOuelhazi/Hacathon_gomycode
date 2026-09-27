from typing import Literal

from pydantic import BaseModel, Field


class ChatHistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4_000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=10_000)
    history: list[ChatHistoryMessage] = Field(default_factory=list, max_length=12)


class ToolEvent(BaseModel):
    tool: str
    status: str
    duration_ms: float
    summary: str


class ChatResponse(BaseModel):
    answer: str
    tool_events: list[ToolEvent]
    visualizations: list[dict]
