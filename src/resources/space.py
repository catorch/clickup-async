"""
Space resources for ClickUp API.

This module contains resource classes for interacting with space-related endpoints.
"""

from typing import Dict, List, Optional, Union

from ..models import Space
from .base import BaseResource


class SpaceResource(BaseResource):
    """Space-related API endpoints."""

    async def get_spaces(
        self, workspace_id: Optional[str] = None, archived: bool = False
    ) -> List[Space]:
        """
        Get all spaces in a workspace.

        Args:
            workspace_id: ID of the workspace (uses the one set in the client context if not provided)
            archived: Whether to include archived spaces (defaults to False)

        Returns:
            List of Space objects

        Raises:
            ValueError: If workspace_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the workspace doesn't exist
            ClickUpError: For other API errors
        """
        workspace_id = self._get_context_id("_workspace_id", workspace_id)
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
            space_id: ID of the space to fetch (uses the one set in the client context if not provided)

        Returns:
            Space object

        Raises:
            ValueError: If space_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the space doesn't exist
            ClickUpError: For other API errors
        """
        space_id = self._get_context_id("_space_id", space_id)
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
            workspace_id: ID of the workspace (uses the one set in the client context if not provided)
            private: Whether the space is private (defaults to False)
            admin_can_manage: Whether admins can manage the space (Enterprise feature, defaults to True)
            multiple_assignees: Whether to allow multiple assignees for tasks (defaults to True)
            features: Dictionary of space features to enable/disable
            color: Color for the space (hex code)

        Returns:
            The created Space object

        Raises:
            ValueError: If workspace_id is not provided and not set in context, or if name is empty
            AuthenticationError: If authentication fails
            ResourceNotFound: If the workspace doesn't exist
            ValidationError: If the request data is invalid
            ClickUpError: For other API errors
        """
        workspace_id = self._get_context_id("_workspace_id", workspace_id)
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
            space_id: ID of the space to update (uses the one set in the client context if not provided)
            name: New name for the space
            color: New color for the space (hex code)
            private: Whether the space should be private
            admin_can_manage: Whether admins can manage the space (Enterprise feature)
            multiple_assignees: Whether to allow multiple assignees for tasks
            features: Dictionary of space features to enable/disable

        Returns:
            The updated Space object

        Raises:
            ValueError: If space_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the space doesn't exist
            ValidationError: If the request data is invalid
            ClickUpError: For other API errors
        """
        space_id = self._get_context_id("_space_id", space_id)
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
            space_id: ID of the space to delete (uses the one set in the client context if not provided)

        Returns:
            True if successful

        Raises:
            ValueError: If space_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the space doesn't exist
            ClickUpError: For other API errors
        """
        space_id = self._get_context_id("_space_id", space_id)
        if not space_id:
            raise ValueError("Space ID must be provided")

        await self._request("DELETE", f"space/{space_id}")
        return True

    async def get_custom_fields(
        self,
        space_id: Optional[str] = None,
    ) -> List:
        """
        Get all custom fields available in a specific space.
        Note: This only returns custom fields created at the space level.

        Args:
            space_id: ID of the space (uses the one set in the client context if not provided)

        Returns:
            List of CustomField objects

        Raises:
            ValueError: If space_id is not provided and not set in context
            ResourceNotFound: If the space doesn't exist
            ClickUpError: For other API errors
        """
        space_id = self._get_context_id("_space_id", space_id)
        if not space_id:
            raise ValueError("Space ID must be provided")

        response = await self._request("GET", f"space/{space_id}/field")

        # Import here to avoid circular imports
        from ..models import CustomField

        return [
            CustomField.model_validate(field) for field in response.get("fields", [])
        ]
