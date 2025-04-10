"""
Folder resources for ClickUp API.

This module contains resource classes for interacting with folder-related endpoints.
"""

from typing import Any, Dict, List, Literal, Optional

from ..models import Folder
from .base import BaseResource


class FolderResource(BaseResource):
    """Folder-related API endpoints."""

    async def get_all(self, space_id: Optional[str] = None) -> List[Folder]:
        """
        Get all folders in a space.

        Args:
            space_id: ID of the space (uses the one set in the client context if not provided)

        Returns:
            List of Folder objects

        Raises:
            ValueError: If space_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the space doesn't exist
            ClickUpError: For other API errors
        """
        space_id = self._get_context_id("_space_id", space_id)
        if not space_id:
            raise ValueError("Space ID must be provided")

        response = await self._request("GET", f"space/{space_id}/folder")
        return [Folder.model_validate(folder) for folder in response.get("folders", [])]

    async def get(self, folder_id: Optional[str] = None) -> Folder:
        """
        Get details for a specific folder.

        Args:
            folder_id: ID of the folder to fetch (uses the one set in the client context if not provided)

        Returns:
            Folder object

        Raises:
            ValueError: If folder_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the folder doesn't exist
            ClickUpError: For other API errors
        """
        folder_id = self._get_context_id("_folder_id", folder_id)
        if not folder_id:
            raise ValueError("Folder ID must be provided")

        response = await self._request("GET", f"folder/{folder_id}")
        return Folder.model_validate(response)

    async def create(
        self,
        name: str,
        space_id: Optional[str] = None,
        hidden: bool = False,
    ) -> Folder:
        """
        Create a new folder in a space.

        Args:
            name: Name of the new folder
            space_id: ID of the space (uses the one set in the client context if not provided)
            hidden: Whether the folder should be hidden

        Returns:
            The created Folder object

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

        data = {
            "name": name,
            "hidden": hidden,
        }

        response = await self._request("POST", f"space/{space_id}/folder", data=data)
        return Folder.model_validate(response)

    async def update(
        self,
        folder_id: Optional[str] = None,
        name: Optional[str] = None,
        hidden: Optional[bool] = None,
    ) -> Folder:
        """
        Update an existing folder.

        Args:
            folder_id: ID of the folder to update (uses the one set in the client context if not provided)
            name: New name for the folder
            hidden: Whether the folder should be hidden

        Returns:
            The updated Folder object

        Raises:
            ValueError: If folder_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the folder doesn't exist
            ValidationError: If the request data is invalid
            ClickUpError: For other API errors
        """
        folder_id = self._get_context_id("_folder_id", folder_id)
        if not folder_id:
            raise ValueError("Folder ID must be provided")

        data = {}
        if name is not None:
            data["name"] = name
        if hidden is not None:
            data["hidden"] = hidden

        response = await self._request("PUT", f"folder/{folder_id}", data=data)
        return Folder.model_validate(response)

    async def delete(self, folder_id: Optional[str] = None) -> bool:
        """
        Delete a folder.

        Args:
            folder_id: ID of the folder to delete (uses the one set in the client context if not provided)

        Returns:
            True if successful

        Raises:
            ValueError: If folder_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the folder doesn't exist
            ClickUpError: For other API errors
        """
        folder_id = self._get_context_id("_folder_id", folder_id)
        if not folder_id:
            raise ValueError("Folder ID must be provided")

        await self._request("DELETE", f"folder/{folder_id}")
        return True

    async def create_from_template(
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
            space_id: ID of the space where the folder will be created (uses the one set in the client context if not provided)
            template_id: ID of the folder template to use (uses the one set in the client context if not provided)
            return_immediately: Whether to return immediately without waiting for all assets to be created
            options: Additional options for creating the folder from template

        Returns:
            The newly created folder

        Raises:
            ValueError: If required parameters are missing
            AuthenticationError: If authentication fails
            ResourceNotFound: If the space or template doesn't exist
            ValidationError: If the request data is invalid
            ClickUpError: For other API errors
        """
        space_id = self._get_context_id("_space_id", space_id)
        if not space_id:
            raise ValueError("Space ID must be provided")

        template_id = self._get_context_id("_template_id", template_id)
        if not template_id:
            raise ValueError("Template ID must be provided")

        if not name:
            raise ValueError("Name must be provided")

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

        return Folder.model_validate(response)

    # --- Guest Access --- #

    async def add_guest_to_folder(
        self,
        folder_id: str,
        guest_id: int,
        permission_level: Literal["read", "comment", "edit", "create"],
        include_shared: bool = True,
    ) -> Dict[str, Any]:
        """
        Share a Folder with a guest.
        Requires Enterprise Plan.

        Args:
            folder_id: ID of the Folder.
            guest_id: ID of the guest.
            permission_level: Access level ("read", "comment", "edit", "create").
            include_shared: Include details of items shared with the guest.

        Returns:
            Dictionary representing the Folder (structure may vary).

        Raises:
            AuthenticationError: If authentication fails or plan is not Enterprise.
            ResourceNotFound: If the Folder or guest doesn't exist.
            ClickUpError: For other API errors.
        """
        params = {"include_shared": str(include_shared).lower()}
        data = {"permission_level": permission_level}
        response = await self._request(
            "POST", f"folder/{folder_id}/guest/{guest_id}", params=params, data=data
        )
        return response  # Return raw dict

    async def remove_guest_from_folder(
        self,
        folder_id: str,
        guest_id: int,
        include_shared: bool = True,
    ) -> None:
        """
        Revoke a guest's access to a Folder.
        Requires Enterprise Plan.

        Args:
            folder_id: ID of the Folder.
            guest_id: ID of the guest.
            include_shared: Include details of items shared with the guest.

        Raises:
            AuthenticationError: If authentication fails or plan is not Enterprise.
            ResourceNotFound: If the Folder or guest doesn't exist.
            ClickUpError: For other API errors.
        """
        params = {"include_shared": str(include_shared).lower()}
        await self._request(
            "DELETE", f"folder/{folder_id}/guest/{guest_id}", params=params
        )
        # No return value
