import datetime

from pydantic import BaseModel


class WorkspacePublic(BaseModel):
    """Workspace fields safe to expose over the API (excludes owner identity)."""

    id: int
    name: str
    slug: str
    created_at: datetime.datetime
    can_edit: bool


class FilePublic(BaseModel):
    id: int
    display_name: str
    original_filename: str
    status: str
    uploaded_at: datetime.datetime
    url: str


class UploadPublic(BaseModel):
    filename: str
    display_name: str
    original_filename: str
    size: int


class ConversationPublic(BaseModel):
    id: int
    title: str
    created_at: datetime.datetime


class ExchangePublic(BaseModel):
    id: int
    question: str
    answer: str | None
    sources: list[dict[str, str]] | None
    status: str
    created_at: datetime.datetime


class ConversationDetail(ConversationPublic):
    exchanges: list[ExchangePublic]


class AskResponse(BaseModel):
    conversation_id: int
    title: str
    answer: str
    sources: list[dict[str, str]]


class TokenResponse(BaseModel):
    token: str
    email: str


class HealthStatus(BaseModel):
    status: str
