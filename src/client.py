"""
Main ClickUp Client module.

This module contains the main ClickUp client class for interacting with the ClickUp API.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

import httpx

from .exceptions import (
    AuthenticationError,
    ClickUpError,
    RateLimitExceeded,
    ResourceNotFound,
    ValidationError,
)
from .models import User
from .resources.checklist import ChecklistResource
from .resources.comment import CommentResource
from .resources.custom_field import CustomFieldResource
from .resources.doc import DocResource
from .resources.folder import FolderResource
from .resources.goal import GoalResource
from .resources.list import ListResource
from .resources.space import SpaceResource
from .resources.tag import TagResource
from .resources.task import TaskResource
from .resources.time import TimeTrackingResource
from .resources.view import ViewResource
from .resources.webhook import WebhookResource
from .resources.workspace import WorkspaceResource

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("clickup")


class ClickUp:
    """
    Modern ClickUp API client with async support and resource-based interface.

    Usage:
        async with ClickUp(api_token) as client:
            workspaces = await client.workspaces.get_workspaces()
            user = await client.get_authenticated_user()

        # Or with the fluent interface
        async with ClickUp(api_token) as client:
            tasks = await client.workspace("workspace_id").list("list_id").tasks.get_all()

        # Obtain OAuth token (static method)
        token_info = await ClickUp.get_oauth_token(client_id, client_secret, code)
    """

    BASE_URL = "https://api.clickup.com/api/v2"
    OAUTH_URL = "https://api.clickup.com/api/v2/oauth/token"

    def __init__(
        self,
        api_token: str,
        base_url: str = BASE_URL,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        retry_rate_limited_requests: bool = True,
        rate_limit_buffer: int = 5,
    ):
        """Initialize the ClickUp client."""
        self.api_token = api_token
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.retry_rate_limited_requests = retry_rate_limited_requests
        self.rate_limit_buffer = rate_limit_buffer

        self._client = httpx.AsyncClient(timeout=timeout)
        self._rate_limit_remaining = 100
        self._rate_limit_reset = datetime.now().timestamp()
        self._current_method = None

        # Resource managers for the client
        self.workspaces = WorkspaceResource(self)
        self.spaces = SpaceResource(self)
        self.folders = FolderResource(self)
        self.lists = ListResource(self)
        self.tasks = TaskResource(self)
        self.comments = CommentResource(self)
        self.checklists = ChecklistResource(self)
        self.time = TimeTrackingResource(self)
        self.goals = GoalResource(self)
        self.docs = DocResource(self)
        self.custom_fields = CustomFieldResource(self)
        self.views = ViewResource(self)
        self.webhooks = WebhookResource(self)
        self.tags = TagResource(self)

        # Context IDs for fluent interface
        self._workspace_id: Optional[str] = None
        self._space_id: Optional[str] = None
        self._folder_id: Optional[str] = None
        self._list_id: Optional[str] = None
        self._task_id: Optional[str] = None
        self._template_id: Optional[str] = None
        self._doc_id: Optional[str] = None
        self._view_id: Optional[str] = None

    async def __aenter__(self) -> "ClickUp":
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()

    async def close(self):
        """Close the HTTP client and release resources."""
        await self._client.aclose()

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers including auth token."""
        return {
            "Authorization": self.api_token,
            "Content-Type": "application/json",
        }

    def _get_upload_headers(self) -> Dict[str, str]:
        """Get request headers for file uploads."""
        return {
            "Authorization": self.api_token,
        }

    async def _check_rate_limit(self):
        """Handle rate limiting by waiting if needed."""
        if self._rate_limit_remaining <= 5:
            now = datetime.now().timestamp()
            wait_time = max(0, self._rate_limit_reset - now + self.rate_limit_buffer)
            if wait_time > 0:
                logger.info(f"Rate limit approaching. Waiting {wait_time:.2f} seconds")
                await asyncio.sleep(wait_time)

    def _update_rate_limit_info(self, response: httpx.Response):
        """Update rate limit information from response headers."""
        if "X-RateLimit-Remaining" in response.headers:
            self._rate_limit_remaining = int(response.headers["X-RateLimit-Remaining"])
        if "X-RateLimit-Reset" in response.headers:
            self._rate_limit_reset = float(response.headers["X-RateLimit-Reset"])

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        api_version: str = "v2",
    ) -> Dict[str, Any]:
        """
        Make a request to the ClickUp API with automatic retry and error handling.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            params: Query parameters
            data: Request body data
            files: Files to upload
            api_version: API version to use (default: "v2")

        Returns:
            Response data as a dictionary or an empty dict for 204 responses

        Raises:
            RateLimitExceeded: When rate limit is exceeded and retries are exhausted
            AuthenticationError: When authentication fails
            ResourceNotFound: When the requested resource doesn't exist
            ValidationError: When the request data is invalid
            ClickUpError: For other API errors
        """
        url = f"https://api.clickup.com/api/{api_version}/{endpoint.lstrip('/')}"

        await self._check_rate_limit()

        retries = 0
        while True:
            try:
                response = await self._client.request(
                    method,
                    url,
                    headers=self._get_headers(),
                    params=params,
                    json=data if not files else None,
                    files=files,
                )
                response.raise_for_status()
                self._update_rate_limit_info(response)

                # Handle 204 No Content responses
                if response.status_code == 204:
                    return {}
                return response.json()

            except httpx.HTTPStatusError as e:
                error_data = {}
                try:
                    error_data = e.response.json()
                except (ValueError, KeyError):
                    pass

                status_code = e.response.status_code
                err_msg = error_data.get("err", str(e))

                if status_code == 401:
                    raise AuthenticationError(err_msg, status_code, error_data)
                elif status_code == 404:
                    raise ResourceNotFound(err_msg, status_code, error_data)
                elif status_code == 400:
                    raise ValidationError(err_msg, status_code, error_data)
                else:
                    raise ClickUpError(
                        f"HTTP error: {err_msg}", status_code, error_data
                    )

            except (httpx.RequestError, asyncio.TimeoutError) as e:
                if retries < self.max_retries:
                    wait = self.retry_delay * (2**retries)  # Exponential backoff
                    logger.warning(
                        f"Request failed: {str(e)}. Retrying in {wait} seconds"
                    )
                    await asyncio.sleep(wait)
                    retries += 1
                    continue
                raise ClickUpError(
                    f"Request failed after {self.max_retries} retries: {str(e)}"
                )

    # --- Static Method for OAuth --- #

    @staticmethod
    async def get_oauth_token(
        client_id: str,
        client_secret: str,
        code: str,
        timeout: float = 30.0,
    ) -> Dict[str, Any]:
        """
        Exchange an OAuth code for an access token.

        This is a static method and does not use the client's initialized api_token.

        Args:
            client_id: OAuth app client ID.
            client_secret: OAuth app client secret.
            code: Code received in the redirect URL after user authorization.
            timeout: Request timeout in seconds.

        Returns:
            Dictionary containing the access token and related info.

        Raises:
            ClickUpError: For network errors or API errors during token exchange.
            AuthenticationError: If client_id/client_secret/code are invalid.
        """
        url = ClickUp.OAUTH_URL
        payload = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
        }

        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()  # Raise exception for 4xx/5xx errors
                return response.json()
            except httpx.HTTPStatusError as e:
                error_data = {}
                try:
                    error_data = e.response.json()
                except (ValueError, KeyError):
                    pass
                status_code = e.response.status_code
                err_msg = error_data.get("err", str(e))

                if status_code == 401:
                    raise AuthenticationError(
                        f"OAuth token exchange failed: {err_msg}",
                        status_code,
                        error_data,
                    )
                else:
                    raise ClickUpError(
                        f"OAuth token exchange HTTP error: {err_msg}",
                        status_code,
                        error_data,
                    )
            except httpx.RequestError as e:
                raise ClickUpError(f"OAuth token exchange request failed: {str(e)}")

    # --- User Endpoint --- #

    async def get_authenticated_user(self) -> User:
        """
        Get details for the authenticated user.

        Returns:
            User object representing the authenticated user.

        Raises:
            AuthenticationError: If authentication fails
            ClickUpError: For other API errors
        """
        response = await self._request("GET", "user")
        # The response structure is {"user": {...user_details...}}
        return User.model_validate(response["user"])

    # Fluent interface methods

    def workspace(self, workspace_id: str) -> WorkspaceResource:
        """Set the current workspace context and return the workspace resource."""
        self._workspace_id = workspace_id
        return self.workspaces

    def space(self, space_id: str) -> SpaceResource:
        """Set the current space context and return the space resource."""
        self._space_id = space_id
        return self.spaces

    def folder(self, folder_id: str) -> FolderResource:
        """Set the current folder context and return the folder resource."""
        self._folder_id = folder_id
        return self.folders

    def list(self, list_id: str) -> ListResource:
        """Set the current list context and return the list resource."""
        self._list_id = list_id
        return self.lists

    def task(self, task_id: str) -> TaskResource:
        """Set the current task context and return the task resource."""
        self._task_id = task_id
        return self.tasks

    def template(self, template_id: str) -> "ClickUp":
        """Set the template ID for subsequent operations."""
        self._template_id = template_id
        return self

    def doc(self, doc_id: str) -> DocResource:
        """Set the current doc context and return the doc resource."""
        self._doc_id = doc_id
        return self.docs

    def view(self, view_id: str) -> "ClickUp":
        """Set the current view ID for subsequent operations."""
        self._view_id = view_id
        return self
