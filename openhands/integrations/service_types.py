from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol

from pydantic import SecretStr

from openhands.app_server.user.user_models import UserMeta
from openhands.core.logger import openhands_logger as logger
from openhands.integrations.service_type_models import (
    AuthenticationError as _AuthenticationError,
)
from openhands.integrations.service_type_models import (
    Branch,
    MicroagentParseError,
    PaginatedBranchesResponse,
    Repository,
    RequestMethod,
    ResourceNotFoundError,
    SuggestedTask,
)
from openhands.integrations.service_type_models import (
    Comment as _Comment,
)
from openhands.integrations.service_type_models import (
    CreateMicroagent as _CreateMicroagent,
)
from openhands.integrations.service_type_models import (
    OwnerType as _OwnerType,
)
from openhands.integrations.service_type_models import (
    ProviderTimeoutError as _ProviderTimeoutError,
)
from openhands.integrations.service_type_models import (
    ProviderType as _ProviderType,
)
from openhands.integrations.service_type_models import (
    RateLimitError as _RateLimitError,
)
from openhands.integrations.service_type_models import (
    TaskType as _TaskType,
)
from openhands.integrations.service_type_models import (
    TokenResponse as _TokenResponse,
)
from openhands.integrations.service_type_models import (
    UnknownException as _UnknownException,
)
from openhands.microagent.microagent import BaseMicroagent
from openhands.microagent.types import MicroagentContentResponse, MicroagentResponse
from openhands.server.types import AppMode

# Exports for backward compatibility
AuthenticationError = _AuthenticationError
Comment = _Comment
CreateMicroagent = _CreateMicroagent
OwnerType = _OwnerType
ProviderTimeoutError = _ProviderTimeoutError
ProviderType = _ProviderType
RateLimitError = _RateLimitError
TaskType = _TaskType
TokenResponse = _TokenResponse
UnknownException = _UnknownException


class BaseGitService(ABC):
    @property
    def provider(self) -> str:
        raise NotImplementedError('Subclasses must implement the provider property')

    # Method used to satisfy mypy for abstract class definition
    @abstractmethod
    async def _make_request(
        self,
        url: str,
        params: dict | None = None,
        method: RequestMethod = RequestMethod.GET,
    ) -> tuple[Any, dict]: ...

    @abstractmethod
    async def _get_cursorrules_url(self, repository: str) -> str:
        """Get the URL for checking .cursorrules file."""
        ...

    @abstractmethod
    async def _get_microagents_directory_url(
        self, repository: str, microagents_path: str
    ) -> str:
        """Get the URL for checking microagents directory."""
        ...

    @abstractmethod
    def _get_microagents_directory_params(self, microagents_path: str) -> dict | None:
        """Get parameters for the microagents directory request. Return None if no parameters needed."""
        ...

    @abstractmethod
    def _is_valid_microagent_file(self, item: dict) -> bool:
        """Check if an item represents a valid microagent file."""
        ...

    @abstractmethod
    def _get_file_name_from_item(self, item: dict) -> str:
        """Extract file name from directory item."""
        ...

    @abstractmethod
    def _get_file_path_from_item(self, item: dict, microagents_path: str) -> str:
        """Extract file path from directory item."""
        ...

    def _determine_microagents_path(self, repository_name: str) -> str:
        """Determine the microagents directory path based on repository name."""
        actual_repo_name = repository_name.split('/')[-1]

        # Check for special repository names that use a different structure
        if actual_repo_name == '.openhands' or actual_repo_name == 'openhands-config':
            # For repository name ".openhands", scan "microagents" folder
            return 'microagents'
        else:
            # Default behavior: look for .openhands/microagents directory
            return '.openhands/microagents'

    def _create_microagent_response(
        self, file_name: str, path: str
    ) -> MicroagentResponse:
        """Create a microagent response from basic file information."""
        # Extract name without extension
        name = file_name.replace('.md', '').replace('.cursorrules', 'cursorrules')

        return MicroagentResponse(
            name=name,
            path=path,
            created_at=datetime.now(),
        )

    def _parse_microagent_content(
        self, content: str, file_path: str
    ) -> MicroagentContentResponse:
        """Parse microagent content and extract triggers using BaseMicroagent.load.

        Args:
            content: Raw microagent file content
            file_path: Path to the file (used for microagent loading)

        Returns:
            MicroagentContentResponse with parsed content and triggers

        Raises:
            MicroagentParseError: If the microagent file cannot be parsed
        """
        try:
            # Use BaseMicroagent.load to properly parse the content
            # Create a temporary path object for the file
            temp_path = Path(file_path)

            # Load the microagent using the existing infrastructure
            microagent = BaseMicroagent.load(path=temp_path, file_content=content)

            # Extract triggers from the microagent's metadata
            triggers = microagent.metadata.triggers

            # Return the MicroagentContentResponse
            return MicroagentContentResponse(
                content=microagent.content,
                path=file_path,
                triggers=triggers,
                git_provider=self.provider,
            )

        except Exception as e:
            logger.error(f'Error parsing microagent content for {file_path}: {str(e)}')
            raise MicroagentParseError(
                f'Failed to parse microagent file {file_path}: {str(e)}'
            )

    async def _fetch_cursorrules_content(self, repository: str) -> Any | None:
        """Fetch .cursorrules file content from the repository via API.

        Args:
            repository: Repository name in format specific to the provider

        Returns:
            Raw API response content if .cursorrules file exists, None otherwise
        """
        cursorrules_url = await self._get_cursorrules_url(repository)
        cursorrules_response, _ = await self._make_request(cursorrules_url)
        return cursorrules_response

    async def _check_cursorrules_file(
        self, repository: str
    ) -> MicroagentResponse | None:
        """Check for .cursorrules file in the repository and return microagent response if found.

        Args:
            repository: Repository name in format specific to the provider

        Returns:
            MicroagentResponse for .cursorrules file if found, None otherwise
        """
        try:
            cursorrules_content = await self._fetch_cursorrules_content(repository)
            if cursorrules_content:
                return self._create_microagent_response('.cursorrules', '.cursorrules')
        except ResourceNotFoundError:
            logger.debug(f'No .cursorrules file found in {repository}')
        except Exception as e:
            logger.warning(f'Error checking .cursorrules file in {repository}: {e}')

        return None

    async def _process_microagents_directory(
        self, repository: str, microagents_path: str
    ) -> list[MicroagentResponse]:
        """Process microagents directory and return list of microagent responses.

        Args:
            repository: Repository name in format specific to the provider
            microagents_path: Path to the microagents directory

        Returns:
            List of MicroagentResponse objects found in the directory
        """
        microagents = []

        try:
            directory_url = await self._get_microagents_directory_url(
                repository, microagents_path
            )
            directory_params = self._get_microagents_directory_params(microagents_path)
            response, _ = await self._make_request(directory_url, directory_params)

            # Handle different response structures
            items = response
            if isinstance(response, dict) and 'values' in response:
                # Bitbucket format
                items = response['values']
            elif isinstance(response, dict) and 'nodes' in response:
                # GraphQL format (if used)
                items = response['nodes']

            for item in items:
                if self._is_valid_microagent_file(item):
                    try:
                        file_name = self._get_file_name_from_item(item)
                        file_path = self._get_file_path_from_item(
                            item, microagents_path
                        )
                        microagents.append(
                            self._create_microagent_response(file_name, file_path)
                        )
                    except Exception as e:
                        logger.warning(
                            f'Error processing microagent {item.get("name", "unknown")}: {str(e)}'
                        )
        except ResourceNotFoundError:
            logger.info(
                f'No microagents directory found in {repository} at {microagents_path}'
            )
        except Exception as e:
            logger.warning(f'Error fetching microagents directory: {str(e)}')

        return microagents

    async def get_microagents(self, repository: str) -> list[MicroagentResponse]:
        """Generic implementation of get_microagents that works across all providers.

        Args:
            repository: Repository name in format specific to the provider

        Returns:
            List of microagents found in the repository (without content for performance)
        """
        microagents_path = self._determine_microagents_path(repository)
        microagents = []

        # Step 1: Check for .cursorrules file
        cursorrules_microagent = await self._check_cursorrules_file(repository)
        if cursorrules_microagent:
            microagents.append(cursorrules_microagent)

        # Step 2: Check for microagents directory and process .md files
        directory_microagents = await self._process_microagents_directory(
            repository, microagents_path
        )
        microagents.extend(directory_microagents)

        return microagents

    def _truncate_comment(
        self, comment_body: str, max_comment_length: int = 500
    ) -> str:
        """Truncate comment body to a maximum length."""
        if len(comment_body) > max_comment_length:
            return comment_body[:max_comment_length] + '...'
        return comment_body


class InstallationsService(Protocol):
    async def get_installations(self) -> list[str]:
        """Get installations for the service; repos live underneath these installations"""
        ...


class GitService(Protocol):
    """Protocol defining the interface for Git service providers"""

    def __init__(
        self,
        user_id: str | None = None,
        token: SecretStr | None = None,
        external_auth_id: str | None = None,
        external_auth_token: SecretStr | None = None,
        external_token_manager: bool = False,
        base_domain: str | None = None,
    ) -> None:
        """Initialize the service with authentication details"""
        ...

    async def get_latest_token(self) -> SecretStr | None:
        """Get latest working token of the user"""
        ...

    async def get_user(self) -> UserMeta:
        """Get the authenticated user's information"""
        ...

    async def search_repositories(
        self,
        query: str,
        per_page: int,
        sort: str,
        order: str,
        public: bool,
        app_mode: AppMode,
    ) -> list[Repository]:
        """Search for public repositories"""
        ...

    async def get_all_repositories(
        self, sort: str, app_mode: AppMode
    ) -> list[Repository]:
        """Get repositories for the authenticated user"""
        ...

    async def get_paginated_repos(
        self,
        page: int,
        per_page: int,
        sort: str,
        installation_id: str | None,
        query: str | None = None,
    ) -> list[Repository]:
        """Get a page of repositories for the authenticated user"""
        ...

    async def get_suggested_tasks(self) -> list[SuggestedTask]:
        """Get suggested tasks for the authenticated user across all repositories"""
        ...

    async def get_repository_details_from_repo_name(
        self, repository: str
    ) -> Repository:
        """Gets all repository details from repository name"""

    async def get_branches(self, repository: str) -> list[Branch]:
        """Get branches for a repository"""

    async def get_paginated_branches(
        self, repository: str, page: int = 1, per_page: int = 30
    ) -> PaginatedBranchesResponse:
        """Get branches for a repository with pagination"""

    async def search_branches(
        self, repository: str, query: str, per_page: int = 30
    ) -> list[Branch]:
        """Search for branches within a repository"""

    async def get_microagents(self, repository: str) -> list[MicroagentResponse]:
        """Get microagents from a repository"""
        ...

    async def get_microagent_content(
        self, repository: str, file_path: str
    ) -> MicroagentContentResponse:
        """Get content of a specific microagent file

        Returns:
            MicroagentContentResponse with parsed content and triggers
        """
        ...

    async def get_pr_details(self, repository: str, pr_number: int) -> dict:
        """Get detailed information about a specific pull request/merge request

        Args:
            repository: Repository name in format specific to the provider
            pr_number: The pull request/merge request number

        Returns:
            Raw API response from the git provider
        """
        ...

    async def is_pr_open(self, repository: str, pr_number: int) -> bool:
        """Check if a PR is still active (not closed/merged).

        Args:
            repository: Repository name in format 'owner/repo'
            pr_number: The PR number to check

        Returns:
            True if PR is active (open), False if closed/merged
        """
        ...
