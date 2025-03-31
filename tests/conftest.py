"""
Shared test fixtures for ClickUp API tests.
"""

import asyncio
import os
import uuid
from datetime import datetime, timedelta
from typing import AsyncGenerator, cast

import pytest
import pytest_asyncio
from dotenv import load_dotenv

from src import ClickUp, ClickUpError, Folder, Space, Task, TaskList, Workspace

# Load environment variables from .env file
load_dotenv()

# Get API token from environment variable
API_TOKEN = cast(str, os.environ.get("CLICKUP_API_TOKEN"))
if not API_TOKEN:
    raise ValueError(
        "CLICKUP_API_TOKEN environment variable must be set to run tests."
        "Create one at https://app.clickup.com/settings/apps"
    )

# Configure pytest-asyncio
pytest_plugins = ("pytest_asyncio",)
pytestmark = pytest.mark.asyncio


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def client() -> AsyncGenerator[ClickUp, None]:
    """Create a ClickUp client for testing."""
    client = ClickUp(api_token=API_TOKEN)
    yield client
    await client.close()


@pytest_asyncio.fixture(scope="session")
async def workspace(client: ClickUp) -> AsyncGenerator[Workspace, None]:
    """Get the first workspace for testing."""
    workspaces = await client.get_workspaces()
    assert workspaces, "No workspaces found"
    yield workspaces[0]


@pytest_asyncio.fixture(scope="function")
async def test_space(
    client: ClickUp, workspace: Workspace
) -> AsyncGenerator[Space, None]:
    """Get an existing space for testing."""
    spaces = await client.get_spaces(workspace.id)
    assert spaces, "No spaces found in workspace"
    yield spaces[0]


@pytest_asyncio.fixture(scope="function")
async def test_folder(
    client: ClickUp, test_space: Space
) -> AsyncGenerator[Folder, None]:
    """Create a test folder and clean it up after the test."""
    name = f"Test Folder {uuid.uuid4()}"
    folder = await client.create_folder(test_space.id, name)
    yield folder
    await client.delete_folder(folder.id)


@pytest_asyncio.fixture(scope="function")
async def test_list(
    client: ClickUp, test_folder: Folder
) -> AsyncGenerator[TaskList, None]:
    """Create a test list and clean it up after the test."""
    name = f"Test List {uuid.uuid4()}"
    task_list = await client.create_list(test_folder.id, name)
    yield task_list
    await client.delete_list(task_list.id)


@pytest_asyncio.fixture(scope="function")
async def test_task(client: ClickUp, test_list: TaskList) -> AsyncGenerator[Task, None]:
    """Create a test task and clean it up after the test."""
    name = f"Test Task {uuid.uuid4()}"
    task = await client.create_task(test_list.id, name)
    yield task
    await client.delete_task(task.id)
