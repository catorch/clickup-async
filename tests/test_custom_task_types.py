"""Tests for custom task types functionality."""

import pytest

from src.models import CustomItem


@pytest.mark.asyncio
async def test_get_custom_task_types(client, workspace):
    """Test getting custom task types from a workspace."""
    custom_items = await client.workspaces.get_custom_task_types(workspace.id)

    # Verify we got a list of CustomItem objects
    assert isinstance(custom_items, list)
    assert all(isinstance(item, CustomItem) for item in custom_items)

    # Log the custom items for debugging
    print("\nCustom Task Types:")
    for item in custom_items:
        print(f"- {item.name} (ID: {item.id})")
        if item.description:
            print(f"  Description: {item.description}")
        if item.name_plural:
            print(f"  Plural: {item.name_plural}")
        if item.avatar:
            print(f"  Avatar: {item.avatar}")


@pytest.mark.asyncio
async def test_custom_task_types_fluent_interface(client, workspace):
    """Test getting custom task types using the fluent interface."""
    custom_items = await client.workspaces.get_custom_task_types(
        workspace_id=workspace.id
    )

    # Verify we got a list of CustomItem objects
    assert isinstance(custom_items, list)
    assert all(isinstance(item, CustomItem) for item in custom_items)

    # Log the custom items for debugging
    print("\nCustom Task Types (via fluent interface):")
    for item in custom_items:
        print(f"- {item.name} (ID: {item.id})")
        if item.description:
            print(f"  Description: {item.description}")
        if item.name_plural:
            print(f"  Plural: {item.name_plural}")
        if item.avatar:
            print(f"  Avatar: {item.avatar}")


@pytest.mark.asyncio
async def test_custom_task_types_no_workspace_id(client):
    """Test that missing workspace ID raises ValueError."""
    # Create a new client instance without any workspace context
    test_client = client.__class__(client.api_token)
    test_client._workspace_id = None  # Explicitly set to None

    with pytest.raises(ValueError, match="Workspace ID must be provided"):
        await test_client.workspaces.get_custom_task_types()
