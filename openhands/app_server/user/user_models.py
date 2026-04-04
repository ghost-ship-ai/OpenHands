from enum import Enum

from pydantic import BaseModel

from openhands.integrations.provider import PROVIDER_TOKEN_TYPE
from openhands.storage.data_models.settings import Settings


class UserInfo(Settings):
    """Model for user settings including the current user id."""

    id: str | None = None


class SandboxGroupingStrategy(str, Enum):
    """Strategy for grouping conversations within sandboxes."""

    NO_GROUPING = 'NO_GROUPING'  # Default - each conversation gets its own sandbox
    GROUP_BY_NEWEST = 'GROUP_BY_NEWEST'  # Add to the most recently created sandbox
    LEAST_RECENTLY_USED = (
        'LEAST_RECENTLY_USED'  # Add to the least recently used sandbox
    )
    FEWEST_CONVERSATIONS = (
        'FEWEST_CONVERSATIONS'  # Add to sandbox with fewest conversations
    )
    ADD_TO_ANY = 'ADD_TO_ANY'  # Add to any available sandbox (first found)


class UserMeta(BaseModel):
    """Model for user metadata from git provider.

    This model has no dependencies and is used by various modules.
    """

    id: str
    login: str
    avatar_url: str
    company: str | None = None
    name: str | None = None
    email: str | None = None


class ProviderTokenPage:
    items: list[PROVIDER_TOKEN_TYPE]
    next_page_id: str | None = None
