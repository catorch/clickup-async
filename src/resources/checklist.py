"""
Checklist resources for ClickUp API.

This module contains resource classes for interacting with checklist-related endpoints.
"""

from typing import Optional

from ..models import Checklist
from .base import BaseResource


class ChecklistResource(BaseResource):
    """Checklist-related API endpoints."""

    async def create(
        self,
        name: str,
        task_id: Optional[str] = None,
    ) -> Checklist:
        """
        Create a checklist in a task.

        Args:
            name: Name of the checklist
            task_id: ID of the task (uses the one set in the client context if not provided)

        Returns:
            The created Checklist object

        Raises:
            ValueError: If task_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the task doesn't exist
            ValidationError: If the request data is invalid
            ClickUpError: For other API errors
        """
        task_id = self._get_context_id("_task_id", task_id)
        if not task_id:
            raise ValueError("Task ID must be provided")

        data = {"name": name}

        response = await self._request("POST", f"task/{task_id}/checklist", data=data)
        return Checklist.model_validate(response)

    async def create_item(
        self,
        checklist_id: str,
        name: str,
        assignee: Optional[str] = None,
    ) -> Checklist:
        """
        Add an item to a checklist.

        Args:
            checklist_id: ID of the checklist
            name: Name of the checklist item
            assignee: User ID to assign the item to

        Returns:
            The updated Checklist object

        Raises:
            AuthenticationError: If authentication fails
            ResourceNotFound: If the checklist doesn't exist
            ValidationError: If the request data is invalid
            ClickUpError: For other API errors
        """
        data = {"name": name}

        if assignee:
            data["assignee"] = assignee

        response = await self._request(
            "POST", f"checklist/{checklist_id}/checklist_item", data=data
        )
        return Checklist.model_validate(response)

    async def update_item(
        self,
        checklist_id: str,
        item_id: str,
        name: Optional[str] = None,
        resolved: Optional[bool] = None,
        assignee: Optional[str] = None,
    ) -> Checklist:
        """
        Update an item in a checklist.

        Args:
            checklist_id: ID of the checklist
            item_id: ID of the checklist item
            name: New name for the checklist item
            resolved: Whether the item is resolved
            assignee: User ID to assign the item to

        Returns:
            The updated Checklist object

        Raises:
            AuthenticationError: If authentication fails
            ResourceNotFound: If the checklist or item doesn't exist
            ValidationError: If the request data is invalid
            ClickUpError: For other API errors
        """
        data = {}

        if name is not None:
            data["name"] = name
        if resolved is not None:
            data["resolved"] = resolved
        if assignee is not None:
            data["assignee"] = assignee

        response = await self._request(
            "PUT", f"checklist/{checklist_id}/checklist_item/{item_id}", data=data
        )
        return Checklist.model_validate(response)

    async def delete_item(
        self,
        checklist_id: str,
        item_id: str,
    ) -> Checklist:
        """
        Delete an item from a checklist.

        Args:
            checklist_id: ID of the checklist
            item_id: ID of the checklist item

        Returns:
            The updated Checklist object

        Raises:
            AuthenticationError: If authentication fails
            ResourceNotFound: If the checklist or item doesn't exist
            ClickUpError: For other API errors
        """
        response = await self._request(
            "DELETE", f"checklist/{checklist_id}/checklist_item/{item_id}"
        )
        return Checklist.model_validate(response)

    async def update(
        self,
        checklist_id: str,
        name: str,
    ) -> Checklist:
        """
        Update a checklist.

        Args:
            checklist_id: ID of the checklist
            name: New name for the checklist

        Returns:
            The updated Checklist object

        Raises:
            AuthenticationError: If authentication fails
            ResourceNotFound: If the checklist doesn't exist
            ValidationError: If the request data is invalid
            ClickUpError: For other API errors
        """
        data = {"name": name}

        response = await self._request("PUT", f"checklist/{checklist_id}", data=data)
        return Checklist.model_validate(response)

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
