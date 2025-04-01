import asyncio
from datetime import datetime, timedelta

import pytest

from src.exceptions import ResourceNotFound
from src.models import KeyResultType


@pytest.mark.asyncio
async def test_goal_crud_operations(client, workspace):
    """Test creating, reading, updating, and deleting goals."""
    # Create a goal
    name = f"Test Goal {datetime.now()}"
    due_date = datetime.now() + timedelta(days=7)
    description = "Test goal description"

    created_goal = await client.goals.create(
        name=name,
        due_date=due_date,
        description=description,
        workspace_id=workspace.id,
    )

    assert created_goal.name == name
    assert created_goal.description == description

    # Get the goal and verify
    retrieved_goal = await client.goals.get(created_goal.id)
    assert retrieved_goal.id == created_goal.id
    assert retrieved_goal.name == name

    # Update the goal
    new_name = f"Updated Goal {datetime.now()}"
    updated_goal = await client.goals.update(
        goal_id=created_goal.id,
        name=new_name,
    )
    assert updated_goal.name == new_name

    # Get all goals and verify our goal is there
    goals = await client.goals.get_all(workspace_id=workspace.id)
    assert any(goal.id == created_goal.id for goal in goals)

    # Delete the goal
    assert await client.goals.delete(created_goal.id)

    # Verify deletion
    with pytest.raises(ResourceNotFound):
        await client.goals.get(created_goal.id)


@pytest.mark.asyncio
async def test_key_result_crud_operations(client, workspace):
    """Test creating, reading, updating, and deleting key results."""
    # First create a goal to add key results to
    goal = await client.goals.create(
        name=f"Test Goal for KR {datetime.now()}",
        due_date=datetime.now() + timedelta(days=7),
        description="Test goal for key results",
        workspace_id=workspace.id,
    )

    try:
        # Create a key result
        name = f"Test Key Result {datetime.now()}"
        kr_type = KeyResultType.NUMBER
        steps_start = 0
        steps_end = 100
        unit = "points"

        created_kr = await client.goals.create_key_result(
            goal_id=goal.id,
            name=name,
            type=kr_type,
            steps_start=steps_start,
            steps_end=steps_end,
            unit=unit,
        )

        assert created_kr.name == name
        assert created_kr.type == kr_type
        assert created_kr.steps_start == steps_start
        assert created_kr.steps_end == steps_end
        assert created_kr.unit == unit

        # Update the key result
        new_steps_current = 50
        updated_kr = await client.goals.update_key_result(
            key_result_id=created_kr.id,
            steps_current=new_steps_current,
        )
        assert updated_kr.steps_current == new_steps_current

        # Delete the key result
        assert await client.goals.delete_key_result(created_kr.id)

        # Verify the goal still exists after key result deletion
        goal_after = await client.goals.get(goal.id)
        assert goal_after.id == goal.id

    finally:
        # Clean up by deleting the goal
        await client.goals.delete(goal.id)


@pytest.mark.asyncio
async def test_goal_with_multiple_key_results(client, workspace):
    """Test managing multiple key results for a single goal."""
    print("\n=== Starting Multiple Key Results Test ===")
    print(f"Using workspace ID: {workspace.id}")

    # Create a goal
    print("\nAttempting to create goal...")
    try:
        goal = await client.goals.create(
            name=f"Multi KR Goal {datetime.now()}",
            due_date=datetime.now() + timedelta(days=7),
            description="Goal with multiple key results",
            workspace_id=workspace.id,
        )
        print(f"Created goal: {goal}")
    except Exception as e:
        error_message = str(e).lower()
        if (
            "free forever plan" in error_message
            or "100 usages" in error_message
            or "upgrade" in error_message
        ):
            print("Skipping test: Goals feature is limited in free plan")
            pytest.skip("Goals feature is limited in free plan")
        print(f"Error creating goal: {str(e)}")
        raise

    try:
        # Create multiple key results of different types
        kr_configs = [
            {
                "name": "Number KR",
                "type": KeyResultType.NUMBER,
                "steps_start": 0,
                "steps_end": 100,
                "unit": "items",
            },
            {
                "name": "Percentage KR",
                "type": KeyResultType.PERCENTAGE,
                "steps_start": 0,
                "steps_end": 100,
                "unit": "%",
            },
            {
                "name": "Currency KR",
                "type": KeyResultType.CURRENCY,
                "steps_start": 0,
                "steps_end": 1000,
                "unit": "USD",
            },
        ]

        print("\nCreating key results...")
        key_results = []
        for config in kr_configs:
            print(f"\nCreating key result with config: {config}")
            try:
                kr = await client.goals.create_key_result(goal_id=goal.id, **config)
                print(f"Created key result: {kr}")
                key_results.append(kr)
                await asyncio.sleep(1)  # Small delay between creations
            except Exception as e:
                error_message = str(e).lower()
                if (
                    "free forever plan" in error_message
                    or "100 usages" in error_message
                    or "upgrade" in error_message
                ):
                    print("Skipping test: Goals feature is limited in free plan")
                    pytest.skip("Goals feature is limited in free plan")
                print(f"Error creating key result {config['name']}: {str(e)}")
                raise

        print("\nVerifying key results...")
        # Verify all key results were created with correct types
        for kr, config in zip(key_results, kr_configs):
            print(f"\nVerifying key result: {kr.name}")
            print(f"Expected type: {config['type']}, Got type: {kr.type}")
            print(f"Expected unit: {config['unit']}, Got unit: {kr.unit}")
            print(f"Full key result data: {kr.model_dump_json(indent=2)}")
            assert (
                kr.name == config["name"]
            ), f"Name mismatch: expected {config['name']}, got {kr.name}"
            assert (
                kr.type == config["type"]
            ), f"Type mismatch: expected {config['type']}, got {kr.type}"
            assert (
                kr.unit == config["unit"]
            ), f"Unit mismatch: expected {config['unit']}, got {kr.unit}"
            print("Verification passed!")

        print("\nUpdating key result progress...")
        # Update progress on all key results
        for kr in key_results:
            print(f"\nUpdating progress for key result: {kr.name}")
            expected_progress = kr.steps_end // 2
            print(f"Setting progress to: {expected_progress}")
            try:
                updated_kr = await client.goals.update_key_result(
                    key_result_id=kr.id,
                    steps_current=expected_progress,
                )
                print(f"Updated key result: {updated_kr}")
                print(
                    f"Full updated key result data: {updated_kr.model_dump_json(indent=2)}"
                )
                assert (
                    updated_kr.steps_current == expected_progress
                ), f"Progress mismatch: expected {expected_progress}, got {updated_kr.steps_current}"
                await asyncio.sleep(1)  # Small delay between updates
            except Exception as e:
                error_message = str(e).lower()
                if (
                    "free forever plan" in error_message
                    or "100 usages" in error_message
                    or "upgrade" in error_message
                ):
                    print("Skipping test: Goals feature is limited in free plan")
                    pytest.skip("Goals feature is limited in free plan")
                print(f"Error updating key result {kr.name}: {str(e)}")
                raise

        print("\nDeleting key results...")
        # Delete all key results
        for kr in key_results:
            print(f"\nDeleting key result: {kr.name}")
            try:
                result = await client.goals.delete_key_result(kr.id)
                print(f"Deletion result: {result}")
                assert result, f"Failed to delete key result {kr.name}"
                print("Deletion successful!")
                await asyncio.sleep(1)  # Small delay between deletions
            except Exception as e:
                error_message = str(e).lower()
                if (
                    "free forever plan" in error_message
                    or "100 usages" in error_message
                    or "upgrade" in error_message
                ):
                    print("Skipping test: Goals feature is limited in free plan")
                    pytest.skip("Goals feature is limited in free plan")
                print(f"Error deleting key result {kr.name}: {str(e)}")
                raise

    except Exception as e:
        print(f"\nTest failed with error: {str(e)}")
        raise
    finally:
        print("\nCleaning up goal...")
        try:
            # Clean up by deleting the goal
            if "goal" in locals():
                await client.goals.delete(goal.id)
                print("Goal deleted successfully!")
        except Exception as e:
            error_message = str(e).lower()
            if (
                "free forever plan" in error_message
                or "100 usages" in error_message
                or "upgrade" in error_message
            ):
                print("Skipping cleanup: Goals feature is limited in free plan")
            else:
                print(f"Error deleting goal: {str(e)}")
        print("\n=== Test Completed ===")
