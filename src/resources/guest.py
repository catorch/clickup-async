"""
Guest resources for ClickUp API.
"""

import logging
from typing import Any, Dict, Optional

from ..exceptions import ClickUpError, ResourceNotFound, ValidationError
from ..models.guest import Guest
from .base import BaseResource

logger = logging.getLogger("clickup")


class GuestResource(BaseResource):
    """Guest-related API endpoints (Workspace level)."""

    async def invite_guest_to_workspace(
        self,
        email: str,
        workspace_id: Optional[str] = None,
        can_edit_tags: bool = True,
        can_see_time_spent: bool = True,
        can_see_time_estimated: bool = True,
        can_create_views: bool = True,
        custom_role_id: Optional[int] = None,
    ) -> Guest:
        """
        Invite a guest to join a Workspace.
        Requires Enterprise Plan.

        Args:
            email: Email address of the guest to invite.
            workspace_id: ID of the workspace (uses context if None).
            can_edit_tags: Permission setting.
            can_see_time_spent: Permission setting.
            can_see_time_estimated: Permission setting.
            can_create_views: Permission setting.
            custom_role_id: Optional custom role ID.

        Returns:
            Guest object representing the invited user.

        Raises:
            ValueError: If workspace_id is not provided and not set in context.
            AuthenticationError: If authentication fails or plan is not Enterprise.
            ResourceNotFound: If the workspace doesn't exist.
            ValidationError: If the request data is invalid.
            ClickUpError: For other API errors.
        """
        workspace_id = self._get_context_id("_workspace_id", workspace_id)
        if not workspace_id:
            raise ValueError("Workspace ID must be provided")

        data: Dict[str, Any] = {
            "email": email,
            "can_edit_tags": can_edit_tags,
            "can_see_time_spent": can_see_time_spent,
            "can_see_time_estimated": can_see_time_estimated,
            "can_create_views": can_create_views,
        }
        if custom_role_id is not None:
            data["custom_role_id"] = custom_role_id

        response = await self._request("POST", f"team/{workspace_id}/guest", data=data)
        # API returns the guest user object directly
        return Guest.model_validate(response.get("user", {}))  # Nested under "user"

    async def get_guest(
        self, guest_id: int, workspace_id: Optional[str] = None
    ) -> Guest:
        """
        Get information about a specific guest.
        Requires Enterprise Plan.

        Args:
            guest_id: ID of the guest.
            workspace_id: ID of the workspace (uses context if None).

        Returns:
            Guest object.

        Raises:
            ValueError: If workspace_id is not provided and not set in context.
            AuthenticationError: If authentication fails or plan is not Enterprise.
            ResourceNotFound: If the workspace or guest doesn't exist.
            ClickUpError: For other API errors.
        """
        workspace_id = self._get_context_id("_workspace_id", workspace_id)
        if not workspace_id:
            raise ValueError("Workspace ID must be provided")

        response = await self._request("GET", f"team/{workspace_id}/guest/{guest_id}")
        # API returns the guest user object directly under "user"
        return Guest.model_validate(response.get("user", {}))

    async def edit_guest_on_workspace(
        self,
        guest_id: int,
        workspace_id: Optional[str] = None,
        username: Optional[str] = None,
        can_edit_tags: Optional[bool] = None,
        can_see_time_spent: Optional[bool] = None,
        can_see_time_estimated: Optional[bool] = None,
        can_create_views: Optional[bool] = None,
        custom_role_id: Optional[int] = None,
    ) -> Guest:
        """
        Edit details and permissions for a guest on the Workspace.
        Requires Enterprise Plan.

        Args:
            guest_id: ID of the guest to edit.
            workspace_id: ID of the workspace (uses context if None).
            username: New username for the guest.
            can_edit_tags: Permission setting.
            can_see_time_spent: Permission setting.
            can_see_time_estimated: Permission setting.
            can_create_views: Permission setting.
            custom_role_id: Optional new custom role ID.

        Returns:
            Guest object with updated details.

        Raises:
            ValueError: If workspace_id is not provided and not set in context or no fields provided.
            AuthenticationError: If authentication fails or plan is not Enterprise.
            ResourceNotFound: If the workspace or guest doesn't exist.
            ValidationError: If the request data is invalid.
            ClickUpError: For other API errors.
        """
        workspace_id = self._get_context_id("_workspace_id", workspace_id)
        if not workspace_id:
            raise ValueError("Workspace ID must be provided")

        data: Dict[str, Any] = {}
        if username is not None:
            data["username"] = username
        if can_edit_tags is not None:
            data["can_edit_tags"] = can_edit_tags
        if can_see_time_spent is not None:
            data["can_see_time_spent"] = can_see_time_spent
        if can_see_time_estimated is not None:
            data["can_see_time_estimated"] = can_see_time_estimated
        if can_create_views is not None:
            data["can_create_views"] = can_create_views
        if custom_role_id is not None:
            data["custom_role_id"] = custom_role_id

        if not data:
            raise ValueError("At least one field must be provided for editing.")

        response = await self._request(
            "PUT", f"team/{workspace_id}/guest/{guest_id}", data=data
        )
        # API returns the updated guest user object under "user"
        return Guest.model_validate(response.get("user", {}))

    async def remove_guest_from_workspace(
        self, guest_id: int, workspace_id: Optional[str] = None
    ) -> None:
        """
        Remove a guest from the Workspace.
        Requires Enterprise Plan.

        Args:
            guest_id: ID of the guest to remove.
            workspace_id: ID of the workspace (uses context if None).

        Raises:
            ValueError: If workspace_id is not provided and not set in context.
            AuthenticationError: If authentication fails or plan is not Enterprise.
            ResourceNotFound: If the workspace or guest doesn't exist.
            ClickUpError: For other API errors.
        """
        workspace_id = self._get_context_id("_workspace_id", workspace_id)
        if not workspace_id:
            raise ValueError("Workspace ID must be provided")

        await self._request("DELETE", f"team/{workspace_id}/guest/{guest_id}")
        # No return value
