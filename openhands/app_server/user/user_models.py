from __future__ import annotations

from typing import Any

from pydantic import BaseModel, SecretStr

# Import UserMeta from standalone module to avoid circular import
from openhands.app_server.user.user_meta import UserMeta
from openhands.storage.data_models.settings import SandboxGroupingStrategy


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


# Re-export UserMeta for backward compatibility
__all__ = ['UserMeta', 'UserInfo', 'ProviderTokenPage']
