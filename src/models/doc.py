"""
Doc models for ClickUp API.

This module contains models related to docs and doc pages in ClickUp.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class DocPage(BaseModel):
    """Represents a page in a ClickUp doc."""

    id: str
    name: str
    content: Optional[str] = None
    sub_title: Optional[str] = None
    parent_page_id: Optional[str] = None
    created_date: Optional[int] = None
    updated_date: Optional[int] = None
    assignee: Optional[Dict[str, Any]] = None
    archived: Optional[bool] = None

    model_config = ConfigDict(populate_by_name=True)


class DocPageListing(BaseModel):
    """Represents a page listing in a ClickUp doc."""

    id: str
    name: str
    sub_title: Optional[str] = None
    parent_page_id: Optional[str] = None
    pages: List["DocPageListing"] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


class Doc(BaseModel):
    """Represents a ClickUp doc."""

    id: str
    name: str
    title: Optional[str] = None
    description: Optional[str] = None
    folder_id: Optional[str] = None
    space_id: Optional[str] = None
    list_id: Optional[str] = None
    task_id: Optional[str] = None
    created_by_id: Optional[str] = None
    created_date: Optional[int] = None
    updated_date: Optional[int] = None
    archived: Optional[bool] = None
    deleted: Optional[bool] = None
    visibility: Optional[str] = None  # PUBLIC, PRIVATE
    parent: Optional[Dict[str, Any]] = None
    hidden: Optional[bool] = None
    pages: Optional[List[DocPage]] = None

    model_config = ConfigDict(populate_by_name=True)


# Handle circular reference
DocPageListing.model_rebuild()
