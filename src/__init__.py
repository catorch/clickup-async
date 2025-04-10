"""
ClickUp Async - A modern, elegant client for the ClickUp API.

This package provides a clean, asynchronous interface to work with the ClickUp API.
"""

# Version info
__version__ = "0.1.0"
__author__ = "catorch"
__repository__ = "https://github.com/catorch/clickup-async"

# Set default logging handler to avoid "No handler found" warnings
import logging
from logging import NullHandler

# Import main classes for convenient access
from .client import ClickUp
from .exceptions import (
    AuthenticationError,
    ClickUpError,
    RateLimitExceeded,
    ResourceNotFound,
    ValidationError,
)
from .models import (
    Checklist,
    Comment,
    Folder,
    Guest,
    Space,
    Status,
    Tag,
    Task,
    TaskList,
    TimeEntry,
    View,
    Webhook,
    Workspace,
)
from .utils import convert_to_timestamp, human_readable_time, parse_time_to_milliseconds

logging.getLogger(__name__).addHandler(NullHandler())

__all__ = [
    # Main client
    "ClickUp",
    # Exceptions
    "ClickUpError",
    "AuthenticationError",
    "RateLimitExceeded",
    "ResourceNotFound",
    "ValidationError",
    # Models
    "Workspace",
    "Space",
    "Folder",
    "TaskList",
    "Task",
    "TimeEntry",
    "Comment",
    "Checklist",
    "Status",
    "View",
    "Webhook",
    "Tag",
    "Guest",
]
