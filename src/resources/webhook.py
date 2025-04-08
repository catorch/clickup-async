"""
Webhook resources for ClickUp API.

This module contains resource classes for interacting with webhook-related endpoints.
"""

import logging
from typing import Any, Dict, List, Optional

from ..exceptions import ResourceNotFound, ValidationError
from ..models.webhook import Webhook
from .base import BaseResource

logger = logging.getLogger("clickup")


class WebhookResource(BaseResource):
    """Webhook-related API endpoints."""

    async def get_webhooks(self, workspace_id: Optional[str] = None) -> List[Webhook]:
        """
        Get all webhooks for a workspace created by the authenticated user.

        Args:
            workspace_id: ID of the workspace (uses the one set in the client context if not provided)

        Returns:
            List of Webhook objects

        Raises:
            ValueError: If workspace_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the workspace doesn't exist
            ClickUpError: For other API errors
        """
        workspace_id = self._get_context_id("_workspace_id", workspace_id)
        if not workspace_id:
            raise ValueError("Workspace ID must be provided")

        response = await self._request("GET", f"team/{workspace_id}/webhook")
        # API returns webhooks in a list under the "webhooks" key
        webhooks_data = response.get("webhooks", [])
        return [Webhook.model_validate(hook) for hook in webhooks_data]

    async def create_webhook(
        self,
        endpoint: str,
        events: List[str],
        workspace_id: Optional[str] = None,
        space_id: Optional[int] = None,
        folder_id: Optional[int] = None,
        list_id: Optional[int] = None,
        task_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new webhook.

        Args:
            endpoint: The URL endpoint for the webhook.
            events: List of events to subscribe to (use "*" for all).
            workspace_id: ID of the workspace (uses the one set in the client context if not provided)
            space_id: Optional Space ID to scope the webhook.
            folder_id: Optional Folder ID to scope the webhook.
            list_id: Optional List ID to scope the webhook.
            task_id: Optional Task ID to scope the webhook.

        Returns:
            The created Webhook object (contains id and secret).

        Raises:
            ValueError: If workspace_id is not provided and not set in context, or if multiple scope IDs are provided.
            AuthenticationError: If authentication fails
            ResourceNotFound: If the workspace or scope ID doesn't exist
            ValidationError: If the request data is invalid
            ClickUpError: For other API errors
        """
        workspace_id = self._get_context_id("_workspace_id", workspace_id)
        if not workspace_id:
            raise ValueError("Workspace ID must be provided")

        # Ensure only one scope ID is provided
        scope_ids = [space_id, folder_id, list_id, task_id]
        if sum(1 for scope_id in scope_ids if scope_id is not None) > 1:
            raise ValueError(
                "Only one of space_id, folder_id, list_id, or task_id can be provided."
            )

        data: Dict[str, Any] = {"endpoint": endpoint, "events": events}

        if space_id is not None:
            data["space_id"] = space_id
        if folder_id is not None:
            data["folder_id"] = folder_id
        if list_id is not None:
            data["list_id"] = list_id
        if task_id is not None:
            data["task_id"] = task_id

        response = await self._request(
            "POST", f"team/{workspace_id}/webhook", data=data
        )
        # API returns only id and secret, not the full object
        return response  # Return the raw dict

    async def update_webhook(
        self,
        webhook_id: str,
        endpoint: Optional[str] = None,
        events: Optional[List[str]] = None,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update an existing webhook.

        Args:
            webhook_id: ID of the webhook to update.
            endpoint: New URL endpoint.
            events: New list of events to subscribe to (use "*" for all).
            status: New status for the webhook.

        Returns:
            The updated Webhook object.

        Raises:
            AuthenticationError: If authentication fails
            ResourceNotFound: If the webhook doesn't exist
            ValidationError: If the request data is invalid
            ClickUpError: For other API errors
        """
        data: Dict[str, Any] = {}
        if endpoint is not None:
            data["endpoint"] = endpoint
        if events is not None:
            data["events"] = events
        if status is not None:
            data["status"] = status

        if not data:
            raise ValueError(
                "At least one field (endpoint, events, status) must be provided for update."
            )

        response = await self._request("PUT", f"webhook/{webhook_id}", data=data)
        # API returns only id and secret on update
        return response  # Return the raw dict

    async def delete_webhook(self, webhook_id: str) -> bool:
        """
        Delete a webhook.

        Args:
            webhook_id: ID of the webhook to delete.

        Returns:
            True if successful.

        Raises:
            AuthenticationError: If authentication fails
            ResourceNotFound: If the webhook doesn't exist
            ClickUpError: For other API errors
        """
        await self._request("DELETE", f"webhook/{webhook_id}")
        return True
