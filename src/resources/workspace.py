"""
Workspace resources for ClickUp API.

This module contains resource classes for interacting with workspace-related endpoints.
"""

from typing import List, Optional

from ..models import CustomItem, Workspace
from .base import BaseResource


class WorkspaceResource(BaseResource):
    """Workspace-related API endpoints."""

    async def get_workspaces(self) -> List[Workspace]:
        """
        Get all workspaces accessible to the authenticated user.

        Returns:
            List of Workspace objects
        """
        response = await self._request("GET", "team")
        return [Workspace.model_validate(team) for team in response.get("teams", [])]

    async def get_workspace(self, workspace_id: Optional[str] = None) -> Workspace:
        """
        Get details for a specific workspace.

        Args:
            workspace_id: ID of the workspace to fetch (uses the one set in the client context if not provided)

        Returns:
            Workspace object

        Raises:
            ValueError: If workspace_id is not provided and not set in context
        """
        workspace_id = self._get_context_id("_workspace_id", workspace_id)
        if not workspace_id:
            raise ValueError("Workspace ID must be provided")

        response = await self._request("GET", f"team/{workspace_id}")
        return Workspace.model_validate(response.get("team", {}))

    async def get_custom_task_types(
        self,
        workspace_id: Optional[str] = None,
    ) -> List[CustomItem]:
        """
        Get all custom task types available in a workspace.

        Args:
            workspace_id: ID of the workspace (uses the one set in the client context if not provided)

        Returns:
            List of CustomItem objects representing the custom task types

        Raises:
            ValueError: If workspace_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the workspace doesn't exist
            ClickUpError: For other API errors
        """
        workspace_id = self._get_context_id("_workspace_id", workspace_id)
        if not workspace_id:
            raise ValueError("Workspace ID must be provided")

        response = await self._request("GET", f"team/{workspace_id}/custom_item")
        return [
            CustomItem.model_validate(item) for item in response.get("custom_items", [])
        ]

    async def get_custom_fields(
        self,
        workspace_id: Optional[str] = None,
    ) -> List:
        """
        Get all custom fields available in a specific workspace.
        Note: This only returns custom fields created at the workspace level.

        Args:
            workspace_id: ID of the workspace (uses the one set in the client context if not provided)

        Returns:
            List of CustomField objects

        Raises:
            ValueError: If workspace_id is not provided and not set in context
            ResourceNotFound: If the workspace doesn't exist
            ClickUpError: For other API errors
        """
        workspace_id = self._get_context_id("_workspace_id", workspace_id)
        if not workspace_id:
            raise ValueError("Workspace ID must be provided")

        response = await self._request("GET", f"team/{workspace_id}/field")

        # Import here to avoid circular imports
        from ..models import CustomField

        return [
            CustomField.model_validate(field) for field in response.get("fields", [])
        ]
