from datetime import datetime
from enum import Enum

from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel


class TokenResponse(BaseModel):
    token: str


class ProviderType(Enum):
    GITHUB = 'github'
    GITLAB = 'gitlab'
    BITBUCKET = 'bitbucket'
    BITBUCKET_DATA_CENTER = 'bitbucket_data_center'
    FORGEJO = 'forgejo'
    AZURE_DEVOPS = 'azure_devops'
    ENTERPRISE_SSO = 'enterprise_sso'


class TaskType(str, Enum):
    MERGE_CONFLICTS = 'MERGE_CONFLICTS'
    FAILING_CHECKS = 'FAILING_CHECKS'
    UNRESOLVED_COMMENTS = 'UNRESOLVED_COMMENTS'
    OPEN_ISSUE = 'OPEN_ISSUE'
    OPEN_PR = 'OPEN_PR'
    CREATE_MICROAGENT = 'CREATE_MICROAGENT'


class OwnerType(str, Enum):
    USER = 'user'
    ORGANIZATION = 'organization'


class SuggestedTask(BaseModel):
    git_provider: ProviderType
    task_type: TaskType
    repo: str
    issue_number: int
    title: str

    def get_provider_terms(self) -> dict:
        if self.git_provider == ProviderType.GITHUB:
            return {
                'requestType': 'Pull Request',
                'requestTypeShort': 'PR',
                'apiName': 'GitHub API',
                'tokenEnvVar': 'GITHUB_TOKEN',
                'ciSystem': 'GitHub Actions',
                'ciProvider': 'GitHub',
                'requestVerb': 'pull request',
            }
        elif self.git_provider == ProviderType.GITLAB:
            return {
                'requestType': 'Merge Request',
                'requestTypeShort': 'MR',
                'apiName': 'GitLab API',
                'tokenEnvVar': 'GITLAB_TOKEN',
                'ciSystem': 'CI pipelines',
                'ciProvider': 'GitLab',
                'requestVerb': 'merge request',
            }
        elif self.git_provider == ProviderType.BITBUCKET:
            return {
                'requestType': 'Pull Request',
                'requestTypeShort': 'PR',
                'apiName': 'Bitbucket API',
                'tokenEnvVar': 'BITBUCKET_TOKEN',
                'ciSystem': 'Bitbucket Pipelines',
                'ciProvider': 'Bitbucket',
                'requestVerb': 'pull request',
            }
        elif self.git_provider == ProviderType.BITBUCKET_DATA_CENTER:
            return {
                'requestType': 'Pull Request',
                'requestTypeShort': 'PR',
                'apiName': 'Bitbucket Data Center API',
                'tokenEnvVar': 'BITBUCKET_DATA_CENTER_TOKEN',
                'ciSystem': 'Bitbucket Pipelines',
                'ciProvider': 'Bitbucket Data Center',
                'requestVerb': 'pull request',
            }

        raise ValueError(f'Provider {self.git_provider} for suggested task prompts')

    def get_prompt_for_task(
        self,
    ) -> str:
        task_type = self.task_type
        issue_number = self.issue_number
        repo = self.repo

        env = Environment(
            loader=FileSystemLoader('openhands/integrations/templates/suggested_task')
        )

        template = None
        if task_type == TaskType.MERGE_CONFLICTS:
            template = env.get_template('merge_conflict_prompt.j2')
        elif task_type == TaskType.FAILING_CHECKS:
            template = env.get_template('failing_checks_prompt.j2')
        elif task_type == TaskType.UNRESOLVED_COMMENTS:
            template = env.get_template('unresolved_comments_prompt.j2')
        elif task_type == TaskType.OPEN_ISSUE:
            template = env.get_template('open_issue_prompt.j2')
        else:
            raise ValueError(f'Unsupported task type: {task_type}')

        terms = self.get_provider_terms()

        return template.render(issue_number=issue_number, repo=repo, **terms)


class CreateMicroagent(BaseModel):
    repo: str
    git_provider: ProviderType | None = None
    title: str | None = None


class Branch(BaseModel):
    name: str
    commit_sha: str
    protected: bool
    last_push_date: str | None = None  # ISO 8601 format date string


class PaginatedBranchesResponse(BaseModel):
    branches: list[Branch]
    has_next_page: bool
    current_page: int
    per_page: int
    total_count: int | None = None  # Some APIs don't provide total count


class Repository(BaseModel):
    id: str
    full_name: str
    git_provider: ProviderType
    is_public: bool
    stargazers_count: int | None = None
    link_header: str | None = None
    pushed_at: str | None = None  # ISO 8601 format date string
    owner_type: OwnerType | None = (
        None  # Whether the repository is owned by a user or organization
    )
    main_branch: str | None = None  # The main/default branch of the repository


class Comment(BaseModel):
    id: str
    body: str
    author: str
    created_at: datetime
    updated_at: datetime
    system: bool = False  # Whether this is a system-generated comment


class AuthenticationError(ValueError):
    """Raised when there is an issue with GitHub authentication."""

    pass


class UnknownException(ValueError):
    """Raised when there is an issue with GitHub communcation."""

    pass


class RateLimitError(ValueError):
    """Raised when the git provider's API rate limits are exceeded."""

    pass


class ProviderTimeoutError(ValueError):
    """Raised when a request to a git provider times out."""

    pass


class ResourceNotFoundError(ValueError):
    """Raised when a requested resource (file, directory, etc.) is not found."""

    pass


class MicroagentParseError(ValueError):
    """Raised when there is an error parsing a microagent file."""

    pass


class RequestMethod(Enum):
    POST = 'post'
    GET = 'get'
