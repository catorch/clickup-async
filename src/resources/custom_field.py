"""
Custom field resources for ClickUp API.

This module contains resource classes for interacting with custom field-related endpoints.
"""

from typing import Any, Dict, List, Optional

from ..models import CustomField
from .base import BaseResource


class CustomFieldResource(BaseResource):
    """Custom field-related API endpoints."""

    async def get_workspace_fields(
        self,
        workspace_id: Optional[str] = None,
    ) -> List[CustomField]:
        """
        Get all custom fields available in a specific workspace.
        Note: This only returns custom fields created at the workspace level.

        Args:
            workspace_id: ID of the workspace (uses the one set in the client context if not provided)

        Returns:
            List of CustomField objects

        Raises:
            ValueError: If workspace_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the workspace doesn't exist
            ClickUpError: For other API errors
        """
        workspace_id = self._get_context_id("_workspace_id", workspace_id)
        if not workspace_id:
            raise ValueError("Workspace ID must be provided")

        response = await self._request("GET", f"team/{workspace_id}/field")
        return [
            CustomField.model_validate(field) for field in response.get("fields", [])
        ]

    async def get_space_fields(
        self,
        space_id: Optional[str] = None,
    ) -> List[CustomField]:
        """
        Get all custom fields available in a specific space.
        Note: This only returns custom fields created at the space level.

        Args:
            space_id: ID of the space (uses the one set in the client context if not provided)

        Returns:
            List of CustomField objects

        Raises:
            ValueError: If space_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the space doesn't exist
            ClickUpError: For other API errors
        """
        space_id = self._get_context_id("_space_id", space_id)
        if not space_id:
            raise ValueError("Space ID must be provided")

        response = await self._request("GET", f"space/{space_id}/field")
        return [
            CustomField.model_validate(field) for field in response.get("fields", [])
        ]

    async def get_folder_fields(
        self,
        folder_id: Optional[str] = None,
    ) -> List[CustomField]:
        """
        Get all custom fields available in a specific folder.
        Note: This only returns custom fields created at the folder level.

        Args:
            folder_id: ID of the folder (uses the one set in the client context if not provided)

        Returns:
            List of CustomField objects

        Raises:
            ValueError: If folder_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the folder doesn't exist
            ClickUpError: For other API errors
        """
        folder_id = self._get_context_id("_folder_id", folder_id)
        if not folder_id:
            raise ValueError("Folder ID must be provided")

        response = await self._request("GET", f"folder/{folder_id}/field")
        return [
            CustomField.model_validate(field) for field in response.get("fields", [])
        ]

    async def get_list_fields(
        self,
        list_id: Optional[str] = None,
    ) -> List[CustomField]:
        """
        Get all custom fields available in a specific list.

        Args:
            list_id: ID of the list (uses the one set in the client context if not provided)

        Returns:
            List of CustomField objects

        Raises:
            ValueError: If list_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the list doesn't exist
            ClickUpError: For other API errors
        """
        list_id = self._get_context_id("_list_id", list_id)
        if not list_id:
            raise ValueError("List ID must be provided")

        response = await self._request("GET", f"list/{list_id}/field")
        return [
            CustomField.model_validate(field) for field in response.get("fields", [])
        ]

    async def set_task_field(
        self,
        field_id: str,
        value: Dict[str, Any],
        task_id: Optional[str] = None,
        custom_task_ids: bool = False,
        team_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Set a custom field value for a task.

        Args:
            field_id: ID of the custom field to set
            value: Value to set for the custom field
            task_id: ID of the task (uses the one set in the client context if not provided)
            custom_task_ids: Whether to use custom task IDs
            team_id: Team ID when using custom task IDs

        Returns:
            Response data from the API

        Raises:
            ValueError: If task_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the task or field doesn't exist
            ValidationError: If the value is invalid for the field type
            ClickUpError: For other API errors
        """
        task_id = self._get_context_id("_task_id", task_id)
        if not task_id:
            raise ValueError("Task ID must be provided")

        params = {}
        if custom_task_ids:
            params["custom_task_ids"] = str(custom_task_ids).lower()
            if team_id:
                params["team_id"] = team_id

        data = {"value": value}
        return await self._request(
            "POST", f"task/{task_id}/field/{field_id}", data=data, params=params
        )

    async def remove_task_field(
        self,
        field_id: str,
        task_id: Optional[str] = None,
        custom_task_ids: bool = False,
        team_id: Optional[str] = None,
    ) -> bool:
        """
        Remove a custom field value from a task.

        Args:
            field_id: ID of the custom field to remove
            task_id: ID of the task (uses the one set in the client context if not provided)
            custom_task_ids: Whether to use custom task IDs
            team_id: Team ID when using custom task IDs

        Returns:
            True if successful

        Raises:
            ValueError: If task_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the task or field doesn't exist
            ClickUpError: For other API errors
        """
        task_id = self._get_context_id("_task_id", task_id)
        if not task_id:
            raise ValueError("Task ID must be provided")

        params = {}
        if custom_task_ids:
            params["custom_task_ids"] = str(custom_task_ids).lower()
            if team_id:
                params["team_id"] = team_id

        await self._request("DELETE", f"task/{task_id}/field/{field_id}", params=params)
        return True
