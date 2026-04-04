from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, SecretStr


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


class UserInfo(BaseModel):
    """Model for user settings including the current user id."""

    id: str | None = None
    language: str | None = None
    llm_api_key: SecretStr | None = None
    llm_model: str | None = None
    llm_base_url: str | None = None
    security_analyzer: str | None = None
    confirmation_mode: bool | None = None
    disabled_skills: list[str] | None = None
    condenser_max_size: int | None = None
    git_user_name: str | None = None
    git_user_email: str | None = None
    sandbox_grouping_strategy: SandboxGroupingStrategy = (
        SandboxGroupingStrategy.NO_GROUPING
    )
    mcp_config: Any | None = None
    search_api_key: SecretStr | None = None
    model_config = {'extra': 'allow'}


class ProviderTokenPage:
    items: list[Any]
    next_page_id: str | None = None
