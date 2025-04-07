"""
Time tracking resources for ClickUp API.

This module contains resource classes for interacting with time tracking-related endpoints.
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional, Union

from ..models import TimeEntry
from .base import BaseResource

logger = logging.getLogger("clickup")


class TimeTrackingResource(BaseResource):
    """Time tracking-related API endpoints."""

    async def start_timer(
        self,
        task_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        duration: Optional[int] = None,
    ) -> TimeEntry:
        """
        Start a timer for a task.

        Args:
            task_id: ID of the task (uses the one set in the client context if not provided)
            workspace_id: ID of the workspace (uses the one set in the client context if not provided)
            duration: Duration in milliseconds (optional)

        Returns:
            The created TimeEntry object

        Raises:
            ValueError: If task_id or workspace_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the task or workspace doesn't exist
            ValidationError: If the request data is invalid
            ClickUpError: For other API errors
        """
        task_id = self._get_context_id("_task_id", task_id)
        workspace_id = self._get_context_id("_workspace_id", workspace_id)

        if not task_id:
            raise ValueError("Task ID must be provided")
        if not workspace_id:
            raise ValueError("Workspace ID must be provided")

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
            f"Time entry response: {json.dumps(response, indent=2) if isinstance(response, dict) else response}"
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
        Stop the currently running timer.

        Args:
            workspace_id: ID of the workspace (uses the one set in the client context if not provided)

        Returns:
            TimeEntry object for the stopped timer

        Raises:
            ValueError: If workspace_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the workspace doesn't exist
            ClickUpError: For other API errors
        """
        workspace_id = self._get_context_id("_workspace_id", workspace_id)
        if not workspace_id:
            raise ValueError("Workspace ID must be provided")

        response = await self._request("POST", f"team/{workspace_id}/time_entries/stop")
        return TimeEntry.model_validate(response.get("data", {}))

    async def get_entries(
        self,
        workspace_id: Optional[str] = None,
        start_date: Optional[int] = None,
        end_date: Optional[int] = None,
        assignee: Optional[str] = None,
        include_task_tags: bool = False,
        include_location_names: bool = False,
        space_id: Optional[str] = None,
        folder_id: Optional[str] = None,
        list_id: Optional[str] = None,
        task_id: Optional[str] = None,
        custom_task_ids: bool = False,
        team_id: Optional[str] = None,
    ) -> list:
        """
        Get time entries for a workspace.

        Args:
            workspace_id: ID of the workspace (uses the one set in the client context if not provided)
            start_date: Start date timestamp in milliseconds
            end_date: End date timestamp in milliseconds
            assignee: Filter by assignee ID
            include_task_tags: Include task tags in response
            include_location_names: Include location names in response
            space_id: Filter by space ID
            folder_id: Filter by folder ID
            list_id: Filter by list ID
            task_id: Filter by task ID
            custom_task_ids: Whether to use custom task IDs
            team_id: Team ID (required if using custom task IDs)

        Returns:
            List of TimeEntry objects

        Raises:
            ValueError: If workspace_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the workspace doesn't exist
            ClickUpError: For other API errors
        """
        workspace_id = self._get_context_id("_workspace_id", workspace_id)
        if not workspace_id:
            raise ValueError("Workspace ID must be provided")

        params = {}

        if start_date is not None:
            params["start_date"] = str(start_date)
        if end_date is not None:
            params["end_date"] = str(end_date)
        if assignee is not None:
            params["assignee"] = assignee
        if include_task_tags:
            params["include_task_tags"] = str(include_task_tags).lower()
        if include_location_names:
            params["include_location_names"] = str(include_location_names).lower()
        if space_id:
            params["space_id"] = space_id
        if folder_id:
            params["folder_id"] = folder_id
        if list_id:
            params["list_id"] = list_id
        if task_id:
            params["task_id"] = task_id
        if custom_task_ids:
            params["custom_task_ids"] = str(custom_task_ids).lower()
            if team_id:
                params["team_id"] = team_id

        response = await self._request(
            "GET", f"team/{workspace_id}/time_entries", params=params
        )

        return [TimeEntry.model_validate(entry) for entry in response.get("data", [])]

    async def create_entry(
        self,
        workspace_id: Optional[str] = None,
        description: str = "",
        task_id: Optional[str] = None,
        start: Optional[int] = None,
        duration: Optional[int] = None,
        billable: bool = False,
        tags: Optional[list] = None,
    ) -> TimeEntry:
        """
        Create a new time entry manually.

        Args:
            workspace_id: ID of the workspace (uses the one set in the client context if not provided)
            description: Description of the time entry
            task_id: ID of the task (uses the one set in the client context if not provided)
            start: Start timestamp in milliseconds
            duration: Duration in milliseconds
            billable: Whether the time entry is billable
            tags: List of tags

        Returns:
            The created TimeEntry object

        Raises:
            ValueError: If workspace_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the workspace doesn't exist
            ValidationError: If the request data is invalid
            ClickUpError: For other API errors
        """
        workspace_id = self._get_context_id("_workspace_id", workspace_id)
        task_id = self._get_context_id("_task_id", task_id)

        if not workspace_id:
            raise ValueError("Workspace ID must be provided")

        # Default to current time if not provided
        if start is None:
            start = int(time.time() * 1000)

        data = {
            "description": description,
            "start": start,
            "billable": billable,
        }

        if task_id:
            data["tid"] = task_id
        if duration:
            data["duration"] = duration
        if tags:
            data["tags"] = tags

        response = await self._request(
            "POST", f"team/{workspace_id}/time_entries", data=data
        )

        return TimeEntry.model_validate(response)

    async def update_entry(
        self,
        time_entry_id: str,
        workspace_id: Optional[str] = None,
        description: Optional[str] = None,
        task_id: Optional[str] = None,
        start: Optional[int] = None,
        duration: Optional[int] = None,
        billable: Optional[bool] = None,
        tags: Optional[list] = None,
    ) -> TimeEntry:
        """
        Update an existing time entry.

        Args:
            time_entry_id: ID of the time entry to update
            workspace_id: ID of the workspace (uses the one set in the client context if not provided)
            description: New description for the time entry
            task_id: New task ID
            start: New start timestamp in milliseconds
            duration: New duration in milliseconds
            billable: Whether the time entry is billable
            tags: New list of tags

        Returns:
            The updated TimeEntry object

        Raises:
            ValueError: If workspace_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the workspace or time entry doesn't exist
            ValidationError: If the request data is invalid
            ClickUpError: For other API errors
        """
        workspace_id = self._get_context_id("_workspace_id", workspace_id)
        if not workspace_id:
            raise ValueError("Workspace ID must be provided")

        data = {}

        if description is not None:
            data["description"] = description
        if task_id is not None:
            data["tid"] = task_id
        if start is not None:
            data["start"] = start
        if duration is not None:
            data["duration"] = duration
        if billable is not None:
            data["billable"] = billable
        if tags is not None:
            data["tags"] = tags

        response = await self._request(
            "PUT", f"team/{workspace_id}/time_entries/{time_entry_id}", data=data
        )

        return TimeEntry.model_validate(response)

    async def delete_entry(
        self,
        time_entry_id: str,
        workspace_id: Optional[str] = None,
    ) -> bool:
        """
        Delete a time entry.

        Args:
            time_entry_id: ID of the time entry to delete
            workspace_id: ID of the workspace (uses the one set in the client context if not provided)

        Returns:
            True if successful

        Raises:
            ValueError: If workspace_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the workspace or time entry doesn't exist
            ClickUpError: For other API errors
        """
        workspace_id = self._get_context_id("_workspace_id", workspace_id)
        if not workspace_id:
            raise ValueError("Workspace ID must be provided")

        await self._request(
            "DELETE", f"team/{workspace_id}/time_entries/{time_entry_id}"
        )
        return True

    async def get_entry(
        self,
        time_entry_id: str,
        workspace_id: Optional[str] = None,
        include_task_tags: bool = False,
        include_location_names: bool = False,
    ) -> TimeEntry:
        """
        Get a single time entry by ID.

        Args:
            time_entry_id: ID of the time entry
            workspace_id: ID of the workspace (uses the one set in the client context if not provided)
            include_task_tags: Include task tags in response
            include_location_names: Include location names in response

        Returns:
            TimeEntry object

        Raises:
            ValueError: If workspace_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the time entry or workspace doesn't exist
            ClickUpError: For other API errors
        """
        workspace_id = self._get_context_id("_workspace_id", workspace_id)
        if not workspace_id:
            raise ValueError("Workspace ID must be provided")

        params = {}
        if include_task_tags:
            params["include_task_tags"] = str(include_task_tags).lower()
        if include_location_names:
            params["include_location_names"] = str(include_location_names).lower()

        response = await self._request(
            "GET", f"team/{workspace_id}/time_entries/{time_entry_id}", params=params
        )
        return TimeEntry.model_validate(response)

    async def get_entry_history(
        self,
        time_entry_id: str,
        workspace_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get the history of changes for a time entry.

        Args:
            time_entry_id: ID of the time entry
            workspace_id: ID of the workspace (uses the one set in the client context if not provided)

        Returns:
            List of history entries

        Raises:
            ValueError: If workspace_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the time entry or workspace doesn't exist
            ClickUpError: For other API errors
        """
        workspace_id = self._get_context_id("_workspace_id", workspace_id)
        if not workspace_id:
            raise ValueError("Workspace ID must be provided")

        response = await self._request(
            "GET", f"team/{workspace_id}/time_entries/{time_entry_id}/history"
        )
        return response.get("data", [])

    async def get_running_entry(
        self,
        workspace_id: Optional[str] = None,
        assignee: Optional[str] = None,
    ) -> Optional[TimeEntry]:
        """
        Get the currently running time entry for a user.

        Args:
            workspace_id: ID of the workspace (uses the one set in the client context if not provided)
            assignee: User ID to check for running timer (defaults to authenticated user)

        Returns:
            TimeEntry object if a timer is running, None otherwise

        Raises:
            ValueError: If workspace_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the workspace doesn't exist
            ClickUpError: For other API errors
        """
        workspace_id = self._get_context_id("_workspace_id", workspace_id)
        if not workspace_id:
            raise ValueError("Workspace ID must be provided")

        params = {}
        if assignee:
            params["assignee"] = assignee

        try:
            response = await self._request(
                "GET", f"team/{workspace_id}/time_entries/current", params=params
            )
            return TimeEntry.model_validate(response)
        except Exception as e:
            logger.debug(f"No running timer found: {e}")
            return None

    async def remove_tags(
        self,
        time_entry_ids: List[str],
        tags: List[Dict[str, str]],
        workspace_id: Optional[str] = None,
    ) -> bool:
        """
        Remove tags from time entries.

        Args:
            time_entry_ids: List of time entry IDs
            tags: List of tag objects to remove
            workspace_id: ID of the workspace (uses the one set in the client context if not provided)

        Returns:
            True if successful

        Raises:
            ValueError: If workspace_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the workspace doesn't exist
            ClickUpError: For other API errors
        """
        workspace_id = self._get_context_id("_workspace_id", workspace_id)
        if not workspace_id:
            raise ValueError("Workspace ID must be provided")

        data = {
            "time_entry_ids": time_entry_ids,
            "tags": tags,
        }

        await self._request(
            "DELETE", f"team/{workspace_id}/time_entries/tags", data=data
        )
        return True

    async def get_all_tags(
        self,
        workspace_id: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """
        Get all time entry tags in a workspace.

        Args:
            workspace_id: ID of the workspace (uses the one set in the client context if not provided)

        Returns:
            List of tag objects

        Raises:
            ValueError: If workspace_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the workspace doesn't exist
            ClickUpError: For other API errors
        """
        workspace_id = self._get_context_id("_workspace_id", workspace_id)
        if not workspace_id:
            raise ValueError("Workspace ID must be provided")

        response = await self._request("GET", f"team/{workspace_id}/time_entries/tags")
        return response.get("data", [])

    async def add_tags(
        self,
        time_entry_ids: List[str],
        tags: List[Dict[str, str]],
        workspace_id: Optional[str] = None,
    ) -> bool:
        """
        Add tags to time entries.

        Args:
            time_entry_ids: List of time entry IDs
            tags: List of tag objects to add
            workspace_id: ID of the workspace (uses the one set in the client context if not provided)

        Returns:
            True if successful

        Raises:
            ValueError: If workspace_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the workspace doesn't exist
            ClickUpError: For other API errors
        """
        workspace_id = self._get_context_id("_workspace_id", workspace_id)
        if not workspace_id:
            raise ValueError("Workspace ID must be provided")

        data = {
            "time_entry_ids": time_entry_ids,
            "tags": tags,
        }

        await self._request("POST", f"team/{workspace_id}/time_entries/tags", data=data)
        return True

    async def update_tag(
        self,
        name: str,
        new_name: str,
        tag_bg: str,
        tag_fg: str,
        workspace_id: Optional[str] = None,
    ) -> bool:
        """
        Update a time entry tag's properties.

        Args:
            name: Current tag name
            new_name: New tag name
            tag_bg: Background color for the tag
            tag_fg: Foreground color for the tag
            workspace_id: ID of the workspace (uses the one set in the client context if not provided)

        Returns:
            True if successful

        Raises:
            ValueError: If workspace_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the workspace doesn't exist
            ClickUpError: For other API errors
        """
        workspace_id = self._get_context_id("_workspace_id", workspace_id)
        if not workspace_id:
            raise ValueError("Workspace ID must be provided")

        data = {
            "name": name,
            "new_name": new_name,
            "tag_bg": tag_bg,
            "tag_fg": tag_fg,
        }

        await self._request("PUT", f"team/{workspace_id}/time_entries/tags", data=data)
        return True
