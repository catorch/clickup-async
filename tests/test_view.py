"""
Integration tests for ClickUp view operations.

These tests verify that the client works correctly with the real ClickUp API.
To run these tests, you need to set up the following environment variables:
- CLICKUP_API_TOKEN: Your ClickUp API token
- CLICKUP_WORKSPACE_ID: ID of a workspace to test with
"""

import logging
from uuid import uuid4

import pytest
import pytest_asyncio

from src import ClickUp, View
from src.exceptions import ClickUpError, ResourceNotFound, ValidationError

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("clickup")

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio


async def test_get_workspace_views(client: ClickUp, workspace):
    """Test getting workspace views."""
    views = await client.views.get_workspace_views(workspace_id=workspace.id)
    assert isinstance(views, list)
    for view in views:
        assert isinstance(view, View)


async def test_get_space_views(client: ClickUp, test_space):
    """Test getting space views."""
    views = await client.views.get_space_views(space_id=test_space.id)
    assert isinstance(views, list)
    for view in views:
        assert isinstance(view, View)


async def test_get_folder_views(client: ClickUp, test_folder):
    """Test getting folder views."""
    views = await client.views.get_folder_views(folder_id=test_folder.id)
    assert isinstance(views, list)
    for view in views:
        assert isinstance(view, View)


async def test_get_list_views(client: ClickUp, test_list):
    """Test getting list views."""
    view_data = await client.views.get_list_views(list_id=test_list.id)

    assert isinstance(view_data, dict)
    assert "views" in view_data
    assert "required_views" in view_data

    for view in view_data["views"]:
        assert isinstance(view, View)

    # Required views are returned as strings
    for view_type in view_data["required_views"]:
        assert isinstance(view_type, str)


async def test_create_list_view(client: ClickUp, test_list):
    """Test creating a list view."""
    view_name = f"Test List View {uuid4()}"

    created_view = await client.views.create_list_view(
        name=view_name,
        type="board",
        list_id=test_list.id,
    )

    assert isinstance(created_view, View)
    assert created_view.name == view_name
    assert created_view.type == "board"

    # Clean up
    if created_view.id:
        await client.views.delete_view(view_id=created_view.id)


async def test_update_view(client: ClickUp, test_list):
    """Test updating a view."""
    # First create a view
    view_name = f"Test View to Update {uuid4()}"
    created_view = await client.views.create_list_view(
        name=view_name,
        type="list",
        list_id=test_list.id,
    )

    try:
        # Update the view
        new_name = f"Updated View {uuid4()}"
        # Make sure view ID is not None
        if created_view.id:
            updated_view = await client.views.update_view(
                view_id=created_view.id,
                name=new_name,
            )

            assert isinstance(updated_view, View)
            assert updated_view.id == created_view.id
            assert updated_view.name == new_name

    finally:
        # Clean up
        if created_view.id:
            await client.views.delete_view(view_id=created_view.id)


async def test_delete_view(client: ClickUp, test_list):
    """Test deleting a view."""
    # First create a view
    view_name = f"Test View to Delete {uuid4()}"
    created_view = await client.views.create_list_view(
        name=view_name,
        type="list",
        list_id=test_list.id,
    )

    # Delete the view
    if created_view.id:
        result = await client.views.delete_view(view_id=created_view.id)
        assert result is True

        # Verify deletion
        with pytest.raises(ResourceNotFound):
            await client.views.get_view(view_id=created_view.id)


async def test_view_fluent_interface(client: ClickUp, workspace):
    """Test using the view with fluent interface."""
    # Get views using fluent interface without using workspace().views
    views = await client.views.get_workspace_views(workspace_id=workspace.id)
    assert isinstance(views, list)

    if views and views[0].id:
        # Test getting a specific view
        view = await client.views.get_view(view_id=views[0].id)
        assert isinstance(view, View)
        assert view.id == views[0].id
