"""
Tests for ClickUp workspace operations.
"""

import pytest

from src.models import Workspace


@pytest.mark.asyncio
async def test_get_workspaces(client):
    """Test getting all workspaces."""
    workspaces = await client.workspaces.get_workspaces()
    assert isinstance(workspaces, list)
    assert all(isinstance(w, Workspace) for w in workspaces)


@pytest.mark.asyncio
async def test_get_workspace(client, workspace):
    """Test getting a specific workspace."""
    workspace_details = await client.workspaces.get_workspace(workspace.id)
    assert isinstance(workspace_details, Workspace)
    assert workspace_details.id == workspace.id
    assert workspace_details.name == workspace.name


@pytest.mark.asyncio
async def test_workspace_fluent_interface(client, workspace):
    """Test the fluent interface for workspace operations."""
    # Test chaining workspace operations
    workspace_details = await client.workspace(workspace.id).workspaces.get_workspace()
    assert isinstance(workspace_details, Workspace)
    assert workspace_details.id == workspace.id
    assert workspace_details.name == workspace.name
