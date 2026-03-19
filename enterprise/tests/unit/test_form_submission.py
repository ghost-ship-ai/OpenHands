"""Unit tests for form submission API."""

import sys
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

# Mock the modules that are causing issues
sys.modules['google'] = MagicMock()
sys.modules['google.cloud'] = MagicMock()
sys.modules['google.cloud.sql'] = MagicMock()
sys.modules['google.cloud.sql.connector'] = MagicMock()
sys.modules['google.cloud.sql.connector.Connector'] = MagicMock()
mock_db_module = MagicMock()
mock_db_module.a_session_maker = MagicMock()
sys.modules['storage.database'] = mock_db_module

# Now import the modules we need
from server.routes.form_submission import (  # noqa: E402
    FormSubmissionRequest,
    FormSubmissionResponse,
    _validate_enterprise_lead_answers,
    submit_form,
)
from storage.form_submission import FormSubmission  # noqa: E402


@pytest.fixture
def valid_enterprise_lead_data():
    """Valid enterprise lead form data."""
    return {
        'form_type': 'enterprise_lead',
        'answers': {
            'request_type': 'saas',
            'name': 'John Doe',
            'company': 'Acme Corp',
            'email': 'john@acme.com',
            'message': 'We are interested in your enterprise plan.',
        },
    }


@pytest.fixture
def mock_request():
    """Create a mock FastAPI request."""
    request = MagicMock()
    request.state = MagicMock()
    request.state.user_auth = None  # Unauthenticated request
    return request


@pytest.fixture
def mock_authenticated_request():
    """Create a mock authenticated FastAPI request."""
    from server.auth.saas_user_auth import SaasUserAuth

    request = MagicMock()
    mock_user_auth = MagicMock(spec=SaasUserAuth)
    mock_user_auth.user_id = str(uuid4())
    request.state.user_auth = mock_user_auth
    return request


class TestEnterpriseLeadValidation:
    """Tests for enterprise lead form validation."""

    def test_valid_saas_request_type(self):
        """Test validation passes for saas request type."""
        answers = {
            'request_type': 'saas',
            'name': 'John Doe',
            'company': 'Acme Corp',
            'email': 'john@acme.com',
            'message': 'Interested in saas.',
        }
        # Should not raise
        _validate_enterprise_lead_answers(answers)

    def test_valid_self_hosted_request_type(self):
        """Test validation passes for self-hosted request type."""
        answers = {
            'request_type': 'self-hosted',
            'name': 'Jane Smith',
            'company': 'Tech Inc',
            'email': 'jane@tech.com',
            'message': 'Need self-hosted solution.',
        }
        # Should not raise
        _validate_enterprise_lead_answers(answers)

    def test_invalid_request_type(self):
        """Test validation fails for invalid request type."""
        answers = {
            'request_type': 'invalid',
            'name': 'John Doe',
            'company': 'Acme Corp',
            'email': 'john@acme.com',
            'message': 'Test message.',
        }
        with pytest.raises(HTTPException) as excinfo:
            _validate_enterprise_lead_answers(answers)
        assert excinfo.value.status_code == 400
        assert 'Invalid enterprise lead form answers' in excinfo.value.detail

    def test_missing_name(self):
        """Test validation fails when name is missing."""
        answers = {
            'request_type': 'saas',
            'company': 'Acme Corp',
            'email': 'john@acme.com',
            'message': 'Test message.',
        }
        with pytest.raises(HTTPException) as excinfo:
            _validate_enterprise_lead_answers(answers)
        assert excinfo.value.status_code == 400

    def test_empty_name(self):
        """Test validation fails when name is empty."""
        answers = {
            'request_type': 'saas',
            'name': '',
            'company': 'Acme Corp',
            'email': 'john@acme.com',
            'message': 'Test message.',
        }
        with pytest.raises(HTTPException) as excinfo:
            _validate_enterprise_lead_answers(answers)
        assert excinfo.value.status_code == 400

    def test_missing_email(self):
        """Test validation fails when email is missing."""
        answers = {
            'request_type': 'saas',
            'name': 'John Doe',
            'company': 'Acme Corp',
            'message': 'Test message.',
        }
        with pytest.raises(HTTPException) as excinfo:
            _validate_enterprise_lead_answers(answers)
        assert excinfo.value.status_code == 400

    def test_missing_company(self):
        """Test validation fails when company is missing."""
        answers = {
            'request_type': 'saas',
            'name': 'John Doe',
            'email': 'john@acme.com',
            'message': 'Test message.',
        }
        with pytest.raises(HTTPException) as excinfo:
            _validate_enterprise_lead_answers(answers)
        assert excinfo.value.status_code == 400

    def test_missing_message(self):
        """Test validation fails when message is missing."""
        answers = {
            'request_type': 'saas',
            'name': 'John Doe',
            'company': 'Acme Corp',
            'email': 'john@acme.com',
        }
        with pytest.raises(HTTPException) as excinfo:
            _validate_enterprise_lead_answers(answers)
        assert excinfo.value.status_code == 400


class TestSubmitForm:
    """Tests for form submission endpoint."""

    @pytest.mark.asyncio
    async def test_submit_enterprise_lead_unauthenticated(
        self, valid_enterprise_lead_data, mock_request
    ):
        """Test submitting enterprise lead form without authentication."""
        mock_session = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        # Mock the form submission with expected attributes
        mock_submission = MagicMock(spec=FormSubmission)
        mock_submission.id = uuid4()
        mock_submission.status = 'pending'
        mock_submission.created_at = MagicMock()

        @asynccontextmanager
        async def mock_a_session_maker():
            yield mock_session

        submission_request = FormSubmissionRequest(**valid_enterprise_lead_data)

        with patch('server.routes.form_submission.a_session_maker', mock_a_session_maker):
            with patch('server.routes.form_submission.uuid4', return_value=mock_submission.id):
                result = await submit_form(mock_request, submission_request)

                # Verify response type
                assert isinstance(result, FormSubmissionResponse)
                assert result.id == str(mock_submission.id)
                assert result.status == 'pending'

                # Verify database operations
                mock_session.add.assert_called_once()
                mock_session.commit.assert_called_once()

                # Verify the submission data
                added_submission = mock_session.add.call_args[0][0]
                assert isinstance(added_submission, FormSubmission)
                assert added_submission.form_type == 'enterprise_lead'
                assert added_submission.answers == valid_enterprise_lead_data['answers']
                assert added_submission.status == 'pending'
                assert added_submission.user_id is None  # Unauthenticated

    @pytest.mark.asyncio
    async def test_submit_enterprise_lead_authenticated(
        self, valid_enterprise_lead_data, mock_authenticated_request
    ):
        """Test submitting enterprise lead form with authentication."""
        mock_session = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        submission_id = uuid4()

        @asynccontextmanager
        async def mock_a_session_maker():
            yield mock_session

        submission_request = FormSubmissionRequest(**valid_enterprise_lead_data)
        expected_user_id = mock_authenticated_request.state.user_auth.user_id

        with patch('server.routes.form_submission.a_session_maker', mock_a_session_maker):
            with patch('server.routes.form_submission.uuid4', return_value=submission_id):
                result = await submit_form(mock_authenticated_request, submission_request)

                # Verify response type
                assert isinstance(result, FormSubmissionResponse)

                # Verify the submission data has user_id
                added_submission = mock_session.add.call_args[0][0]
                assert added_submission.user_id == UUID(expected_user_id)

    @pytest.mark.asyncio
    async def test_submit_invalid_form_type(self, mock_request):
        """Test submitting with invalid form type."""
        submission_request = FormSubmissionRequest(
            form_type='invalid_type',
            answers={'key': 'value'},
        )

        with pytest.raises(HTTPException) as excinfo:
            await submit_form(mock_request, submission_request)

        assert excinfo.value.status_code == 400
        assert 'Invalid form_type' in excinfo.value.detail

    @pytest.mark.asyncio
    async def test_submit_self_hosted_request_type(self, mock_request):
        """Test submitting with self-hosted request type."""
        mock_session = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        submission_id = uuid4()

        @asynccontextmanager
        async def mock_a_session_maker():
            yield mock_session

        submission_request = FormSubmissionRequest(
            form_type='enterprise_lead',
            answers={
                'request_type': 'self-hosted',
                'name': 'Test User',
                'company': 'Test Company',
                'email': 'test@example.com',
                'message': 'Need self-hosted solution.',
            },
        )

        with patch('server.routes.form_submission.a_session_maker', mock_a_session_maker):
            with patch('server.routes.form_submission.uuid4', return_value=submission_id):
                result = await submit_form(mock_request, submission_request)

                assert isinstance(result, FormSubmissionResponse)
                added_submission = mock_session.add.call_args[0][0]
                assert added_submission.answers['request_type'] == 'self-hosted'


class TestFormSubmissionRequest:
    """Tests for the Pydantic request model."""

    def test_valid_request(self, valid_enterprise_lead_data):
        """Test creating a valid request."""
        request = FormSubmissionRequest(**valid_enterprise_lead_data)
        assert request.form_type == 'enterprise_lead'
        assert request.answers == valid_enterprise_lead_data['answers']

    def test_form_type_max_length(self):
        """Test form_type max length validation."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            FormSubmissionRequest(
                form_type='a' * 51,  # Over 50 chars
                answers={'key': 'value'},
            )
