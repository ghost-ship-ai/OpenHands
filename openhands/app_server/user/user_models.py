from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

# Import UserMeta from standalone module to avoid circular import
from openhands.app_server.user.user_meta import UserMeta

if TYPE_CHECKING:
    from openhands.storage.data_models.settings import Settings
    from openhands.integrations.provider import PROVIDER_TOKEN_TYPE


# Lazy import for Settings to break circular dependency
def _get_settings_class():
    from openhands.storage.data_models.settings import Settings
    return Settings


class UserInfo(BaseModel):
    """Model for user settings including the current user id."""

    id: str | None = None
    language: str | None = None
    llm_api_key: str | None = None
    # Add other fields from Settings that are needed - use dict for flexibility
    model_config = {'extra': 'allow'}


class ProviderTokenPage:
    items: list[Any]
    next_page_id: str | None = None


# Re-export UserMeta for backward compatibility
__all__ = ['UserMeta', 'UserInfo', 'ProviderTokenPage']
