from __future__ import annotations

from collections.abc import Mapping

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SecretStr,
)

from openhands.integrations.service_type_models import ProviderType


class ProviderToken(BaseModel):
    token: SecretStr | None = Field(default=None)
    user_id: str | None = Field(default=None)
    host: str | None = Field(default=None)

    model_config = ConfigDict(
        frozen=True,  # Makes the entire model immutable
        validate_assignment=True,
    )

    @classmethod
    def from_value(cls, token_value: ProviderToken | dict[str, str]) -> ProviderToken:
        """Factory method to create a ProviderToken from various input types"""
        if isinstance(token_value, cls):
            return token_value
        elif isinstance(token_value, dict):
            token_str = token_value.get('token', '')
            # Override with emtpy string if it was set to None
            # Cannot pass None to SecretStr
            if token_str is None:
                token_str = ''  # type: ignore[unreachable]
            user_id = token_value.get('user_id')
            host = token_value.get('host')
            return cls(token=SecretStr(token_str), user_id=user_id, host=host)

        else:
            raise ValueError('Unsupported Provider token type')


class CustomSecret(BaseModel):
    secret: SecretStr = Field(default_factory=lambda: SecretStr(''))
    description: str = Field(default='')

    model_config = ConfigDict(
        frozen=True,  # Makes the entire model immutable
        validate_assignment=True,
    )

    @classmethod
    def from_value(cls, secret_value: CustomSecret | dict[str, str]) -> CustomSecret:
        """Factory method to create a ProviderToken from various input types"""
        if isinstance(secret_value, CustomSecret):
            return secret_value
        elif isinstance(secret_value, dict):
            secret = secret_value.get('secret', '')
            description = secret_value.get('description', '')
            return cls(secret=SecretStr(secret), description=description)

        else:
            raise ValueError('Unsupport Provider token type')


PROVIDER_TOKEN_TYPE = Mapping[ProviderType, ProviderToken]
CUSTOM_SECRETS_TYPE = Mapping[str, CustomSecret]
