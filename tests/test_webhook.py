"""
Integration tests for ClickUp webhook operations.

These tests verify that the client works correctly with the real ClickUp API.
Requires a valid webhook endpoint URL configured in environment variables.

Environment Variables:
- CLICKUP_API_TOKEN: Your ClickUp API token
- CLICKUP_WORKSPACE_ID: ID of a workspace to test with
- CLICKUP_TEST_WEBHOOK_ENDPOINT: A valid URL to receive webhook events (e.g., from webhook.site)
"""

import asyncio
import logging
import os
from typing import Any, AsyncGenerator, Dict
from uuid import uuid4

import pytest
import pytest_asyncio

from src import ClickUp, Webhook
from src.exceptions import ClickUpError, ResourceNotFound, ValidationError

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("clickup")

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio

# Get webhook endpoint from environment variable
WEBHOOK_ENDPOINT = os.getenv("CLICKUP_TEST_WEBHOOK_ENDPOINT")
skip_reason = "CLICKUP_TEST_WEBHOOK_ENDPOINT environment variable not set"


@pytest_asyncio.fixture(scope="session")
async def sample_webhook(
    client: ClickUp, workspace
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Creates or retrieves a sample webhook for testing and ensures cleanup afterwards.
    This fixture is session-scoped and idempotent. Yields {'id': webhook_id}.
    """
    if not WEBHOOK_ENDPOINT:
        pytest.skip(skip_reason)
        return

    webhook_id_to_yield = None

    try:
        logger.info(
            f"Attempting to create/retrieve test webhook for endpoint: {WEBHOOK_ENDPOINT} in workspace {workspace.id}"
        )
        try:
            # 1. Attempt to create
            created_hook_data = await client.webhooks.create_webhook(
                workspace_id=workspace.id,
                endpoint=WEBHOOK_ENDPOINT,
                events=["*"],
            )
            assert isinstance(created_hook_data, dict)
            assert "id" in created_hook_data
            webhook_id_to_yield = created_hook_data["id"]
            logger.info(f"Created webhook {webhook_id_to_yield}")

        except ValidationError as e:
            # 2. If it already exists, fetch it to get the ID
            if "Webhook configuration already exists" in str(e):
                logger.warning(
                    f"Webhook for {WEBHOOK_ENDPOINT} already exists. Fetching..."
                )
                all_hooks = await client.webhooks.get_webhooks(
                    workspace_id=workspace.id
                )
                found = False
                for hook in all_hooks:
                    if hook.endpoint == WEBHOOK_ENDPOINT:
                        webhook_id_to_yield = hook.id
                        logger.info(f"Found existing webhook {webhook_id_to_yield}")
                        found = True
                        break
                if not found:
                    logger.error(
                        f"Webhook reported as existing but not found via GET for endpoint {WEBHOOK_ENDPOINT}"
                    )
                    pytest.fail(
                        f"Failed to find existing webhook for {WEBHOOK_ENDPOINT}"
                    )
            else:
                # Re-raise other validation errors
                raise e

        if webhook_id_to_yield is None:
            pytest.fail("Failed to create or find the sample webhook ID.")

        # Yield a dictionary containing only the ID, as that's all we can guarantee
        yield {"id": webhook_id_to_yield}

    finally:
        # Cleanup: Always attempt deletion if we got an ID
        if webhook_id_to_yield:
            try:
                logger.info(f"Cleaning up webhook {webhook_id_to_yield}")
                await client.webhooks.delete_webhook(webhook_id=webhook_id_to_yield)
                logger.info(f"Successfully deleted webhook {webhook_id_to_yield}")
            except ResourceNotFound:
                logger.info(
                    f"Webhook {webhook_id_to_yield} already deleted or not found during cleanup."
                )
            except Exception as cleanup_e:
                logger.error(
                    f"Error during webhook cleanup for {webhook_id_to_yield}: {cleanup_e}",
                    exc_info=True,
                )
        else:
            logger.info("No webhook ID available for cleanup.")


@pytest.mark.skipif(not WEBHOOK_ENDPOINT, reason=skip_reason)
async def test_get_webhooks(client: ClickUp, workspace, sample_webhook: Dict[str, Any]):
    """Test getting webhooks."""
    webhooks = await client.webhooks.get_webhooks(workspace_id=workspace.id)
    assert isinstance(webhooks, list)
    assert any(hook.id == sample_webhook["id"] for hook in webhooks)


@pytest.mark.skipif(not WEBHOOK_ENDPOINT, reason=skip_reason)
async def test_create_webhook(client: ClickUp, workspace, test_list):
    """Test creating a webhook scoped to a list."""
    created_hook_data = None
    try:
        created_hook_data = await client.webhooks.create_webhook(
            workspace_id=workspace.id,
            endpoint=f"{WEBHOOK_ENDPOINT}/{uuid4()}",  # Unique endpoint
            events=["taskCreated"],
            list_id=int(test_list.id),  # API expects integer for list_id
        )
        assert isinstance(created_hook_data, dict)
        assert "id" in created_hook_data
        # Cannot assert events/list_id as they are not returned by create
    finally:
        if created_hook_data:
            await client.webhooks.delete_webhook(webhook_id=created_hook_data["id"])


@pytest.mark.skipif(not WEBHOOK_ENDPOINT, reason=skip_reason)
async def test_update_webhook(
    client: ClickUp, sample_webhook: Dict[str, Any], workspace
):
    """Test updating a webhook."""
    new_endpoint = f"{WEBHOOK_ENDPOINT}/{uuid4()}"  # Unique endpoint
    new_events = ["taskUpdated", "taskDeleted"]

    update_response = await client.webhooks.update_webhook(
        webhook_id=sample_webhook["id"],
        endpoint=new_endpoint,
        events=new_events,
        status="active",
    )
    assert isinstance(update_response, dict)
    assert update_response["id"] == sample_webhook["id"]

    # Fetch the webhook again to verify the updates
    await asyncio.sleep(2)
    all_hooks = await client.webhooks.get_webhooks(workspace_id=workspace.id)
    updated_hook = None
    for hook in all_hooks:
        if hook.id == sample_webhook["id"]:
            updated_hook = hook
            break

    assert (
        updated_hook is not None
    ), f"Webhook {sample_webhook['id']} not found after update."
    assert isinstance(updated_hook, Webhook)
    assert updated_hook.endpoint == new_endpoint
    assert set(updated_hook.events) == set(
        new_events
    )  # Health status check might be flaky, so omit for now


@pytest.mark.skipif(not WEBHOOK_ENDPOINT, reason=skip_reason)
async def test_delete_webhook(client: ClickUp, workspace):
    """Test deleting a webhook."""
    # Create a webhook specifically for deletion
    hook_to_delete_data = await client.webhooks.create_webhook(
        workspace_id=workspace.id,
        endpoint=f"{WEBHOOK_ENDPOINT}/{uuid4()}",  # Unique endpoint
        events=["listCreated"],
    )
    assert "id" in hook_to_delete_data
    hook_id = hook_to_delete_data["id"]

    # Delete it
    deleted = await client.webhooks.delete_webhook(webhook_id=hook_id)
    assert deleted is True

    # Verify deletion by trying to get it (should fail)
    # We verify by checking if it's in the list after deletion
    all_hooks = await client.webhooks.get_webhooks(workspace_id=workspace.id)
    assert not any(hook.id == hook_id for hook in all_hooks)
