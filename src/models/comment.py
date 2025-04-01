"""
Comment models for ClickUp API.

This module contains models related to comments in ClickUp.
"""

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CommentText(BaseModel):
    """Represents the text content of a comment"""

    text: str

    model_config = ConfigDict(populate_by_name=True)


class Comment(BaseModel):
    """A comment on a task or list."""

    id: Optional[Union[str, int]] = None
    text: Optional[str] = None
    comment_text: Optional[str] = None
    comment_content: Optional[str] = Field(None, alias="comment_text")
    user: Optional[Dict[str, Any]] = None
    resolved: bool = False
    assignee: Optional[Union[str, Dict[str, Any]]] = None
    assigned_by: Optional[Dict[str, Any]] = None
    date: Optional[Union[str, int]] = None
    parent: Optional[str] = None
    reactions: Optional[List[Dict[str, Any]]] = None
    attributes: Optional[Dict[str, Any]] = None
    comment: Optional[List[Dict[str, Any]]] = None
    original_comment_text: Optional[str] = None
    original_assignee: Optional[str] = None
    hist_id: Optional[str] = None
    reply_count: Optional[int] = None
    group_assignee: Optional[Any] = None

    @field_validator("id")
    @classmethod
    def validate_id(cls, v):
        """Convert id to string if it's an integer."""
        if v is None:
            return None
        return str(v)

    @field_validator("date")
    @classmethod
    def validate_date(cls, v):
        """Convert date to string if it's an integer."""
        if v is None:
            return None
        return str(v)

    def model_post_init(self, __context: Any) -> None:
        """Handle comment text from API response."""
        # Handle nested comment structure
        if self.comment and isinstance(self.comment, list) and len(self.comment) > 0:
            comment_data = self.comment[0]
            if "text" in comment_data:
                self.text = comment_data["text"]
            if "comment_text" in comment_data:
                self.comment_text = comment_data["comment_text"]

        # Handle text/comment_text synchronization
        if self.comment_text is None and self.text is not None:
            self.comment_text = self.text
        elif self.text is None and self.comment_text is not None:
            self.text = self.comment_text

        # Use original values if current ones are None
        if self.assignee is None and self.original_assignee is not None:
            self.assignee = self.original_assignee

        if not self.text and not self.comment_text and self.original_comment_text:
            self.text = self.original_comment_text
            self.comment_text = self.original_comment_text

        # Ensure at least one text field is set
        if not self.text and not self.comment_text and not self.original_comment_text:
            self.text = ""
            self.comment_text = ""

        # Handle resolved value
        if isinstance(self.resolved, str):
            self.resolved = self.resolved.lower() == "true"

    @property
    def content(self) -> str:
        """Get the comment text content."""
        if self.text:
            return self.text
        if self.comment_text:
            return self.comment_text
        if self.comment_content:
            return self.comment_content

        if self.comment and isinstance(self.comment, list) and len(self.comment) > 0:
            comment_data = self.comment[0]
            if "text" in comment_data:
                return comment_data["text"]
            if "comment_text" in comment_data:
                return comment_data["comment_text"]

        if self.attributes and isinstance(self.attributes, dict):
            if "text" in self.attributes:
                return self.attributes["text"]

        if self.original_comment_text:
            return self.original_comment_text

        return ""

    @property
    def effective_assignee(self) -> Optional[Union[str, Dict[str, Any]]]:
        """Get the effective assignee of the comment."""
        if self.assignee is not None:
            return self.assignee
        return getattr(self, "original_assignee", None)

    model_config = ConfigDict(
        populate_by_name=True, extra="allow", validate_assignment=True
    )
