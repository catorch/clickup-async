"""
Base resource for ClickUp API.

This module contains the base resource class that all other resources inherit from.
"""

from typing import Any, Dict, Optional


class BaseResource:
    """Base class for API resources."""

    def __init__(self, client):
        """Initialize the resource with a client instance.

        Args:
            client: The ClickUp client instance
        """
        self.client = client

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        api_version: str = "v2",
    ) -> Dict[str, Any]:
        """Delegate the request to the client's request method.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            params: Query parameters
            data: Request body data
            files: Files to upload
            api_version: API version to use

        Returns:
            Response data as a dictionary or an empty dict for 204 responses
        """
        response = await self.client._request(
            method, endpoint, params, data, files, api_version
        )
        # For 204 No Content responses, return an empty dict
        if not response and method == "DELETE":
            return {}
        return response

    def _get_context_id(
        self, id_name: str, provided_id: Optional[str] = None
    ) -> Optional[str]:
        """Get an ID from either the provided value or the client context.

        Args:
            id_name: Name of the ID attribute on the client (e.g., "_workspace_id")
            provided_id: Explicitly provided ID value

        Returns:
            The resolved ID value or None
        """
        if provided_id is not None:
            return provided_id

        return getattr(self.client, id_name, None)
