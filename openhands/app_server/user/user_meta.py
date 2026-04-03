from pydantic import BaseModel


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
