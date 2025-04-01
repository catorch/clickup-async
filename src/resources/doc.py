"""
Doc resources for ClickUp API.

This module contains resource classes for interacting with doc-related endpoints.
"""

from typing import Any, Dict, List, Optional, Tuple

from ..models import Doc, DocPage, DocPageListing
from .base import BaseResource


class DocResource(BaseResource):
    """Doc-related API endpoints."""

    async def get_all(
        self,
        workspace_id: Optional[str] = None,
        doc_id: Optional[str] = None,
        creator: Optional[int] = None,
        deleted: bool = False,
        archived: bool = False,
        parent_id: Optional[str] = None,
        parent_type: Optional[str] = None,
        limit: int = 50,
        next_cursor: Optional[str] = None,
    ) -> Tuple[List[Doc], Optional[str]]:
        """
        Get docs from a workspace.

        Args:
            workspace_id: ID of the workspace (uses the one set in the client context if not provided)
            doc_id: Filter results to a single Doc with the given Doc ID
            creator: Filter results to Docs created by the user with the given user ID
            deleted: Filter results to return deleted Docs
            archived: Filter results to return archived Docs
            parent_id: Filter results to children of a parent Doc with the given parent Doc ID
            parent_type: Filter results to children of the given parent Doc type (e.g., SPACE, FOLDER, LIST, etc.)
            limit: The maximum number of results to retrieve (10-100)
            next_cursor: The cursor to use to get the next page of results

        Returns:
            Tuple of (list of Doc objects, next cursor string if more results exist)

        Raises:
            ValueError: If workspace_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the workspace doesn't exist
            ClickUpError: For other API errors
        """
        workspace_id = self._get_context_id("_workspace_id", workspace_id)
        if not workspace_id:
            raise ValueError("Workspace ID must be provided")

        params = {
            "deleted": str(deleted).lower(),
            "archived": str(archived).lower(),
            "limit": limit,
        }
        if doc_id:
            params["id"] = doc_id
        if creator:
            params["creator"] = creator
        if parent_id:
            params["parent_id"] = parent_id
        if parent_type:
            params["parent_type"] = parent_type
        if next_cursor:
            params["next_cursor"] = next_cursor

        response = await self._request(
            "GET", f"workspaces/{workspace_id}/docs", params=params, api_version="v3"
        )
        docs = [Doc.model_validate(doc) for doc in response.get("docs", [])]
        next_cursor = response.get("next_cursor")
        return docs, next_cursor

    async def create(
        self,
        name: str,
        workspace_id: Optional[str] = None,
        parent: Optional[Dict[str, Any]] = None,
        visibility: Optional[str] = None,
        create_page: bool = True,
    ) -> Doc:
        """
        Create a new doc in a workspace.

        Args:
            name: The name of the new doc
            workspace_id: ID of the workspace (uses the one set in the client context if not provided)
            parent: The parent of the new doc (dict with 'id' and 'type')
            visibility: The visibility of the new doc (e.g., 'PUBLIC' or 'PRIVATE')
            create_page: Whether to create a new page when creating the doc

        Returns:
            The created Doc object

        Raises:
            ValueError: If workspace_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the workspace doesn't exist
            ValidationError: If the request data is invalid
            ClickUpError: For other API errors
        """
        workspace_id = self._get_context_id("_workspace_id", workspace_id)
        if not workspace_id:
            raise ValueError("Workspace ID must be provided")

        data = {
            "name": name,
            "create_page": create_page,
        }
        if parent:
            data["parent"] = parent
        if visibility:
            data["visibility"] = visibility

        response = await self._request(
            "POST", f"workspaces/{workspace_id}/docs", data=data, api_version="v3"
        )
        return Doc.model_validate(response)

    async def get(
        self,
        doc_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
    ) -> Doc:
        """
        Get a specific doc by ID.

        Args:
            doc_id: ID of the doc (uses the one set in the client context if not provided)
            workspace_id: ID of the workspace (uses the one set in the client context if not provided)

        Returns:
            The Doc object

        Raises:
            ValueError: If doc_id or workspace_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the doc or workspace doesn't exist
            ClickUpError: For other API errors
        """
        doc_id = self._get_context_id("_doc_id", doc_id)
        workspace_id = self._get_context_id("_workspace_id", workspace_id)
        if not doc_id:
            raise ValueError("Doc ID must be provided")
        if not workspace_id:
            raise ValueError("Workspace ID must be provided")

        response = await self._request(
            "GET", f"workspaces/{workspace_id}/docs/{doc_id}", api_version="v3"
        )
        return Doc.model_validate(response)

    async def get_page_listing(
        self,
        doc_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        max_page_depth: int = -1,
    ) -> List[DocPageListing]:
        """
        Get the page listing for a doc.

        Args:
            doc_id: ID of the doc (uses the one set in the client context if not provided)
            workspace_id: ID of the workspace (uses the one set in the client context if not provided)
            max_page_depth: Maximum depth to retrieve pages and subpages (-1 for unlimited)

        Returns:
            List of DocPageListing objects

        Raises:
            ValueError: If doc_id or workspace_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the doc or workspace doesn't exist
            ClickUpError: For other API errors
        """
        doc_id = self._get_context_id("_doc_id", doc_id)
        workspace_id = self._get_context_id("_workspace_id", workspace_id)
        if not doc_id:
            raise ValueError("Doc ID must be provided")
        if not workspace_id:
            raise ValueError("Workspace ID must be provided")

        params = {"max_page_depth": max_page_depth}
        response = await self._request(
            "GET",
            f"workspaces/{workspace_id}/docs/{doc_id}/pageListing",
            params=params,
            api_version="v3",
        )
        return [DocPageListing.model_validate(page) for page in response]

    async def get_pages(
        self,
        doc_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        max_page_depth: int = -1,
        content_format: str = "text/md",
    ) -> List[DocPage]:
        """
        Get all pages in a doc.

        Args:
            doc_id: ID of the doc (uses the one set in the client context if not provided)
            workspace_id: ID of the workspace (uses the one set in the client context if not provided)
            max_page_depth: Maximum depth to retrieve pages and subpages (-1 for unlimited)
            content_format: Format to return the page content in ('text/md' or 'text/plain')

        Returns:
            List of DocPage objects

        Raises:
            ValueError: If doc_id or workspace_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the doc or workspace doesn't exist
            ClickUpError: For other API errors
        """
        doc_id = self._get_context_id("_doc_id", doc_id)
        workspace_id = self._get_context_id("_workspace_id", workspace_id)
        if not doc_id:
            raise ValueError("Doc ID must be provided")
        if not workspace_id:
            raise ValueError("Workspace ID must be provided")

        params = {
            "max_page_depth": max_page_depth,
            "content_format": content_format,
        }
        response = await self._request(
            "GET",
            f"workspaces/{workspace_id}/docs/{doc_id}/pages",
            params=params,
            api_version="v3",
        )
        return [DocPage.model_validate(page) for page in response]

    async def create_page(
        self,
        name: str,
        doc_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        parent_page_id: Optional[str] = None,
        sub_title: Optional[str] = None,
        content: Optional[str] = None,
        content_format: str = "text/md",
    ) -> DocPage:
        """
        Create a new page in a doc.

        Args:
            name: The name of the new page
            doc_id: ID of the doc (uses the one set in the client context if not provided)
            workspace_id: ID of the workspace (uses the one set in the client context if not provided)
            parent_page_id: ID of the parent page (if this is a subpage)
            sub_title: The subtitle of the new page
            content: The content of the new page
            content_format: Format of the page content ('text/md' or 'text/plain')

        Returns:
            The created DocPage object

        Raises:
            ValueError: If doc_id or workspace_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the doc or workspace doesn't exist
            ValidationError: If the request data is invalid
            ClickUpError: For other API errors
        """
        doc_id = self._get_context_id("_doc_id", doc_id)
        workspace_id = self._get_context_id("_workspace_id", workspace_id)
        if not doc_id:
            raise ValueError("Doc ID must be provided")
        if not workspace_id:
            raise ValueError("Workspace ID must be provided")

        data = {
            "name": name,
            "content_format": content_format,
        }
        if parent_page_id:
            data["parent_page_id"] = parent_page_id
        if sub_title:
            data["sub_title"] = sub_title
        if content:
            data["content"] = content

        response = await self._request(
            "POST",
            f"workspaces/{workspace_id}/docs/{doc_id}/pages",
            data=data,
            api_version="v3",
        )
        return DocPage.model_validate(response)

    async def get_page(
        self,
        page_id: str,
        doc_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        content_format: str = "text/md",
    ) -> DocPage:
        """
        Get a specific page in a doc.

        Args:
            page_id: ID of the page to get
            doc_id: ID of the doc (uses the one set in the client context if not provided)
            workspace_id: ID of the workspace (uses the one set in the client context if not provided)
            content_format: Format to return the page content in ('text/md' or 'text/plain')

        Returns:
            The DocPage object

        Raises:
            ValueError: If doc_id or workspace_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the page, doc, or workspace doesn't exist
            ClickUpError: For other API errors
        """
        doc_id = self._get_context_id("_doc_id", doc_id)
        workspace_id = self._get_context_id("_workspace_id", workspace_id)
        if not doc_id:
            raise ValueError("Doc ID must be provided")
        if not workspace_id:
            raise ValueError("Workspace ID must be provided")

        params = {"content_format": content_format}
        response = await self._request(
            "GET",
            f"workspaces/{workspace_id}/docs/{doc_id}/pages/{page_id}",
            params=params,
            api_version="v3",
        )
        return DocPage.model_validate(response)

    async def update_page(
        self,
        page_id: str,
        doc_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        name: Optional[str] = None,
        sub_title: Optional[str] = None,
        content: Optional[str] = None,
        content_edit_mode: str = "replace",
        content_format: str = "text/md",
    ) -> DocPage:
        """
        Update a page in a doc.

        Args:
            page_id: ID of the page to update
            doc_id: ID of the doc (uses the one set in the client context if not provided)
            workspace_id: ID of the workspace (uses the one set in the client context if not provided)
            name: The updated name of the page
            sub_title: The updated subtitle of the page
            content: The updated content of the page
            content_edit_mode: Strategy for updating content ('replace', 'append', or 'prepend')
            content_format: Format of the page content ('text/md' or 'text/plain')

        Returns:
            The updated DocPage object

        Raises:
            ValueError: If doc_id or workspace_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the page, doc, or workspace doesn't exist
            ValidationError: If the request data is invalid
            ClickUpError: For other API errors
        """
        doc_id = self._get_context_id("_doc_id", doc_id)
        workspace_id = self._get_context_id("_workspace_id", workspace_id)
        if not doc_id:
            raise ValueError("Doc ID must be provided")
        if not workspace_id:
            raise ValueError("Workspace ID must be provided")

        data = {
            "content_edit_mode": content_edit_mode,
            "content_format": content_format,
        }
        if name is not None:
            data["name"] = name
        if sub_title is not None:
            data["sub_title"] = sub_title
        if content is not None:
            data["content"] = content

        response = await self._request(
            "PUT",
            f"workspaces/{workspace_id}/docs/{doc_id}/pages/{page_id}",
            data=data,
            api_version="v3",
        )
        return DocPage.model_validate(response)

    async def delete_page(
        self,
        page_id: str,
        doc_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
    ) -> bool:
        """
        Delete a page from a doc.

        Args:
            page_id: ID of the page to delete
            doc_id: ID of the doc (uses the one set in the client context if not provided)
            workspace_id: ID of the workspace (uses the one set in the client context if not provided)

        Returns:
            True if successful

        Raises:
            ValueError: If doc_id or workspace_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the page, doc, or workspace doesn't exist
            ClickUpError: For other API errors
        """
        doc_id = self._get_context_id("_doc_id", doc_id)
        workspace_id = self._get_context_id("_workspace_id", workspace_id)
        if not doc_id:
            raise ValueError("Doc ID must be provided")
        if not workspace_id:
            raise ValueError("Workspace ID must be provided")

        await self._request(
            "DELETE",
            f"workspaces/{workspace_id}/docs/{doc_id}/pages/{page_id}",
            api_version="v3",
        )
        return True

    async def delete(
        self,
        doc_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
    ) -> bool:
        """
        Delete a doc.

        Args:
            doc_id: ID of the doc to delete (uses the one set in the client context if not provided)
            workspace_id: ID of the workspace (uses the one set in the client context if not provided)

        Returns:
            True if successful

        Raises:
            ValueError: If doc_id or workspace_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the doc or workspace doesn't exist
            ClickUpError: For other API errors
        """
        doc_id = self._get_context_id("_doc_id", doc_id)
        workspace_id = self._get_context_id("_workspace_id", workspace_id)
        if not doc_id:
            raise ValueError("Doc ID must be provided")
        if not workspace_id:
            raise ValueError("Workspace ID must be provided")

        await self._request(
            "DELETE",
            f"workspaces/{workspace_id}/docs/{doc_id}",
            api_version="v3",
        )
        return True
