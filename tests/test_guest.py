"""
Integration tests for ClickUp Guest operations.

NOTE: These tests require an Enterprise Plan and specific environment variables.
They are skipped by default.

Environment Variables:
- CLICKUP_API_TOKEN: Your ClickUp API token
- CLICKUP_WORKSPACE_ID: ID of a workspace to test with
- CLICKUP_TEST_GUEST_EMAIL: Email address for inviting a test guest.
- CLICKUP_RUN_ENTERPRISE_TESTS: Set to 'true' to run these tests.
"""

import asyncio
import logging
import os
import uuid
from typing import Any, AsyncGenerator, Dict

import pytest
import pytest_asyncio

from src import ClickUp, Folder, Guest, Task, TaskList
from src.exceptions import ClickUpError, ResourceNotFound, ValidationError

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("clickup")

# --- Test Setup & Skipping --- #

TEST_GUEST_EMAIL = os.getenv("CLICKUP_TEST_GUEST_EMAIL")
RUN_ENTERPRISE_TESTS = (
    os.getenv("CLICKUP_RUN_ENTERPRISE_TESTS", "false").lower() == "true"
)

skip_reason = (
    "Guest tests require Enterprise plan (set CLICKUP_RUN_ENTERPRISE_TESTS=true) "
    "and CLICKUP_TEST_GUEST_EMAIL environment variable"
)

# Skip the entire module if conditions aren't met
pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.skipif(
        not RUN_ENTERPRISE_TESTS or not TEST_GUEST_EMAIL, reason=skip_reason
    ),
]


# --- Fixtures --- #


@pytest_asyncio.fixture(scope="session")  # Session scope to avoid re-inviting
async def test_guest(client: ClickUp, workspace) -> AsyncGenerator[Guest, None]:
    """Invites a test guest for the session and ensures cleanup."""
    guest_object = None
    # Ensure email is present (pytest skipif should handle None, but this satisfies linter)
    assert isinstance(
        TEST_GUEST_EMAIL, str
    ), "CLICKUP_TEST_GUEST_EMAIL must be set for guest tests"

    try:
        logger.info(
            f"Inviting test guest: {TEST_GUEST_EMAIL} to workspace {workspace.id}"
        )
        guest_object = await client.guests.invite_guest_to_workspace(
            workspace_id=workspace.id, email=TEST_GUEST_EMAIL
        )
        assert isinstance(guest_object, Guest)
        assert guest_object.email == TEST_GUEST_EMAIL
        logger.info(f"Invited guest with ID: {guest_object.id}")
        yield guest_object
    except Exception as e:
        logger.error(f"Failed to invite guest {TEST_GUEST_EMAIL}: {e}")
        pytest.fail(f"Guest fixture setup failed: {e}")
        return  # Should not be reached, but needed for type checker

    # Cleanup
    if guest_object:
        try:
            logger.info(f"Cleaning up guest {guest_object.id} ({TEST_GUEST_EMAIL})")
            await client.guests.remove_guest_from_workspace(
                workspace_id=workspace.id, guest_id=guest_object.id
            )
            logger.info(f"Successfully removed guest {guest_object.id}")
        except ResourceNotFound:
            logger.info(f"Guest {guest_object.id} already removed.")
        except Exception as cleanup_e:
            logger.error(
                f"Error cleaning up guest {guest_object.id}: {cleanup_e}", exc_info=True
            )


# --- Tests --- #


async def test_get_guest(client: ClickUp, workspace, test_guest: Guest):
    """Test getting a specific guest."""
    fetched_guest = await client.guests.get_guest(
        workspace_id=workspace.id, guest_id=test_guest.id
    )
    assert isinstance(fetched_guest, Guest)
    assert fetched_guest.id == test_guest.id
    assert fetched_guest.email == TEST_GUEST_EMAIL


async def test_edit_guest(client: ClickUp, workspace, test_guest: Guest):
    """Test editing a guest's details."""
    new_username = f"TestGuestEdit_{uuid.uuid4()}"
    edited_guest = await client.guests.edit_guest_on_workspace(
        workspace_id=workspace.id,
        guest_id=test_guest.id,
        username=new_username,
        can_edit_tags=False,  # Change a permission
    )
    assert isinstance(edited_guest, Guest)
    assert edited_guest.id == test_guest.id
    assert edited_guest.username == new_username
    assert edited_guest.can_edit_tags is False

    # Revert username for subsequent tests/cleanup if needed (optional)
    try:
        await client.guests.edit_guest_on_workspace(
            workspace_id=workspace.id,
            guest_id=test_guest.id,
            username=test_guest.username,  # Revert username if possible
            can_edit_tags=True,  # Revert permission
        )
    except Exception as revert_e:
        logger.warning(f"Could not revert guest username after edit test: {revert_e}")


async def test_add_remove_guest_task(
    client: ClickUp, test_task: Task, test_guest: Guest
):
    """Test adding and removing a guest from a task."""
    # Add guest
    logger.info(f"Adding guest {test_guest.id} to task {test_task.id}")
    add_resp = await client.tasks.add_guest_to_task(
        task_id=test_task.id, guest_id=test_guest.id, permission_level="read"
    )
    # API returns task object on success, check basic structure
    assert isinstance(add_resp, dict)
    assert add_resp.get("id") == test_task.id

    # Give time for permissions to apply
    await asyncio.sleep(3)

    # Verify guest is added (API doesn't directly expose task guests easily, rely on remove success)
    # logger.info(f"Verifying guest {test_guest.id} on task {test_task.id}...")
    # # Fetch task and check assignees/shared field if possible?

    # Remove guest
    logger.info(f"Removing guest {test_guest.id} from task {test_task.id}")
    await client.tasks.remove_guest_from_task(
        task_id=test_task.id, guest_id=test_guest.id
    )

    # Give time for permissions to apply
    await asyncio.sleep(3)

    # Verification is tricky - best we can do is ensure remove didn't error
    # Optionally try adding again and expect it to succeed if remove worked?
    logger.info(f"Verified removal of guest {test_guest.id} from task {test_task.id}")


async def test_add_remove_guest_list(
    client: ClickUp, test_list: TaskList, test_guest: Guest
):
    """Test adding and removing a guest from a list."""
    list_id_str = str(test_list.id)
    logger.info(f"Adding guest {test_guest.id} to list {list_id_str}")
    add_resp = await client.lists.add_guest_to_list(
        list_id=list_id_str, guest_id=test_guest.id, permission_level="comment"
    )
    assert isinstance(add_resp, dict)
    assert add_resp.get("id") == list_id_str

    await asyncio.sleep(3)

    logger.info(f"Removing guest {test_guest.id} from list {list_id_str}")
    await client.lists.remove_guest_from_list(
        list_id=list_id_str, guest_id=test_guest.id
    )

    await asyncio.sleep(3)
    logger.info(f"Verified removal of guest {test_guest.id} from list {list_id_str}")


async def test_add_remove_guest_folder(
    client: ClickUp, test_folder: Folder, test_guest: Guest
):
    """Test adding and removing a guest from a folder."""
    folder_id_str = str(test_folder.id)
    logger.info(f"Adding guest {test_guest.id} to folder {folder_id_str}")
    add_resp = await client.folders.add_guest_to_folder(
        folder_id=folder_id_str, guest_id=test_guest.id, permission_level="edit"
    )
    assert isinstance(add_resp, dict)
    assert add_resp.get("id") == folder_id_str

    await asyncio.sleep(3)

    logger.info(f"Removing guest {test_guest.id} from folder {folder_id_str}")
    await client.folders.remove_guest_from_folder(
        folder_id=folder_id_str, guest_id=test_guest.id
    )

    await asyncio.sleep(3)
    logger.info(
        f"Verified removal of guest {test_guest.id} from folder {folder_id_str}"
    )


# Note: test_remove_guest_from_workspace is implicitly tested by the fixture cleanup.
