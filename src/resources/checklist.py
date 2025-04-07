"""
Checklist resources for ClickUp API.

This module contains resource classes for interacting with checklist-related endpoints.
"""

from typing import Any, Dict, Optional

from ..models import Checklist
from .base import BaseResource


class ChecklistResource(BaseResource):
    """Checklist-related API endpoints."""

    async def create(
        self,
        name: str,
        task_id: Optional[str] = None,
        custom_task_ids: Optional[bool] = None,
        team_id: Optional[int] = None,
    ) -> Checklist:
        """
        Create a checklist in a task.

        Args:
            name: Name of the checklist
            task_id: ID of the task (uses the one set in the client context if not provided)
            custom_task_ids: If true, reference task by custom task ID.
            team_id: Workspace ID required when using custom_task_ids.

        Returns:
            The created Checklist object

        Raises:
            ValueError: If task_id is not provided and not set in context, or if
                        custom_task_ids is true but team_id is missing.
            AuthenticationError: If authentication fails
            ResourceNotFound: If the task doesn't exist
            ValidationError: If the request data is invalid
            ClickUpError: For other API errors
        """
        task_id = self._get_context_id("_task_id", task_id)
        if not task_id:
            raise ValueError("Task ID must be provided")

        if custom_task_ids and team_id is None:
            raise ValueError("team_id is required when custom_task_ids is true")

        data = {"name": name}
        params = {}
        if custom_task_ids is not None:
            params["custom_task_ids"] = str(custom_task_ids).lower()
            if team_id is not None:
                params["team_id"] = team_id

        response = await self._request(
            "POST", f"task/{task_id}/checklist", data=data, params=params
        )
        return Checklist.model_validate(response.get("checklist", {}))

    async def create_item(
        self,
        checklist_id: str,
        name: str,
        assignee: Optional[int] = None,
    ) -> Checklist:
        """
        Add an item to a checklist.

        Args:
            checklist_id: ID of the checklist
            name: Name of the checklist item
            assignee: User ID (int) to assign the item to

        Returns:
            The updated Checklist object containing the new item

        Raises:
            AuthenticationError: If authentication fails
            ResourceNotFound: If the checklist doesn't exist
            ValidationError: If the request data is invalid
            ClickUpError: For other API errors
        """
        data: Dict[str, Any] = {"name": name}

        if assignee:
            data["assignee"] = assignee

        response = await self._request(
            "POST", f"checklist/{checklist_id}/checklist_item", data=data
        )
        # Response contains the updated checklist
        return Checklist.model_validate(response.get("checklist", {}))

    async def update_item(
        self,
        checklist_id: str,
        item_id: str,
        name: Optional[str] = None,
        resolved: Optional[bool] = None,
        assignee: Optional[int | None] = None,
        parent: Optional[str | None] = None,
    ) -> Checklist:
        """
        Update an item in a checklist.

        Args:
            checklist_id: ID of the checklist
            item_id: ID of the checklist item
            name: New name for the checklist item
            resolved: Whether the item is resolved
            assignee: User ID (int) to assign the item to, or None to remove assignee
            parent: ID of the parent checklist item to nest under, or None to un-nest

        Returns:
            The updated Checklist object (containing the modified item)

        Raises:
            AuthenticationError: If authentication fails
            ResourceNotFound: If the checklist or item doesn't exist
            ValidationError: If the request data is invalid
            ClickUpError: For other API errors
        """
        data: Dict[str, Any] = {}

        if name is not None:
            data["name"] = name
        if resolved is not None:
            data["resolved"] = resolved
        if assignee is not None:
            data["assignee"] = assignee
        elif "assignee" in locals() and assignee is None:
            data["assignee"] = None

        if parent is not None:
            data["parent"] = parent
        elif "parent" in locals() and parent is None:
            data["parent"] = None

        if not data:
            pass

        response = await self._request(
            "PUT", f"checklist/{checklist_id}/checklist_item/{item_id}", data=data
        )
        # The API response contains the updated checklist under the 'checklist' key
        return Checklist.model_validate(response.get("checklist", {}))

    async def delete_item(self, checklist_id: str, item_id: str) -> bool:
        """
        Delete an item from a checklist.

        Args:
            checklist_id: ID of the checklist
            item_id: ID of the checklist item to delete

        Returns:
            True if deletion was successful

        Raises:
            AuthenticationError: If authentication fails
            ResourceNotFound: If the checklist or item doesn't exist
            ClickUpError: For other API errors
        """
        await self._request(
            "DELETE", f"checklist/{checklist_id}/checklist_item/{item_id}"
        )
        return True

    async def update(
        self,
        checklist_id: str,
        name: Optional[str] = None,
        position: Optional[int] = None,
    ) -> Checklist:
        """
        Update a checklist (rename or reorder).

        Args:
            checklist_id: ID of the checklist
            name: New name for the checklist
            position: New position (order) for the checklist. 0 is the top.

        Returns:
            The updated Checklist object

        Raises:
            ValueError: If neither name nor position is provided.
            AuthenticationError: If authentication fails
            ResourceNotFound: If the checklist doesn't exist
            ValidationError: If the request data is invalid
            ClickUpError: For other API errors
        """
        if name is None and position is None:
            raise ValueError("Either name or position must be provided for update")

        data = {}
        if name is not None:
            data["name"] = name
        if position is not None:
            data["position"] = position

        response = await self._request("PUT", f"checklist/{checklist_id}", data=data)
        # The API response contains the updated checklist under the 'checklist' key
        return Checklist.model_validate(response.get("checklist", {}))

    async def delete(
        self,
        checklist_id: str,
    ) -> bool:
        """
        Delete a checklist.

        Args:
            checklist_id: ID of the checklist

        Returns:
            True if successful

        Raises:
            AuthenticationError: If authentication fails
            ResourceNotFound: If the checklist doesn't exist
            ClickUpError: For other API errors
        """
        await self._request("DELETE", f"checklist/{checklist_id}")
        return True
