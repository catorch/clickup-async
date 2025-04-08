"""
View resources for ClickUp API.

This module contains resource classes for interacting with view-related endpoints.
"""

import logging
from typing import Any, Dict, List, Literal, Optional, Union

from ..exceptions import ResourceNotFound, ValidationError
from ..models.view import View
from .base import BaseResource

logger = logging.getLogger("clickup")


class ViewResource(BaseResource):
    """View-related API endpoints."""

    async def get_workspace_views(
        self, workspace_id: Optional[str] = None
    ) -> List[View]:
        """
        Get all views at the workspace level.

        Args:
            workspace_id: ID of the workspace (uses the one set in the client context if not provided)

        Returns:
            List of View objects

        Raises:
            ValueError: If workspace_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the workspace doesn't exist
            ClickUpError: For other API errors
        """
        workspace_id = self._get_context_id("_workspace_id", workspace_id)
        if not workspace_id:
            raise ValueError("Workspace ID must be provided")

        response = await self._request("GET", f"team/{workspace_id}/view")

        # API returns views in a list under the "views" key
        views_data = response.get("views", [])
        return [View.model_validate(view) for view in views_data]

    async def create_workspace_view(
        self,
        name: str,
        type: Literal[
            "list",
            "board",
            "calendar",
            "table",
            "timeline",
            "workload",
            "activity",
            "map",
            "conversation",
            "gantt",
        ],
        workspace_id: Optional[str] = None,
        grouping: Optional[Dict[str, Any]] = None,
        divide: Optional[Dict[str, Any]] = None,
        sorting: Optional[Dict[str, Any]] = None,
        filters: Optional[Dict[str, Any]] = None,
        columns: Optional[Dict[str, Any]] = None,
        team_sidebar: Optional[Dict[str, Any]] = None,
        settings: Optional[Dict[str, Any]] = None,
    ) -> View:
        """
        Create a new view at the workspace level.

        Args:
            name: Name of the view
            type: Type of view (list, board, calendar, etc.)
            workspace_id: ID of the workspace (uses the one set in the client context if not provided)
            grouping: Grouping settings
            divide: Divide settings
            sorting: Sorting settings
            filters: Filter settings
            columns: Column settings (note: custom fields added at workspace level will be added to all tasks)
            team_sidebar: Team sidebar settings
            settings: View settings

        Returns:
            The created View object

        Raises:
            ValueError: If workspace_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the workspace doesn't exist
            ValidationError: If the request data is invalid
            ClickUpError: For other API errors
        """
        workspace_id = self._get_context_id("_workspace_id", workspace_id)
        if not workspace_id:
            raise ValueError("Workspace ID must be provided")

        data: Dict[str, Any] = {
            "name": name,
            "type": type,
        }

        # Add optional parameters if provided
        if grouping is not None:
            data["grouping"] = grouping
        if divide is not None:
            data["divide"] = divide
        if sorting is not None:
            data["sorting"] = sorting
        if filters is not None:
            data["filters"] = filters
        if columns is not None:
            data["columns"] = columns
        if team_sidebar is not None:
            data["team_sidebar"] = team_sidebar
        if settings is not None:
            data["settings"] = settings

        response = await self._request("POST", f"team/{workspace_id}/view", data=data)
        # API returns the view object nested under a "view" key
        return View.model_validate(response.get("view", {}))

    async def get_space_views(self, space_id: str) -> List[View]:
        """
        Get all views at the space level.

        Args:
            space_id: ID of the space

        Returns:
            List of View objects

        Raises:
            AuthenticationError: If authentication fails
            ResourceNotFound: If the space doesn't exist
            ClickUpError: For other API errors
        """
        response = await self._request("GET", f"space/{space_id}/view")

        # API returns views in a list under the "views" key
        views_data = response.get("views", [])
        return [View.model_validate(view) for view in views_data]

    async def create_space_view(
        self,
        name: str,
        type: Literal[
            "list",
            "board",
            "calendar",
            "table",
            "timeline",
            "workload",
            "activity",
            "map",
            "conversation",
            "gantt",
        ],
        space_id: str,
        grouping: Optional[Dict[str, Any]] = None,
        divide: Optional[Dict[str, Any]] = None,
        sorting: Optional[Dict[str, Any]] = None,
        filters: Optional[Dict[str, Any]] = None,
        columns: Optional[Dict[str, Any]] = None,
        team_sidebar: Optional[Dict[str, Any]] = None,
        settings: Optional[Dict[str, Any]] = None,
    ) -> View:
        """
        Create a new view at the space level.

        Args:
            name: Name of the view
            type: Type of view (list, board, calendar, etc.)
            space_id: ID of the space
            grouping: Grouping settings
            divide: Divide settings
            sorting: Sorting settings
            filters: Filter settings
            columns: Column settings
            team_sidebar: Team sidebar settings
            settings: View settings

        Returns:
            The created View object

        Raises:
            AuthenticationError: If authentication fails
            ResourceNotFound: If the space doesn't exist
            ValidationError: If the request data is invalid
            ClickUpError: For other API errors
        """
        data: Dict[str, Any] = {
            "name": name,
            "type": type,
        }

        # Add optional parameters if provided
        if grouping is not None:
            data["grouping"] = grouping
        if divide is not None:
            data["divide"] = divide
        if sorting is not None:
            data["sorting"] = sorting
        if filters is not None:
            data["filters"] = filters
        if columns is not None:
            data["columns"] = columns
        if team_sidebar is not None:
            data["team_sidebar"] = team_sidebar
        if settings is not None:
            data["settings"] = settings

        response = await self._request("POST", f"space/{space_id}/view", data=data)
        # API returns the view object nested under a "view" key
        return View.model_validate(response.get("view", {}))

    async def get_folder_views(self, folder_id: str) -> List[View]:
        """
        Get all views at the folder level.

        Args:
            folder_id: ID of the folder

        Returns:
            List of View objects

        Raises:
            AuthenticationError: If authentication fails
            ResourceNotFound: If the folder doesn't exist
            ClickUpError: For other API errors
        """
        response = await self._request("GET", f"folder/{folder_id}/view")

        # API returns views in a list under the "views" key
        views_data = response.get("views", [])
        return [View.model_validate(view) for view in views_data]

    async def create_folder_view(
        self,
        name: str,
        type: Literal[
            "list",
            "board",
            "calendar",
            "table",
            "timeline",
            "workload",
            "activity",
            "map",
            "conversation",
            "gantt",
        ],
        folder_id: str,
        grouping: Optional[Dict[str, Any]] = None,
        divide: Optional[Dict[str, Any]] = None,
        sorting: Optional[Dict[str, Any]] = None,
        filters: Optional[Dict[str, Any]] = None,
        columns: Optional[Dict[str, Any]] = None,
        team_sidebar: Optional[Dict[str, Any]] = None,
        settings: Optional[Dict[str, Any]] = None,
    ) -> View:
        """
        Create a new view at the folder level.

        Args:
            name: Name of the view
            type: Type of view (list, board, calendar, etc.)
            folder_id: ID of the folder
            grouping: Grouping settings
            divide: Divide settings
            sorting: Sorting settings
            filters: Filter settings
            columns: Column settings
            team_sidebar: Team sidebar settings
            settings: View settings

        Returns:
            The created View object

        Raises:
            AuthenticationError: If authentication fails
            ResourceNotFound: If the folder doesn't exist
            ValidationError: If the request data is invalid
            ClickUpError: For other API errors
        """
        data: Dict[str, Any] = {
            "name": name,
            "type": type,
        }

        # Add optional parameters if provided
        if grouping is not None:
            data["grouping"] = grouping
        if divide is not None:
            data["divide"] = divide
        if sorting is not None:
            data["sorting"] = sorting
        if filters is not None:
            data["filters"] = filters
        if columns is not None:
            data["columns"] = columns
        if team_sidebar is not None:
            data["team_sidebar"] = team_sidebar
        if settings is not None:
            data["settings"] = settings

        response = await self._request("POST", f"folder/{folder_id}/view", data=data)
        # API returns the view object nested under a "view" key
        return View.model_validate(response.get("view", {}))

    async def get_list_views(self, list_id: str) -> Dict[str, List[View]]:
        """
        Get all views at the list level.

        Args:
            list_id: ID of the list

        Returns:
            Dictionary with "views" (List[View]) and "required_views" (List[str]) keys

        Raises:
            AuthenticationError: If authentication fails
            ResourceNotFound: If the list doesn't exist
            ClickUpError: For other API errors
        """
        response = await self._request("GET", f"list/{list_id}/view")

        result: Dict[str, List[View]] = {}

        # Regular views
        views_data = response.get("views", [])
        result["views"] = [View.model_validate(view) for view in views_data]

        # Required views (if present) - API returns list of strings
        required_views_data = response.get("required_views", [])
        result["required_views"] = required_views_data  # Store as list of strings

        return result

    async def create_list_view(
        self,
        name: str,
        type: Literal[
            "list",
            "board",
            "calendar",
            "table",
            "timeline",
            "workload",
            "activity",
            "map",
            "conversation",
            "gantt",
        ],
        list_id: str,
        grouping: Optional[Dict[str, Any]] = None,
        divide: Optional[Dict[str, Any]] = None,
        sorting: Optional[Dict[str, Any]] = None,
        filters: Optional[Dict[str, Any]] = None,
        columns: Optional[Dict[str, Any]] = None,
        team_sidebar: Optional[Dict[str, Any]] = None,
        settings: Optional[Dict[str, Any]] = None,
    ) -> View:
        """
        Create a new view at the list level.

        Args:
            name: Name of the view
            type: Type of view (list, board, calendar, etc.)
            list_id: ID of the list
            grouping: Grouping settings
            divide: Divide settings
            sorting: Sorting settings
            filters: Filter settings
            columns: Column settings
            team_sidebar: Team sidebar settings
            settings: View settings

        Returns:
            The created View object

        Raises:
            AuthenticationError: If authentication fails
            ResourceNotFound: If the list doesn't exist
            ValidationError: If the request data is invalid
            ClickUpError: For other API errors
        """
        data: Dict[str, Any] = {
            "name": name,
            "type": type,
        }

        # Add optional parameters if provided
        if grouping is not None:
            data["grouping"] = grouping
        if divide is not None:
            data["divide"] = divide
        if sorting is not None:
            data["sorting"] = sorting
        if filters is not None:
            data["filters"] = filters
        if columns is not None:
            data["columns"] = columns
        if team_sidebar is not None:
            data["team_sidebar"] = team_sidebar
        if settings is not None:
            data["settings"] = settings

        response = await self._request("POST", f"list/{list_id}/view", data=data)
        # API returns the view object nested under a "view" key
        return View.model_validate(response.get("view", {}))

    async def get_view(self, view_id: str) -> View:
        """
        Get information about a specific view.

        Args:
            view_id: ID of the view

        Returns:
            View object

        Raises:
            AuthenticationError: If authentication fails
            ResourceNotFound: If the view doesn't exist
            ClickUpError: For other API errors
        """
        response = await self._request("GET", f"view/{view_id}")
        # API returns the view object nested under a "view" key
        view_data = response.get("view")
        if not view_data or not isinstance(view_data, dict):
            raise ResourceNotFound(
                f"View with ID '{view_id}' not found or response format unexpected: {response}"
            )
        return View.model_validate(view_data)

    async def update_view(
        self,
        view_id: str,
        name: Optional[str] = None,
        type: Optional[
            Literal[
                "list",
                "board",
                "calendar",
                "table",
                "timeline",
                "workload",
                "activity",
                "map",
                "conversation",
                "gantt",
            ]
        ] = None,
        parent: Optional[Dict[str, Any]] = None,
        grouping: Optional[Dict[str, Any]] = None,
        divide: Optional[Dict[str, Any]] = None,
        sorting: Optional[Dict[str, Any]] = None,
        filters: Optional[Dict[str, Any]] = None,
        columns: Optional[Dict[str, Any]] = None,
        team_sidebar: Optional[Dict[str, Any]] = None,
        settings: Optional[Dict[str, Any]] = None,
    ) -> View:
        """
        Update an existing view.

        Args:
            view_id: ID of the view
            name: New name for the view
            type: New type for the view
            parent: New parent specification (ID and type)
            grouping: New grouping settings
            divide: New divide settings
            sorting: New sorting settings
            filters: New filter settings
            columns: New column settings
            team_sidebar: New team sidebar settings
            settings: New view settings

        Returns:
            The updated View object

        Raises:
            AuthenticationError: If authentication fails
            ResourceNotFound: If the view doesn't exist
            ValidationError: If the request data is invalid
            ClickUpError: For other API errors
        """
        # 1. Fetch the current view state
        current_view = await self.get_view(view_id)

        # 2. Convert current view to dict (ensure nested models are dicts)
        # Use include to ensure all potentially required fields are present initially
        data = current_view.model_dump(
            mode="json", exclude_unset=False, exclude_none=False
        )

        # Remove fields that should not be sent back or are read-only
        data.pop("id", None)
        data.pop("url", None)
        data.pop("created", None)
        data.pop("user", None)
        data.pop("protected", None)
        data.pop("required", None)

        # 3. Merge provided updates into the data dict
        update_payload: Dict[str, Any] = {}
        if name is not None:
            update_payload["name"] = name
        if type is not None:
            update_payload["type"] = type
        if parent is not None:
            update_payload["parent"] = parent
        if grouping is not None:
            update_payload["grouping"] = grouping
        if divide is not None:
            update_payload["divide"] = divide
        if sorting is not None:
            update_payload["sorting"] = sorting
        if filters is not None:
            update_payload["filters"] = filters
        if columns is not None:
            update_payload["columns"] = columns
        if team_sidebar is not None:
            update_payload["team_sidebar"] = team_sidebar
        if settings is not None:
            update_payload["settings"] = settings

        # Overwrite fetched data with user provided updates
        data.update(update_payload)

        # 4. Send the complete data payload
        response = await self._request("PUT", f"view/{view_id}", data=data)
        # API returns the view object nested under a "view" key
        return View.model_validate(response.get("view", {}))

    async def delete_view(self, view_id: str) -> bool:
        """
        Delete a view.

        Args:
            view_id: ID of the view

        Returns:
            True if successful

        Raises:
            AuthenticationError: If authentication fails
            ResourceNotFound: If the view doesn't exist
            ClickUpError: For other API errors
        """
        await self._request("DELETE", f"view/{view_id}")
        return True

    async def get_view_tasks(self, view_id: str, page: int = 0) -> List[Dict[str, Any]]:
        """
        Get all visible tasks in a view.

        Args:
            view_id: ID of the view
            page: Page number for pagination

        Returns:
            List of task objects

        Raises:
            AuthenticationError: If authentication fails
            ResourceNotFound: If the view doesn't exist
            ClickUpError: For other API errors
        """
        response = await self._request(
            "GET", f"view/{view_id}/task", params={"page": page}
        )

        # Return the tasks data
        # Note: We're returning the raw task dictionaries here since we don't know
        # which task model to use for validation (it depends on the view type)
        return response.get("tasks", [])
