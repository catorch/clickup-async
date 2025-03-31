"""
ClickUp Client: A modern, elegant Python interface for the ClickUp API

This client provides a clean, asynchronous interface to work with the ClickUp API.
Features:
- Async/await support with httpx
- Strong type hints and validation with Pydantic
- Smart rate limiting handling
- Fluent interface design
- Comprehensive error handling
- Context manager support
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import httpx

from .exceptions import (
    AuthenticationError,
    ClickUpError,
    RateLimitExceeded,
    ResourceNotFound,
    ValidationError,
)
from .models import (
    BulkTimeInStatus,
    Checklist,
    Comment,
    Folder,
    Goal,
    KeyResult,
    KeyResultType,
    PaginatedResponse,
    Priority,
    Space,
    Task,
    TaskList,
    TaskTimeInStatus,
    TimeEntry,
    Workspace,
)
from .utils import convert_to_timestamp

# Configure logging
logger = logging.getLogger("clickup")


class ClickUp:
    """
    Modern ClickUp API client with async support and fluent interface.

    Usage:
        async with ClickUp(api_token) as client:
            tasks = await client.get_tasks(list_id="123")

    Or without context manager:
        client = ClickUp(api_token)
        try:
            tasks = await client.get_tasks(list_id="123")
        finally:
            await client.close()
    """

    BASE_URL = "https://api.clickup.com/api/v2"

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
        """
        Initialize the ClickUp client.

        Args:
            api_token: Your ClickUp API token
            base_url: Base URL for the ClickUp API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts for failed requests
            retry_delay: Initial delay between retries (exponential backoff is applied)
            retry_rate_limited_requests: Whether to retry rate-limited requests automatically
            rate_limit_buffer: Buffer to add to rate limit reset time in seconds
        """
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

        # Resource managers for fluent interface
        self._workspace_id: Optional[str] = None
        self._space_id: Optional[str] = None
        self._folder_id: Optional[str] = None
        self._list_id: Optional[str] = None
        self._task_id: Optional[str] = None
        self._template_id: Optional[str] = None

    async def __aenter__(self) -> "ClickUp":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        """Close the HTTP client and release resources"""
        await self._client.aclose()

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers including auth token"""
        return {
            "Authorization": self.api_token,
            "Content-Type": "application/json",
        }

    async def _check_rate_limit(self):
        """Handle rate limiting by waiting if needed"""
        if self._rate_limit_remaining <= 5:
            now = datetime.now().timestamp()
            wait_time = max(0, self._rate_limit_reset - now + self.rate_limit_buffer)
            if wait_time > 0:
                logger.info(f"Rate limit approaching. Waiting {wait_time:.2f} seconds")
                await asyncio.sleep(wait_time)

    def _update_rate_limit_info(self, response: httpx.Response):
        """Update rate limit information from response headers"""
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
    ) -> Dict[str, Any]:
        """
        Make a request to the ClickUp API with automatic retry and error handling.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            params: Query parameters
            data: Request body data
            files: Files to upload

        Returns:
            Response data as a dictionary

        Raises:
            RateLimitExceeded: When rate limit is exceeded and retries are exhausted
            AuthenticationError: When authentication fails
            ResourceNotFound: When the requested resource doesn't exist
            ValidationError: When the request data is invalid
            ClickUpError: For other API errors
        """
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"

        await self._check_rate_limit()

        retries = 0
        while True:
            try:
                response = await self._client.request(
                    method,
                    url,
                    params=params,
                    json=data,
                    files=files,
                    headers=self._get_headers(),
                )

                self._update_rate_limit_info(response)

                # Check for 404 before any other processing
                if response.status_code == 404:
                    error_data = {}
                    try:
                        error_data = response.json()
                    except (ValueError, KeyError):
                        pass
                    err_msg = error_data.get("err", f"Resource not found: {endpoint}")
                    raise ResourceNotFound(err_msg, 404, error_data)

                if response.status_code == 429:
                    if self.retry_rate_limited_requests and retries < self.max_retries:
                        retry_after = int(
                            response.headers.get("Retry-After", self.retry_delay)
                        )
                        logger.warning(
                            f"Rate limit exceeded. Retrying after {retry_after} seconds"
                        )
                        await asyncio.sleep(retry_after)
                        retries += 1
                        continue
                    else:
                        raise RateLimitExceeded(
                            "Rate limit exceeded and max retries reached"
                        )

                response.raise_for_status()
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

    # Fluent interface methods

    def workspace(self, workspace_id: str) -> "ClickUp":
        """Set the current workspace context for chained methods"""
        self._workspace_id = workspace_id
        return self

    def space(self, space_id: str) -> "ClickUp":
        """Set the current space context for chained methods"""
        self._space_id = space_id
        return self

    def folder(self, folder_id: str) -> "ClickUp":
        """Set the current folder context for chained methods"""
        self._folder_id = folder_id
        return self

    def list(self, list_id: str) -> "ClickUp":
        """Set the current list context for chained methods"""
        self._list_id = list_id
        return self

    def task(self, task_id: str) -> "ClickUp":
        """Set the current task context for chained methods"""
        self._task_id = task_id
        return self

    def template(self, template_id: str) -> "ClickUp":
        """Set the template ID for subsequent operations"""
        self._template_id = template_id
        return self

    # Workspace methods

    async def get_workspaces(self) -> List[Workspace]:
        """
        Get all workspaces accessible to the authenticated user

        Returns:
            List of Workspace objects
        """
        response = await self._request("GET", "team")
        print("Workspace response:", response)  # Debug log
        return [Workspace.model_validate(team) for team in response.get("teams", [])]

    async def get_workspace(self, workspace_id: Optional[str] = None) -> Workspace:
        """
        Get details for a specific workspace

        Args:
            workspace_id: ID of the workspace to fetch (uses the one set by workspace() if not provided)

        Returns:
            Workspace object
        """
        workspace_id = workspace_id or self._workspace_id
        if not workspace_id:
            raise ValueError("Workspace ID must be provided")

        response = await self._request("GET", f"team/{workspace_id}")
        return Workspace.model_validate(response.get("team", {}))

    # Space methods

    async def get_spaces(
        self, workspace_id: Optional[str] = None, archived: bool = False
    ) -> List[Space]:
        """
        Get all spaces in a workspace.

        Args:
            workspace_id: ID of the workspace (uses the one set by workspace() if not provided)
            archived: Whether to include archived spaces (defaults to False)

        Returns:
            List of Space objects

        Raises:
            ValueError: If workspace_id is not provided
            AuthenticationError: If authentication fails
            ResourceNotFound: If the workspace doesn't exist
            ClickUpError: For other API errors
        """
        workspace_id = workspace_id or self._workspace_id
        if not workspace_id:
            raise ValueError("Workspace ID must be provided")

        params = {"archived": str(archived).lower()}
        response = await self._request(
            "GET", f"team/{workspace_id}/space", params=params
        )
        return [Space.model_validate(space) for space in response.get("spaces", [])]

    async def get_space(self, space_id: Optional[str] = None) -> Space:
        """
        Get details for a specific space.

        Args:
            space_id: ID of the space to fetch (uses the one set by space() if not provided)

        Returns:
            Space object

        Raises:
            ValueError: If space_id is not provided
            AuthenticationError: If authentication fails
            ResourceNotFound: If the space doesn't exist
            ClickUpError: For other API errors
        """
        space_id = space_id or self._space_id
        if not space_id:
            raise ValueError("Space ID must be provided")

        response = await self._request("GET", f"space/{space_id}")
        return Space.model_validate(response)

    async def create_space(
        self,
        name: str,
        workspace_id: Optional[str] = None,
        private: bool = False,
        admin_can_manage: bool = True,
        multiple_assignees: bool = True,
        features: Optional[Dict[str, bool]] = None,
        color: Optional[str] = None,
    ) -> Space:
        """
        Create a new space in a workspace.

        Args:
            name: Name of the new space
            workspace_id: ID of the workspace (uses the one set by workspace() if not provided)
            private: Whether the space is private (defaults to False)
            admin_can_manage: Whether admins can manage the space (Enterprise feature, defaults to True)
            multiple_assignees: Whether to allow multiple assignees for tasks (defaults to True)
            features: Dictionary of space features to enable/disable
            color: Color for the space (hex code)

        Returns:
            The created Space object

        Raises:
            ValueError: If workspace_id is not provided or name is empty
            AuthenticationError: If authentication fails
            ResourceNotFound: If the workspace doesn't exist
            ValidationError: If the request data is invalid
            ClickUpError: For other API errors
        """
        workspace_id = workspace_id or self._workspace_id
        if not workspace_id:
            raise ValueError("Workspace ID must be provided")
        if not name:
            raise ValueError("Space name must not be empty")

        data = {
            "name": name,
            "private": private,
            "admin_can_manage": admin_can_manage,
            "multiple_assignees": multiple_assignees,
        }

        if features is not None:
            data["features"] = features
        if color is not None:
            data["color"] = color

        response = await self._request("POST", f"team/{workspace_id}/space", data=data)
        return Space.model_validate(response)

    async def update_space(
        self,
        space_id: Optional[str] = None,
        name: Optional[str] = None,
        color: Optional[str] = None,
        private: Optional[bool] = None,
        admin_can_manage: Optional[bool] = None,
        multiple_assignees: Optional[bool] = None,
        features: Optional[Dict[str, bool]] = None,
    ) -> Space:
        """
        Update an existing space.

        Args:
            space_id: ID of the space to update (uses the one set by space() if not provided)
            name: New name for the space
            color: New color for the space (hex code)
            private: Whether the space should be private
            admin_can_manage: Whether admins can manage the space (Enterprise feature)
            multiple_assignees: Whether to allow multiple assignees for tasks
            features: Dictionary of space features to enable/disable

        Returns:
            The updated Space object

        Raises:
            ValueError: If space_id is not provided
            AuthenticationError: If authentication fails
            ResourceNotFound: If the space doesn't exist
            ValidationError: If the request data is invalid
            ClickUpError: For other API errors
        """
        space_id = space_id or self._space_id
        if not space_id:
            raise ValueError("Space ID must be provided")

        data = {}
        if name is not None:
            data["name"] = name
        if color is not None:
            data["color"] = color
        if private is not None:
            data["private"] = private
        if admin_can_manage is not None:
            data["admin_can_manage"] = admin_can_manage
        if multiple_assignees is not None:
            data["multiple_assignees"] = multiple_assignees
        if features is not None:
            data["features"] = features

        response = await self._request("PUT", f"space/{space_id}", data=data)
        return Space.model_validate(response)

    async def delete_space(self, space_id: Optional[str] = None) -> bool:
        """
        Delete a space.

        Args:
            space_id: ID of the space to delete (uses the one set by space() if not provided)

        Returns:
            True if successful

        Raises:
            ValueError: If space_id is not provided
            AuthenticationError: If authentication fails
            ResourceNotFound: If the space doesn't exist
            ClickUpError: For other API errors
        """
        space_id = space_id or self._space_id
        if not space_id:
            raise ValueError("Space ID must be provided")

        await self._request("DELETE", f"space/{space_id}")
        return True

    # Folder methods

    async def get_folders(self, space_id: Optional[str] = None) -> List[Folder]:
        """
        Get all folders in a space

        Args:
            space_id: ID of the space (uses the one set by space() if not provided)

        Returns:
            List of Folder objects
        """
        space_id = space_id or self._space_id
        if not space_id:
            raise ValueError("Space ID must be provided")

        response = await self._request("GET", f"space/{space_id}/folder")
        return [Folder.model_validate(folder) for folder in response.get("folders", [])]

    async def get_folder(self, folder_id: Optional[str] = None) -> Folder:
        """
        Get details for a specific folder

        Args:
            folder_id: ID of the folder to fetch (uses the one set by folder() if not provided)

        Returns:
            Folder object
        """
        folder_id = folder_id or self._folder_id
        if not folder_id:
            raise ValueError("Folder ID must be provided")

        response = await self._request("GET", f"folder/{folder_id}")
        return Folder.model_validate(response)

    async def create_folder(
        self,
        name: str,
        space_id: Optional[str] = None,
        hidden: bool = False,
    ) -> Folder:
        """
        Create a new folder in a space

        Args:
            name: Name of the new folder
            space_id: ID of the space (uses the one set by space() if not provided)
            hidden: Whether the folder should be hidden

        Returns:
            The created Folder object
        """
        space_id = space_id or self._space_id
        if not space_id:
            raise ValueError("Space ID must be provided")

        data = {
            "name": name,
            "hidden": hidden,
        }

        response = await self._request("POST", f"space/{space_id}/folder", data=data)
        return Folder.model_validate(response)

    async def update_folder(
        self,
        folder_id: Optional[str] = None,
        name: Optional[str] = None,
        hidden: Optional[bool] = None,
    ) -> Folder:
        """
        Update an existing folder

        Args:
            folder_id: ID of the folder to update (uses the one set by folder() if not provided)
            name: New name for the folder
            hidden: Whether the folder should be hidden

        Returns:
            The updated Folder object
        """
        folder_id = folder_id or self._folder_id
        if not folder_id:
            raise ValueError("Folder ID must be provided")

        data = {}
        if name is not None:
            data["name"] = name
        if hidden is not None:
            data["hidden"] = hidden

        response = await self._request("PUT", f"folder/{folder_id}", data=data)
        return Folder.model_validate(response)

    async def delete_folder(self, folder_id: Optional[str] = None) -> bool:
        """
        Delete a folder

        Args:
            folder_id: ID of the folder to delete (uses the one set by folder() if not provided)

        Returns:
            True if successful

        Raises:
            ResourceNotFound: If the folder doesn't exist
            ClickUpError: For other API errors
        """
        folder_id = folder_id or self._folder_id
        if not folder_id:
            raise ValueError("Folder ID must be provided")

        try:
            await self._request("DELETE", f"folder/{folder_id}")
            return True
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ResourceNotFound(f"Folder {folder_id} not found")
            raise ClickUpError(f"Failed to delete folder: {str(e)}")

    async def create_folder_from_template(
        self,
        name: str,
        space_id: Optional[str] = None,
        template_id: Optional[str] = None,
        return_immediately: bool = True,
        options: Optional[Dict[str, Any]] = None,
    ) -> Folder:
        """
        Create a new folder using a folder template within a space.

        Args:
            name: Name of the new folder
            space_id: ID of the space where the folder will be created
            template_id: ID of the folder template to use
            return_immediately: Whether to return immediately without waiting for all assets to be created
            options: Additional options for creating the folder from template

        Returns:
            The newly created folder

        Raises:
            ValidationError: If required parameters are missing
            ResourceNotFound: If the space or template doesn't exist
            ClickUpError: For other API errors
        """
        space_id = space_id or self._space_id
        if not space_id:
            raise ValidationError("space_id is required")

        template_id = template_id or self._template_id
        if not template_id:
            raise ValidationError("template_id is required")

        if not name:
            raise ValidationError("name is required")

        data = {
            "name": name,
            "return_immediately": return_immediately,
        }

        if options:
            data["options"] = options

        response = await self._request(
            "POST",
            f"space/{space_id}/folder_template/{template_id}",
            data=data,
        )

        return Folder(**response)

    # List methods

    async def get_lists(
        self,
        folder_id: Optional[str] = None,
        space_id: Optional[str] = None,
        archived: bool = False,
    ) -> List[TaskList]:
        """
        Get all lists in a folder or space

        Args:
            folder_id: ID of the folder (uses the one set by folder() if not provided)
            space_id: ID of the space for folderless lists (uses the one set by space() if not provided)
            archived: Whether to include archived lists

        Returns:
            List of List objects
        """
        params = {"archived": str(archived).lower()}

        if folder_id or self._folder_id:
            folder_id = folder_id or self._folder_id
            response = await self._request(
                "GET", f"folder/{folder_id}/list", params=params
            )
            return [TaskList.model_validate(lst) for lst in response.get("lists", [])]
        elif space_id or self._space_id:
            space_id = space_id or self._space_id
            response = await self._request(
                "GET", f"space/{space_id}/list", params=params
            )
            return [TaskList.model_validate(lst) for lst in response.get("lists", [])]
        else:
            raise ValueError("Either folder_id or space_id must be provided")

    async def get_list(self, list_id: Optional[str] = None) -> TaskList:
        """
        Get details for a specific list

        Args:
            list_id: ID of the list to fetch (uses the one set by list() if not provided)

        Returns:
            List object

        Raises:
            ResourceNotFound: If the list doesn't exist
            ClickUpError: For other API errors
        """
        list_id = list_id or self._list_id
        if not list_id:
            raise ValueError("List ID must be provided")

        response = await self._request("GET", f"list/{list_id}")
        return TaskList.model_validate(response)

    async def create_list(
        self,
        name: str,
        folder_id: Optional[str] = None,
        space_id: Optional[str] = None,
        content: Optional[str] = None,
        due_date: Optional[Union[str, int, datetime]] = None,
        priority: Optional[Union[int, Priority]] = None,
        assignee: Optional[str] = None,
        status: Optional[str] = None,
    ) -> TaskList:
        """
        Create a new list in a folder or space

        Args:
            name: Name of the new list
            folder_id: ID of the folder (uses the one set by folder() if not provided)
            space_id: ID of the space for folderless lists (uses the one set by space() if not provided)
            content: Description of the list
            due_date: Due date (string, timestamp, or datetime)
            priority: Priority level (1=Urgent, 2=High, 3=Normal, 4=Low)
            assignee: Default assignee ID
            status: Default status

        Returns:
            The created List object
        """
        data: Dict[str, Any] = {"name": name}

        if content is not None:
            data["content"] = content
        if due_date is not None:
            data["due_date"] = str(convert_to_timestamp(due_date))
        if priority is not None:
            if isinstance(priority, Priority):
                data["priority"] = str(priority.value)
            else:
                data["priority"] = str(priority)
        if assignee is not None:
            data["assignee"] = assignee
        if status is not None:
            data["status"] = status

        if folder_id or self._folder_id:
            folder_id = folder_id or self._folder_id
            response = await self._request(
                "POST", f"folder/{folder_id}/list", data=data
            )
        elif space_id or self._space_id:
            space_id = space_id or self._space_id
            response = await self._request("POST", f"space/{space_id}/list", data=data)
        else:
            raise ValueError("Either folder_id or space_id must be provided")

        return TaskList.model_validate(response)

    async def update_list(
        self,
        list_id: Optional[str] = None,
        name: Optional[str] = None,
        content: Optional[str] = None,
        due_date: Optional[Union[str, int, datetime]] = None,
        due_date_time: Optional[bool] = None,
        priority: Optional[Union[int, Priority]] = None,
        assignee: Optional[str] = None,
        unset_status: Optional[bool] = None,
    ) -> TaskList:
        """
        Update an existing list

        Args:
            list_id: ID of the list to update (uses the one set by list() if not provided)
            name: New name for the list
            content: New description for the list
            due_date: New due date (string, timestamp, or datetime)
            due_date_time: Whether the due date includes time
            priority: New priority level (1=Urgent, 2=High, 3=Normal, 4=Low)
            assignee: New default assignee ID
            unset_status: Whether to unset the default status

        Returns:
            The updated List object
        """
        list_id = list_id or self._list_id
        if not list_id:
            raise ValueError("List ID must be provided")

        data = {}

        if name is not None:
            data["name"] = name
        if content is not None:
            data["content"] = content
        if due_date is not None:
            data["due_date"] = str(convert_to_timestamp(due_date))
        if due_date_time is not None:
            data["due_date_time"] = str(due_date_time).lower()
        if priority is not None:
            if isinstance(priority, Priority):
                data["priority"] = str(priority.value)
            else:
                data["priority"] = str(priority)
        if assignee is not None:
            data["assignee"] = assignee
        if unset_status is not None:
            data["unset_status"] = str(unset_status).lower()

        response = await self._request("PUT", f"list/{list_id}", data=data)
        return TaskList.model_validate(response)

    async def delete_list(self, list_id: Optional[str] = None) -> bool:
        """
        Delete a list

        Args:
            list_id: ID of the list to delete (uses the one set by list() if not provided)

        Returns:
            True if successful

        Raises:
            ResourceNotFound: If the list doesn't exist
            ClickUpError: For other API errors
        """
        list_id = list_id or self._list_id
        if not list_id:
            raise ValueError("List ID must be provided")

        try:
            await self._request("DELETE", f"list/{list_id}")
            return True
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ResourceNotFound(f"List {list_id} not found")
            raise ClickUpError(f"Failed to delete list: {str(e)}")

    async def add_task_to_list(
        self,
        task_id: Optional[str] = None,
        list_id: Optional[str] = None,
    ) -> bool:
        """
        Add a task to an additional list.
        Note: This endpoint requires the Tasks in Multiple List ClickApp to be enabled.

        Args:
            task_id: ID of the task to add (uses the one set by task() if not provided)
            list_id: ID of the list to add the task to (uses the one set by list() if not provided)

        Returns:
            True if successful

        Raises:
            ValueError: If task_id or list_id is not provided
            ClickUpError: If the Tasks in Multiple List ClickApp is not enabled
        """
        task_id = task_id or self._task_id
        list_id = list_id or self._list_id

        if not task_id:
            raise ValueError("Task ID must be provided")
        if not list_id:
            raise ValueError("List ID must be provided")

        await self._request("POST", f"list/{list_id}/task/{task_id}")
        return True

    async def remove_task_from_list(
        self,
        task_id: Optional[str] = None,
        list_id: Optional[str] = None,
    ) -> bool:
        """
        Remove a task from an additional list.
        Note: You cannot remove a task from its home list.
        This endpoint requires the Tasks in Multiple List ClickApp to be enabled.

        Args:
            task_id: ID of the task to remove (uses the one set by task() if not provided)
            list_id: ID of the list to remove the task from (uses the one set by list() if not provided)

        Returns:
            True if successful

        Raises:
            ValueError: If task_id or list_id is not provided
            ClickUpError: If the Tasks in Multiple List ClickApp is not enabled
        """
        task_id = task_id or self._task_id
        list_id = list_id or self._list_id

        if not task_id:
            raise ValueError("Task ID must be provided")
        if not list_id:
            raise ValueError("List ID must be provided")

        await self._request("DELETE", f"list/{list_id}/task/{task_id}")
        return True

    async def create_list_from_template(
        self,
        name: str,
        folder_id: Optional[str] = None,
        space_id: Optional[str] = None,
        template_id: Optional[str] = None,
        return_immediately: bool = True,
        options: Optional[Dict[str, Any]] = None,
    ) -> TaskList:
        """
        Create a new list using a list template in a folder or space.
        This request runs synchronously by default with return_immediately=true.
        The request returns the future List ID immediately, but the List might not be created
        at the time of the request returning.

        Args:
            name: Name of the new list
            folder_id: ID of the folder (uses the one set by folder() if not provided)
            space_id: ID of the space (uses the one set by space() if not provided)
            template_id: ID of the template (uses the one set by template() if not provided)
            return_immediately: Whether to return immediately without waiting for all assets to be created
            options: Additional options for creating the list from template

        Returns:
            The created List object

        Raises:
            ValueError: If neither folder_id nor space_id is provided, or if template_id is not provided
            ResourceNotFound: If the template, folder, or space doesn't exist
            ValidationError: If the request data is invalid
            ClickUpError: For other API errors
        """
        template_id = template_id or self._template_id
        if not template_id:
            raise ValueError("Template ID must be provided")

        data = {
            "name": name,
            "return_immediately": return_immediately,
        }

        if options:
            data["options"] = options

        if folder_id or self._folder_id:
            folder_id = folder_id or self._folder_id
            response = await self._request(
                "POST",
                f"folder/{folder_id}/list_template/{template_id}",
                data=data,
            )
        elif space_id or self._space_id:
            space_id = space_id or self._space_id
            response = await self._request(
                "POST",
                f"space/{space_id}/list_template/{template_id}",
                data=data,
            )
        else:
            raise ValueError("Either folder_id or space_id must be provided")

        return TaskList.model_validate(response)

    async def get_list_with_markdown(
        self,
        list_id: Optional[str] = None,
        include_markdown_description: bool = True,
    ) -> TaskList:
        """
        Get details for a specific list with markdown support.

        Args:
            list_id: ID of the list to fetch (uses the one set by list() if not provided)
            include_markdown_description: Whether to return list descriptions in Markdown format

        Returns:
            List object with markdown content if requested

        Raises:
            ValueError: If list_id is not provided
            ResourceNotFound: If the list doesn't exist
            ClickUpError: For other API errors
        """
        list_id = list_id or self._list_id
        if not list_id:
            raise ValueError("List ID must be provided")

        params = {
            "include_markdown_description": str(include_markdown_description).lower()
        }
        response = await self._request("GET", f"list/{list_id}", params=params)
        return TaskList.model_validate(response)

    # Task methods

    async def get_tasks(
        self,
        list_id: Optional[str] = None,
        archived: bool = False,
        page: int = 0,
        order_by: str = "created",
        reverse: bool = False,
        subtasks: bool = False,
        statuses: Optional[List[str]] = None,
        include_closed: bool = False,
        assignees: Optional[List[str]] = None,
        watchers: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        due_date_gt: Optional[Union[str, int, datetime]] = None,
        due_date_lt: Optional[Union[str, int, datetime]] = None,
        date_created_gt: Optional[Union[str, int, datetime]] = None,
        date_created_lt: Optional[Union[str, int, datetime]] = None,
        date_updated_gt: Optional[Union[str, int, datetime]] = None,
        date_updated_lt: Optional[Union[str, int, datetime]] = None,
        date_done_gt: Optional[Union[str, int, datetime]] = None,
        date_done_lt: Optional[Union[str, int, datetime]] = None,
        custom_fields: Optional[List[Dict[str, Any]]] = None,
        custom_field: Optional[List[Dict[str, Any]]] = None,
        custom_items: Optional[List[int]] = None,
        include_markdown_description: bool = False,
        priority: Optional[Union[int, Priority]] = None,
    ) -> PaginatedResponse[Task]:
        """
        Get tasks from a list with pagination

        Args:
            list_id: ID of the list (uses the one set by list() if not provided)
            archived: Include archived tasks
            page: Page number (starting from 0)
            order_by: Field to order by (id, created, updated, due_date)
            reverse: Reverse the order
            subtasks: Include subtasks
            statuses: Filter by status names
            include_closed: Include closed tasks
            assignees: Filter by assignee IDs
            watchers: Filter by watcher IDs
            tags: Filter by tags
            due_date_gt: Tasks due after this date
            due_date_lt: Tasks due before this date
            date_created_gt: Tasks created after this date
            date_created_lt: Tasks created before this date
            date_updated_gt: Tasks updated after this date
            date_updated_lt: Tasks updated before this date
            date_done_gt: Tasks completed after this date
            date_done_lt: Tasks completed before this date
            custom_fields: Filter by custom field values
            custom_field: Filter by a single custom field value
            custom_items: Filter by custom task types (0=Task, 1=Milestone)
            include_markdown_description: Return task descriptions in Markdown format
            priority: Filter by priority level (1=Urgent, 2=High, 3=Normal, 4=Low)

        Returns:
            PaginatedResponse containing tasks
        """
        self._current_method = "get_tasks"
        try:
            list_id = list_id or self._list_id
            if not list_id:
                raise ValueError("List ID must be provided")

            params = {
                "archived": str(archived).lower(),
                "page": page,
                "order_by": order_by,
                "reverse": str(reverse).lower(),
                "subtasks": str(subtasks).lower(),
                "include_closed": str(include_closed).lower(),
                "include_markdown_description": str(
                    include_markdown_description
                ).lower(),
            }

            if statuses:
                params["statuses[]"] = statuses
            if assignees:
                params["assignees[]"] = assignees
            if watchers:
                params["watchers[]"] = watchers
            if tags:
                params["tags[]"] = tags
            if custom_fields:
                params["custom_fields"] = json.dumps(custom_fields)
            if custom_field:
                params["custom_field"] = json.dumps(custom_field)
            if custom_items:
                params["custom_items[]"] = custom_items
            if priority is not None:
                if isinstance(priority, Priority):
                    params["priority"] = str(priority.value)
                else:
                    params["priority"] = str(priority)

            # Handle date filters
            date_filters = {
                "due_date": (due_date_gt, due_date_lt),
                "date_created": (date_created_gt, date_created_lt),
                "date_updated": (date_updated_gt, date_updated_lt),
                "date_done": (date_done_gt, date_done_lt),
            }

            for prefix, (gt, lt) in date_filters.items():
                if gt:
                    params[f"{prefix}_gt"] = str(convert_to_timestamp(gt))
                if lt:
                    params[f"{prefix}_lt"] = str(convert_to_timestamp(lt))

            response = await self._request("GET", f"list/{list_id}/task", params=params)
            tasks = [Task.model_validate(task) for task in response.get("tasks", [])]

            # Determine if there are more pages and prepare next page params
            next_page_params = None
            if response.get("has_more"):
                next_page_params = dict(params)
                next_page_params["page"] = page + 1
                next_page_params["list_id"] = list_id

            return PaginatedResponse(tasks, self, next_page_params)
        finally:
            self._current_method = None

    async def get_task(self, task_id: Optional[str] = None) -> Task:
        """
        Get a task by ID

        Args:
            task_id: ID of the task (uses the one set by task() if not provided)

        Returns:
            Task object
        """
        task_id = task_id or self._task_id
        if not task_id:
            raise ValueError("Task ID must be provided")

        response = await self._request("GET", f"task/{task_id}")
        return Task.model_validate(response)

    async def create_task(
        self,
        name: str,
        list_id: Optional[str] = None,
        description: Optional[str] = None,
        assignees: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        status: Optional[str] = None,
        priority: Optional[Union[int, Priority]] = None,
        due_date: Optional[Union[str, int, datetime]] = None,
        due_date_time: Optional[bool] = None,
        time_estimate: Optional[int] = None,
        start_date: Optional[Union[str, int, datetime]] = None,
        start_date_time: Optional[bool] = None,
        notify_all: bool = True,
        parent: Optional[str] = None,
        links_to: Optional[str] = None,
        check_required_custom_fields: bool = True,
        custom_fields: Optional[List[Dict[str, Any]]] = None,
        custom_task_ids: bool = False,
        team_id: Optional[str] = None,
        points: Optional[float] = None,
        group_assignees: Optional[List[str]] = None,
        markdown_content: Optional[str] = None,
        custom_item_id: Optional[int] = None,
    ) -> Task:
        """
        Create a new task

        Args:
            name: Task name
            list_id: ID of the list (uses the one set by list() if not provided)
            description: Task description
            assignees: List of assignee IDs
            tags: List of tags
            status: Task status
            priority: Priority level (1=Urgent, 2=High, 3=Normal, 4=Low)
            due_date: Due date (string, timestamp, or datetime)
            due_date_time: Whether the due date includes time
            time_estimate: Time estimate in milliseconds
            start_date: Start date (string, timestamp, or datetime)
            start_date_time: Whether the start date includes time
            notify_all: Notify all assignees
            parent: Parent task ID for subtasks
            links_to: Task ID to link this task to
            check_required_custom_fields: Check if required custom fields are filled
            custom_fields: List of custom field values
            custom_task_ids: Use custom task IDs
            team_id: Team ID when using custom task IDs
            points: Sprint points for the task
            group_assignees: List of group assignee IDs
            markdown_content: Markdown formatted description
            custom_item_id: Custom task type ID

        Returns:
            The created Task object
        """
        list_id = list_id or self._list_id
        if not list_id:
            raise ValueError("List ID must be provided")

        data: Dict[str, Any] = {"name": name}

        if description is not None:
            data["description"] = description
        if assignees is not None:
            data["assignees"] = [str(a) for a in assignees]
        if tags is not None:
            data["tags"] = [str(t) for t in tags]
        if status is not None:
            data["status"] = status
        if priority is not None:
            if isinstance(priority, Priority):
                data["priority"] = str(priority.value)
            else:
                data["priority"] = str(priority)
        if due_date is not None:
            data["due_date"] = str(convert_to_timestamp(due_date))
        if due_date_time is not None:
            data["due_date_time"] = str(due_date_time).lower()
        if time_estimate is not None:
            data["time_estimate"] = str(time_estimate)
        if start_date is not None:
            data["start_date"] = str(convert_to_timestamp(start_date))
        if start_date_time is not None:
            data["start_date_time"] = str(start_date_time).lower()
        if notify_all is not None:
            data["notify_all"] = str(notify_all).lower()
        if parent is not None:
            data["parent"] = parent
        if links_to is not None:
            data["links_to"] = links_to
        if check_required_custom_fields is not None:
            data["check_required_custom_fields"] = str(
                check_required_custom_fields
            ).lower()
        if custom_fields is not None:
            data["custom_fields"] = custom_fields
        if custom_task_ids is not None:
            data["custom_task_ids"] = str(custom_task_ids).lower()
        if team_id is not None:
            data["team_id"] = team_id
        if points is not None:
            data["points"] = str(points)
        if group_assignees is not None:
            data["group_assignees"] = group_assignees
        if markdown_content is not None:
            data["markdown_content"] = markdown_content
        if custom_item_id is not None:
            data["custom_item_id"] = custom_item_id

        response = await self._request("POST", f"list/{list_id}/task", data=data)
        return Task.model_validate(response)

    async def update_task(
        self,
        task_id: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[Union[int, Priority]] = None,
        due_date: Optional[Union[str, int, datetime]] = None,
        due_date_time: Optional[bool] = None,
        time_estimate: Optional[int] = None,
        start_date: Optional[Union[str, int, datetime]] = None,
        start_date_time: Optional[bool] = None,
        assignees: Optional[List[str]] = None,
        add_assignees: Optional[List[str]] = None,
        remove_assignees: Optional[List[str]] = None,
        group_assignees: Optional[Dict[str, List[str]]] = None,
        watchers: Optional[Dict[str, List[str]]] = None,
        archived: Optional[bool] = None,
        points: Optional[float] = None,
        markdown_content: Optional[str] = None,
        custom_item_id: Optional[int] = None,
    ) -> Task:
        """
        Update an existing task

        Args:
            task_id: ID of the task to update (uses the one set by task() if not provided)
            name: New task name
            description: New task description
            status: New task status
            priority: New priority level (1=Urgent, 2=High, 3=Normal, 4=Low)
            due_date: New due date (string, timestamp, or datetime)
            due_date_time: Whether the due date includes time
            time_estimate: New time estimate in milliseconds
            start_date: New start date (string, timestamp, or datetime)
            start_date_time: Whether the start date includes time
            assignees: Complete list of assignee IDs (replaces existing)
            add_assignees: List of assignee IDs to add
            remove_assignees: List of assignee IDs to remove
            group_assignees: Dict with 'add' and 'rem' lists for group assignees
            watchers: Dict with 'add' and 'rem' lists for watchers
            archived: Whether to archive the task
            points: New sprint points
            markdown_content: New markdown formatted description
            custom_item_id: New custom task type ID

        Returns:
            The updated Task object
        """
        task_id = task_id or self._task_id
        if not task_id:
            raise ValueError("Task ID must be provided")

        data = {}

        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description
        if status is not None:
            data["status"] = status
        if priority is not None:
            if isinstance(priority, Priority):
                data["priority"] = priority.value
            else:
                data["priority"] = priority
        if due_date is not None:
            data["due_date"] = str(convert_to_timestamp(due_date))
        if due_date_time is not None:
            data["due_date_time"] = str(due_date_time).lower()
        if time_estimate is not None:
            data["time_estimate"] = str(time_estimate)
        if start_date is not None:
            data["start_date"] = str(convert_to_timestamp(start_date))
        if start_date_time is not None:
            data["start_date_time"] = str(start_date_time).lower()
        if archived is not None:
            data["archived"] = str(archived).lower()
        if points is not None:
            data["points"] = str(points)
        if markdown_content is not None:
            data["markdown_content"] = markdown_content
        if custom_item_id is not None:
            data["custom_item_id"] = custom_item_id

        # Handle assignees
        if assignees is not None:
            data["assignees"] = assignees
        elif add_assignees or remove_assignees:
            data["assignees"] = {}
            if add_assignees:
                data["assignees"]["add"] = add_assignees
            if remove_assignees:
                data["assignees"]["rem"] = remove_assignees

        # Handle group assignees
        if group_assignees is not None:
            data["group_assignees"] = group_assignees

        # Handle watchers
        if watchers is not None:
            data["watchers"] = watchers

        response = await self._request("PUT", f"task/{task_id}", data=data)
        return Task.model_validate(response)

    async def delete_task(self, task_id: Optional[str] = None) -> bool:
        """Delete a task.

        Args:
            task_id: ID of the task to delete. If not provided, uses the task_id from the fluent interface.

        Returns:
            True if successful

        Raises:
            ResourceNotFound: If the task doesn't exist
            ValidationError: If the request data is invalid
            ClickUpError: For other API errors
        """
        task_id = task_id or self._task_id
        if not task_id:
            raise ValueError("task_id is required")

        try:
            response = await self._client.request(
                "DELETE",
                f"{self.base_url.rstrip('/')}/task/{task_id}",
                headers=self._get_headers(),
            )
            response.raise_for_status()
            return True
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ResourceNotFound(f"Task {task_id} not found", 404, {})
            elif e.response.status_code == 400:
                raise ValidationError(str(e), 400, {})
            else:
                raise ClickUpError(str(e), e.response.status_code, {})

    # Comment methods

    async def get_task_comments(self, task_id: Optional[str] = None) -> List[Comment]:
        """
        Get comments for a task

        Args:
            task_id: ID of the task (uses the one set by task() if not provided)

        Returns:
            List of Comment objects
        """
        task_id = task_id or self._task_id
        if not task_id:
            raise ValueError("Task ID must be provided")

        response = await self._request("GET", f"task/{task_id}/comment")
        return [
            Comment.model_validate(comment) for comment in response.get("comments", [])
        ]

    async def create_task_comment(
        self,
        comment_text: str,
        task_id: Optional[str] = None,
        assignee: Optional[str] = None,
        notify_all: bool = True,
    ) -> Comment:
        """Add a comment to a task.

        Args:
            comment_text: Text content of the comment
            task_id: ID of the task. If not provided, uses the task_id from the fluent interface.
            assignee: User ID to assign the comment to
            notify_all: Whether to notify all task assignees

        Returns:
            The created Comment object

        Raises:
            ResourceNotFound: If the task doesn't exist
            ValidationError: If the request data is invalid
            ClickUpError: For other API errors
        """
        task_id = task_id or self._task_id
        if not task_id:
            raise ValueError("task_id is required")

        data = {
            "comment_text": comment_text,
            "notify_all": notify_all,
        }

        if assignee:
            data["assignee"] = assignee

        response = await self._request("POST", f"task/{task_id}/comment", data=data)
        logger.debug(f"Comment response: {response}")  # Debug log

        # Handle the response format
        comment_data = response.copy()
        comment_data["comment_text"] = comment_text
        return Comment.model_validate(comment_data)

    # Checklist methods

    async def create_checklist(
        self,
        name: str,
        task_id: Optional[str] = None,
    ) -> Checklist:
        """
        Create a checklist in a task

        Args:
            name: Name of the checklist
            task_id: ID of the task (uses the one set by task() if not provided)

        Returns:
            The created Checklist object
        """
        task_id = task_id or self._task_id
        if not task_id:
            raise ValueError("Task ID must be provided")

        data = {"name": name}

        response = await self._request("POST", f"task/{task_id}/checklist", data=data)
        return Checklist.model_validate(response)

    async def create_checklist_item(
        self,
        checklist_id: str,
        name: str,
        assignee: Optional[str] = None,
    ) -> Checklist:
        """
        Add an item to a checklist

        Args:
            checklist_id: ID of the checklist
            name: Name of the checklist item
            assignee: User ID to assign the item to

        Returns:
            The updated Checklist object
        """
        data = {"name": name}

        if assignee:
            data["assignee"] = assignee

        response = await self._request(
            "POST", f"checklist/{checklist_id}/checklist_item", data=data
        )
        return Checklist.model_validate(response)

    # Time tracking methods

    async def start_timer(
        self,
        task_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        duration: Optional[int] = None,
    ) -> TimeEntry:
        """Start a timer for a task.

        Args:
            task_id: ID of the task. If not provided, uses the task_id from the fluent interface.
            workspace_id: ID of the workspace. If not provided, uses the workspace_id from the fluent interface.
            duration: Duration in milliseconds (optional)

        Returns:
            The created TimeEntry object

        Raises:
            ResourceNotFound: If the task or workspace doesn't exist
            ValidationError: If the request data is invalid
            ClickUpError: For other API errors
        """
        task_id = task_id or self._task_id
        workspace_id = workspace_id or self._workspace_id

        if not task_id:
            raise ValueError("task_id is required")
        if not workspace_id:
            raise ValueError("workspace_id is required")

        start = int(time.time() * 1000)  # Current time in milliseconds
        data = {
            "tid": task_id,
            "start": start,
        }
        if duration:
            data["duration"] = duration

        logger.debug(f"Starting timer with data: {data}")  # Debug log request data
        response = await self._request(
            "POST", f"team/{workspace_id}/time_entries", data=data
        )
        logger.debug(
            f"Time entry response type: {type(response)}"
        )  # Debug log response type
        logger.debug(
            f"Time entry response: {json.dumps(response, indent=2)}"
        )  # Debug log response content

        # Create TimeEntry object with the required fields
        entry = TimeEntry(
            id=str(response) if isinstance(response, (int, str)) else None,
            task_id=task_id,
            start=str(start),
            duration=str(duration) if duration else None,
            wid=workspace_id,
        )
        logger.debug(f"Created TimeEntry: {entry}")  # Debug log created entry
        return entry

    async def stop_timer(
        self,
        workspace_id: Optional[str] = None,
    ) -> TimeEntry:
        """
        Stop the currently running timer

        Args:
            workspace_id: ID of the workspace (uses the one set by workspace() if not provided)

        Returns:
            TimeEntry object for the stopped timer
        """
        workspace_id = workspace_id or self._workspace_id
        if not workspace_id:
            raise ValueError("Workspace ID must be provided")

        response = await self._request("POST", f"team/{workspace_id}/time_entries/stop")
        return TimeEntry.model_validate(response.get("data", {}))

    async def create_task_from_template(
        self,
        name: str,
        list_id: Optional[str] = None,
        template_id: Optional[str] = None,
    ) -> Task:
        """
        Create a new task using a task template

        Args:
            name: Name for the new task
            list_id: ID of the list (uses the one set by list() if not provided)
            template_id: ID of the template (uses the one set by template() if not provided)

        Returns:
            The created Task object
        """
        list_id = list_id or self._list_id
        if not list_id:
            raise ValueError("List ID must be provided")

        template_id = template_id or self._template_id
        if not template_id:
            raise ValueError("Template ID must be provided")

        data = {"name": name}
        response = await self._request(
            "POST", f"list/{list_id}/taskTemplate/{template_id}", data=data
        )
        return Task.model_validate(response)

    async def get_task_time_in_status(
        self,
        task_id: str,
        status: str,
        start_date: Optional[Union[str, int, datetime]] = None,
        end_date: Optional[Union[str, int, datetime]] = None,
    ) -> Dict[str, Any]:
        """
        Get time spent in a specific status for a task

        Args:
            task_id: ID of the task
            status: Status to get time for
            start_date: Start date filter (string, timestamp, or datetime)
            end_date: End date filter (string, timestamp, or datetime)

        Returns:
            Dictionary containing time spent in status
        """
        params = {"status": status}

        if start_date:
            params["start_date"] = str(convert_to_timestamp(start_date))

        if end_date:
            params["end_date"] = str(convert_to_timestamp(end_date))

        response = await self._request(
            "GET", f"task/{task_id}/time_in_status", params=params
        )
        return response.get("data", {})

    # Goal methods

    async def get_goals(
        self,
        workspace_id: Optional[str] = None,
        include_completed: bool = True,
    ) -> List[Goal]:
        """
        Get all goals in a workspace.

        Args:
            workspace_id: ID of the workspace (uses the one set by workspace() if not provided)
            include_completed: Whether to include completed goals

        Returns:
            List of Goal objects
        """
        workspace_id = workspace_id or self._workspace_id
        if not workspace_id:
            raise ValueError("workspace_id is required")

        params = {"include_completed": "true" if include_completed else "false"}
        response = await self._request(
            "GET", f"team/{workspace_id}/goal", params=params
        )

        # Log the raw response for debugging
        print(f"Raw Goals Response: {response}")

        # Handle both possible response structures
        goals_data = response.get("goals", [])
        if not goals_data and "goal" in response:
            goals_data = [response["goal"]]

        # Ensure each goal has a color
        for goal in goals_data:
            if "color" not in goal or goal["color"] is None:
                goal["color"] = "#000000"  # Default color

        return [Goal.model_validate(goal) for goal in goals_data]

    async def create_goal(
        self,
        workspace_id: str,
        name: str,
        due_date: Union[str, int, datetime],
        description: str = "",
        multiple_owners: bool = False,
        owners: Optional[List[str]] = None,
        color: Optional[str] = None,
    ) -> Goal:
        """Create a new goal in the specified workspace."""
        if not workspace_id:
            raise ValueError("workspace_id is required")

        # Convert due_date to millisecond timestamp
        if isinstance(due_date, datetime):
            due_date_ts = int(due_date.timestamp() * 1000)
        elif isinstance(due_date, str):
            try:
                due_date_ts = int(float(due_date) * 1000)
            except ValueError:
                # Try parsing as datetime string
                due_date_ts = int(datetime.fromisoformat(due_date).timestamp() * 1000)
        else:
            # Assume it's already a timestamp in milliseconds
            due_date_ts = int(due_date)

        data = {
            "name": name,
            "due_date": due_date_ts,
            "description": description,
            "multiple_owners": multiple_owners,
            "owners": owners or [],
            "color": color or "#000000",
        }

        response = await self._request("POST", f"team/{workspace_id}/goal", data=data)

        # Log the raw response for debugging
        print(f"Raw API Response: {response}")

        try:
            if "goal" in response:
                goal_data = response["goal"]
                # Add team_id if not present in response
                if "team_id" not in goal_data:
                    goal_data["team_id"] = workspace_id
                # Log the goal data being validated
                print(f"Goal Data for Validation: {goal_data}")
                return Goal.model_validate(goal_data)
            else:
                # Log the response structure when 'goal' key is missing
                print(f"Response keys: {response.keys()}")
                raise ClickUpError(f"Unexpected response format: {response}")
        except ValidationError as e:
            # Log validation errors
            print(f"Validation Error: {str(e)}")
            raise ClickUpError(f"Failed to validate goal data: {e}") from e

    async def get_goal(self, goal_id: str) -> Goal:
        """
        Get details of a specific goal.

        Args:
            goal_id: ID of the goal to fetch

        Returns:
            Goal object
        """
        response = await self._request("GET", f"goal/{goal_id}")
        if "goal" not in response:
            raise ClickUpError(
                "Unexpected response format from ClickUp API", response=response
            )
        return Goal.model_validate(response["goal"])

    async def update_goal(
        self,
        goal_id: str,
        name: Optional[str] = None,
        due_date: Optional[Union[str, int, datetime]] = None,
        description: Optional[str] = None,
        add_owners: Optional[List[str]] = None,
        rem_owners: Optional[List[str]] = None,
        color: Optional[str] = None,
    ) -> Goal:
        """
        Update an existing goal.

        Args:
            goal_id: ID of the goal to update
            name: New name for the goal
            due_date: New due date for the goal
            description: New description for the goal
            add_owners: List of user IDs to add as owners
            rem_owners: List of user IDs to remove as owners
            color: New color for the goal

        Returns:
            The updated Goal object
        """
        data = {}
        if name is not None:
            data["name"] = name
        if due_date is not None:
            data["due_date"] = str(convert_to_timestamp(due_date))
        if description is not None:
            data["description"] = description
        if add_owners is not None:
            data["add_owners"] = add_owners
        if rem_owners is not None:
            data["rem_owners"] = rem_owners
        if color is not None:
            data["color"] = color

        response = await self._request("PUT", f"goal/{goal_id}", data=data)
        if "goal" not in response:
            raise ClickUpError(
                "Unexpected response format from ClickUp API", response=response
            )
        return Goal.model_validate(response["goal"])

    async def delete_goal(self, goal_id: str) -> bool:
        """
        Delete a goal.

        Args:
            goal_id: ID of the goal to delete

        Returns:
            True if successful
        """
        await self._request("DELETE", f"goal/{goal_id}")
        return True

    async def create_key_result(
        self,
        goal_id: str,
        name: str,
        type: Union[str, KeyResultType],
        steps_start: int = 0,
        steps_end: int = 0,
        unit: str = "points",
        owners: Optional[List[str]] = None,
        task_ids: Optional[List[str]] = None,
        list_ids: Optional[List[str]] = None,
        note: Optional[str] = None,
    ) -> KeyResult:
        """
        Create a new key result for a goal.

        Args:
            goal_id: ID of the goal to add the key result to
            name: Name of the key result
            type: Type of the key result (number, percentage, currency, boolean, automatic)
            steps_start: Starting value for the key result
            steps_end: Target value for the key result
            unit: Unit of measurement (e.g., "points", "%", "USD")
            owners: List of user IDs who own this key result
            task_ids: List of task IDs linked to this key result
            list_ids: List of list IDs linked to this key result
            note: Note about the key result

        Returns:
            The created KeyResult object
        """
        data = {
            "name": name,
            "type": type.value if isinstance(type, KeyResultType) else type,
            "steps_start": steps_start,
            "steps_end": steps_end,
            "unit": unit,
            "owners": owners or [],
            "task_ids": task_ids or [],
            "list_ids": list_ids or [],
        }
        if note is not None:
            data["note"] = note

        response = await self._request("POST", f"goal/{goal_id}/key_result", data=data)
        print("Raw Key Result Response:", response)

        if "key_result" not in response:
            raise ClickUpError("Unexpected response format: missing 'key_result' key")

        # Merge the request data with the response data to ensure all required fields are present
        key_result_data = response["key_result"]
        key_result_data.update(
            {
                "name": name,
                "type": type.value if isinstance(type, KeyResultType) else type,
                "steps_start": steps_start,
                "steps_end": steps_end,
                "unit": unit,
                "owners": owners or [],
                "task_ids": task_ids or [],
                "list_ids": list_ids or [],
            }
        )

        try:
            return KeyResult.model_validate(key_result_data)
        except ValidationError as e:
            print("Key Result Data for Validation:", key_result_data)
            print("Validation Error:", str(e))
            raise

    async def update_key_result(
        self,
        key_result_id: str,
        name: Optional[str] = None,
        type: Optional[Union[str, KeyResultType]] = None,
        steps_start: Optional[int] = None,
        steps_end: Optional[int] = None,
        steps_current: Optional[int] = None,
        unit: Optional[str] = None,
        owners: Optional[List[str]] = None,
        task_ids: Optional[List[str]] = None,
        list_ids: Optional[List[str]] = None,
        note: Optional[str] = None,
    ) -> KeyResult:
        """
        Update an existing key result.

        Args:
            key_result_id: ID of the key result to update
            name: New name for the key result
            type: New type for the key result
            steps_start: New starting value
            steps_end: New target value
            steps_current: Current progress value
            unit: New unit of measurement
            owners: New list of owner user IDs
            task_ids: New list of linked task IDs
            list_ids: New list of linked list IDs
            note: Note about the update

        Returns:
            The updated KeyResult object
        """
        data = {}
        if name is not None:
            data["name"] = name
        if type is not None:
            data["type"] = type.value if isinstance(type, KeyResultType) else type
        if steps_start is not None:
            data["steps_start"] = steps_start
        if steps_end is not None:
            data["steps_end"] = steps_end
        if steps_current is not None:
            data["steps_current"] = steps_current
        if unit is not None:
            data["unit"] = unit
        if owners is not None:
            data["owners"] = owners
        if task_ids is not None:
            data["task_ids"] = task_ids
        if list_ids is not None:
            data["list_ids"] = list_ids
        if note is not None:
            data["note"] = note

        response = await self._request("PUT", f"key_result/{key_result_id}", data=data)
        print("Raw Key Result Response:", response)

        if "key_result" not in response:
            raise ClickUpError("Unexpected response format: missing 'key_result' key")

        # Merge the request data with the response data to ensure all required fields are present
        key_result_data = response["key_result"]
        if name is not None:
            key_result_data["name"] = name
        if type is not None:
            key_result_data["type"] = (
                type.value if isinstance(type, KeyResultType) else type
            )
        if unit is not None:
            key_result_data["unit"] = unit
        if steps_start is not None:
            key_result_data["steps_start"] = steps_start
        if steps_end is not None:
            key_result_data["steps_end"] = steps_end
        if steps_current is not None:
            key_result_data["steps_current"] = steps_current
        if owners is not None:
            key_result_data["owners"] = owners
        if task_ids is not None:
            key_result_data["task_ids"] = task_ids
        if list_ids is not None:
            key_result_data["list_ids"] = list_ids

        try:
            return KeyResult.model_validate(key_result_data)
        except ValidationError as e:
            print("Key Result Data for Validation:", key_result_data)
            print("Validation Error:", str(e))
            raise

    async def delete_key_result(self, key_result_id: str) -> bool:
        """
        Delete a key result.

        Args:
            key_result_id: ID of the key result to delete

        Returns:
            True if successful
        """
        await self._request("DELETE", f"key_result/{key_result_id}")
        return True
