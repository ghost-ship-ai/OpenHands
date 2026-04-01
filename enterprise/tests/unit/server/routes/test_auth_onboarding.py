"""Tests for onboarding-related auth routes and functions.

Tests for:
- _should_redirect_to_onboarding() function
- /complete_onboarding endpoint
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request, status
from fastapi.responses import JSONResponse
from server.auth.saas_user_auth import SaasUserAuth
from server.routes.auth import (
    _should_redirect_to_onboarding,
    complete_onboarding,
)
from storage.org_member import OrgMember
from storage.role import Role
from storage.user import User

# --- Fixtures ---


@pytest.fixture
def mock_request():
    """Create a mock FastAPI Request."""
    request = MagicMock(spec=Request)
    request.url = MagicMock()
    request.url.hostname = 'localhost'
    request.url.netloc = 'localhost:8000'
    request.base_url = 'http://localhost:8000/'
    request.headers = {}
    request.cookies = {}
    return request


@pytest.fixture
def mock_user():
    """Create a mock User object."""
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.onboarding_completed = False
    return user


@pytest.fixture
def mock_org_member():
    """Create a mock OrgMember object."""
    member = MagicMock(spec=OrgMember)
    member.role_id = 1
    return member


@pytest.fixture
def mock_owner_role():
    """Create a mock owner Role object."""
    role = MagicMock(spec=Role)
    role.name = 'owner'
    return role


@pytest.fixture
def mock_admin_role():
    """Create a mock admin Role object."""
    role = MagicMock(spec=Role)
    role.name = 'admin'
    return role


@pytest.fixture
def mock_member_role():
    """Create a mock member Role object."""
    role = MagicMock(spec=Role)
    role.name = 'member'
    return role


# --- Tests for _should_redirect_to_onboarding ---


class TestShouldRedirectToOnboarding:
    """Tests for the _should_redirect_to_onboarding function."""

    @pytest.mark.asyncio
    async def test_returns_false_when_onboarding_completed(self, mock_user):
        """Test that completed onboarding users are not redirected."""
        mock_user.onboarding_completed = True

        result = await _should_redirect_to_onboarding('user-123', mock_user)

        assert result is False

    @pytest.mark.asyncio
    async def test_returns_true_for_cloud_mode_new_user(self, mock_user):
        """Test that cloud mode users with incomplete onboarding are redirected."""
        mock_user.onboarding_completed = False

        with patch('server.routes.auth.DEPLOYMENT_MODE', 'cloud'):
            result = await _should_redirect_to_onboarding('user-123', mock_user)

        assert result is True

    @pytest.mark.asyncio
    async def test_returns_true_for_self_hosted_owner(
        self, mock_user, mock_org_member, mock_owner_role
    ):
        """Test that self-hosted owners with incomplete onboarding are redirected."""
        mock_user.onboarding_completed = False
        user_id = str(uuid.uuid4())

        with (
            patch('server.routes.auth.DEPLOYMENT_MODE', 'self_hosted'),
            patch(
                'server.routes.auth.OrgMemberStore.get_org_member_for_current_org',
                new_callable=AsyncMock,
                return_value=mock_org_member,
            ),
            patch(
                'server.routes.auth.RoleStore.get_role_by_id',
                new_callable=AsyncMock,
                return_value=mock_owner_role,
            ),
        ):
            result = await _should_redirect_to_onboarding(user_id, mock_user)

        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_for_self_hosted_admin(
        self, mock_user, mock_org_member, mock_admin_role
    ):
        """Test that self-hosted admins are not redirected to onboarding."""
        mock_user.onboarding_completed = False
        user_id = str(uuid.uuid4())

        with (
            patch('server.routes.auth.DEPLOYMENT_MODE', 'self_hosted'),
            patch(
                'server.routes.auth.OrgMemberStore.get_org_member_for_current_org',
                new_callable=AsyncMock,
                return_value=mock_org_member,
            ),
            patch(
                'server.routes.auth.RoleStore.get_role_by_id',
                new_callable=AsyncMock,
                return_value=mock_admin_role,
            ),
        ):
            result = await _should_redirect_to_onboarding(user_id, mock_user)

        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_for_self_hosted_member(
        self, mock_user, mock_org_member, mock_member_role
    ):
        """Test that self-hosted members are not redirected to onboarding."""
        mock_user.onboarding_completed = False
        user_id = str(uuid.uuid4())

        with (
            patch('server.routes.auth.DEPLOYMENT_MODE', 'self_hosted'),
            patch(
                'server.routes.auth.OrgMemberStore.get_org_member_for_current_org',
                new_callable=AsyncMock,
                return_value=mock_org_member,
            ),
            patch(
                'server.routes.auth.RoleStore.get_role_by_id',
                new_callable=AsyncMock,
                return_value=mock_member_role,
            ),
        ):
            result = await _should_redirect_to_onboarding(user_id, mock_user)

        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_when_no_org_member(self, mock_user):
        """Test that users without org membership are not redirected in self-hosted."""
        mock_user.onboarding_completed = False
        user_id = str(uuid.uuid4())

        with (
            patch('server.routes.auth.DEPLOYMENT_MODE', 'self_hosted'),
            patch(
                'server.routes.auth.OrgMemberStore.get_org_member_for_current_org',
                new_callable=AsyncMock,
                return_value=None,
            ),
        ):
            result = await _should_redirect_to_onboarding(user_id, mock_user)

        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_when_role_not_found(self, mock_user, mock_org_member):
        """Test that users with missing role are not redirected in self-hosted."""
        mock_user.onboarding_completed = False
        user_id = str(uuid.uuid4())

        with (
            patch('server.routes.auth.DEPLOYMENT_MODE', 'self_hosted'),
            patch(
                'server.routes.auth.OrgMemberStore.get_org_member_for_current_org',
                new_callable=AsyncMock,
                return_value=mock_org_member,
            ),
            patch(
                'server.routes.auth.RoleStore.get_role_by_id',
                new_callable=AsyncMock,
                return_value=None,
            ),
        ):
            result = await _should_redirect_to_onboarding(user_id, mock_user)

        assert result is False


# --- Tests for /complete_onboarding endpoint ---


class TestCompleteOnboardingEndpoint:
    """Tests for the complete_onboarding API endpoint."""

    @pytest.mark.asyncio
    async def test_returns_401_when_not_authenticated(self, mock_request):
        """Test that unauthenticated requests return 401."""
        mock_user_auth = MagicMock(spec=SaasUserAuth)
        mock_user_auth.get_user_id = AsyncMock(return_value=None)

        with patch(
            'server.routes.auth.get_user_auth',
            new_callable=AsyncMock,
            return_value=mock_user_auth,
        ):
            result = await complete_onboarding(mock_request)

        assert isinstance(result, JSONResponse)
        assert result.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_returns_404_when_user_not_found(self, mock_request):
        """Test that request for non-existent user returns 404."""
        user_id = str(uuid.uuid4())
        mock_user_auth = MagicMock(spec=SaasUserAuth)
        mock_user_auth.get_user_id = AsyncMock(return_value=user_id)

        with (
            patch(
                'server.routes.auth.get_user_auth',
                new_callable=AsyncMock,
                return_value=mock_user_auth,
            ),
            patch(
                'server.routes.auth.UserStore.mark_onboarding_completed',
                new_callable=AsyncMock,
                return_value=None,
            ),
        ):
            result = await complete_onboarding(mock_request)

        assert isinstance(result, JSONResponse)
        assert result.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_returns_200_on_success(self, mock_request, mock_user):
        """Test successful onboarding completion returns 200."""
        user_id = str(uuid.uuid4())
        mock_user_auth = MagicMock(spec=SaasUserAuth)
        mock_user_auth.get_user_id = AsyncMock(return_value=user_id)

        with (
            patch(
                'server.routes.auth.get_user_auth',
                new_callable=AsyncMock,
                return_value=mock_user_auth,
            ),
            patch(
                'server.routes.auth.UserStore.mark_onboarding_completed',
                new_callable=AsyncMock,
                return_value=mock_user,
            ),
        ):
            result = await complete_onboarding(mock_request)

        assert isinstance(result, JSONResponse)
        assert result.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_calls_mark_onboarding_completed_with_user_id(
        self, mock_request, mock_user
    ):
        """Test that mark_onboarding_completed is called with the correct user_id."""
        user_id = str(uuid.uuid4())
        mock_user_auth = MagicMock(spec=SaasUserAuth)
        mock_user_auth.get_user_id = AsyncMock(return_value=user_id)
        mock_mark_completed = AsyncMock(return_value=mock_user)

        with (
            patch(
                'server.routes.auth.get_user_auth',
                new_callable=AsyncMock,
                return_value=mock_user_auth,
            ),
            patch(
                'server.routes.auth.UserStore.mark_onboarding_completed',
                mock_mark_completed,
            ),
        ):
            await complete_onboarding(mock_request)

        mock_mark_completed.assert_called_once_with(user_id)
