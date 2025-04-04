"""
Workspace resources for ClickUp API.

This module contains resource classes for interacting with workspace-related endpoints.
"""

from typing import Any, Dict, List, Optional

from ..models import (
    AuditLogEntry,
    AuditLogFilter,
    AuditLogPagination,
    CustomItem,
    GetAuditLogsRequest,
    Workspace,
)
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

    async def get_audit_logs(
        self,
        filter_criteria: AuditLogFilter,
        pagination: AuditLogPagination,
        workspace_id: Optional[str] = None,
    ) -> List[AuditLogEntry]:
        """
        Get Workspace-level audit logs based on filter and pagination criteria.

        Note: Audit logs can only be accessed by the Workspace owner on Enterprise Plans.

        Args:
            filter_criteria: Filter criteria for the audit logs.
            pagination: Pagination settings for the audit logs.
            workspace_id: ID of the workspace (uses the one set in the client context if not provided).

        Returns:
            A list of audit log entries (currently represented as dictionaries).

        Raises:
            ValueError: If workspace_id is not provided and not set in context.
            ClickUpError: For API errors, including permission errors if not owner/Enterprise.
        """
        workspace_id = self._get_context_id("_workspace_id", workspace_id)
        if not workspace_id:
            raise ValueError("Workspace ID must be provided")

        # Ensure the workspace_id in the filter matches the target workspace
        if filter_criteria.workspace_id != workspace_id:
            raise ValueError(
                "Workspace ID in filter must match the target workspace_id"
            )

        request_data = GetAuditLogsRequest(
            filter=filter_criteria, pagination=pagination
        )

        response = await self._request(
            "POST",
            f"workspaces/{workspace_id}/auditlogs",
            data=request_data.model_dump(by_alias=True, exclude_none=True),
        )

        # The response structure for audit logs isn't explicitly defined in the docs.
        # Assuming it returns a list of log entries directly or under a key like 'logs'.
        # Adjust parsing if the actual response structure is known.
        return response.get("logs", response)  # Adapt as needed
