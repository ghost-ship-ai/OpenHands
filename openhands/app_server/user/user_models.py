from pydantic import BaseModel

from openhands.integrations.provider import PROVIDER_TOKEN_TYPE
from openhands.storage.data_models.settings import Settings


class UserMeta(BaseModel):
    """Model for user metadata from git provider."""

    id: str
    login: str
    avatar_url: str
    company: str | None = None
    name: str | None = None
    email: str | None = None


class UserInfo(Settings):
    """Model for user settings including the current user id."""

    id: str | None = None


class ProviderTokenPage:
    items: list[PROVIDER_TOKEN_TYPE]
    next_page_id: str | None = None
