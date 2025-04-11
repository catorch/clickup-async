# ClickUp Async ✨

[![PyPI Version](https://img.shields.io/pypi/v/clickup-async.svg)](https://pypi.org/project/clickup-async/)
[![Python Versions](https://img.shields.io/pypi/pyversions/clickup-async.svg)](https://pypi.org/project/clickup-async/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/clickup-async/month)](https://pepy.tech/project/clickup-async)

A modern, high-performance Python client for the ClickUp API with first-class async support. Built for developers who need robust, type-safe, and efficient ClickUp integration in their Python applications.

## 🌟 Why Choose ClickUp Async?

Transform your ClickUp workflow automation with a library that prioritizes developer experience and performance:

| Feature | ClickUp Async | Other Libraries |
|---------|--------------|-----------------|
| **Async Support** | ✅ Full async/await with concurrent operations | ❌ Synchronous only |
| **Type Safety** | ✅ Comprehensive type hints & Pydantic validation | ❌ Limited or none |
| **Rate Limiting** | ✅ Smart handling with exponential backoff | ❌ Basic or none |
| **Fluent Interface** | ✅ Intuitive, chainable API design | ❌ Verbose calls |
| **Modern Python** | ✅ Leverages Python 3.9+ features | ❌ Legacy compatibility |
| **Error Handling** | ✅ Detailed exceptions with context | ❌ Basic exceptions |
| **Pagination** | ✅ Automatic with async iterators | ❌ Manual handling |
| **Documentation** | ✅ Comprehensive with examples | ❌ Limited coverage |
| **Maintenance** | ✅ Active development & support | ❌ Irregular updates |

## 🚀 Quick Start

### Installation

```bash
pip install clickup-async
```

### Basic Usage

```python
import asyncio
from clickup_async import ClickUp
from clickup_async.models import Priority, Task

async def main():
    async with ClickUp(api_token="your_token_here") as client:
        # Get user info
        user = await client.get_authenticated_user()
        print(f"👋 Welcome, {user.username}!")
        
        # Create a task with rich metadata
        task = await client.list("list_id").tasks.create_task(
            name="Launch New Feature",
            description="## Objective\nImplement the new feature with following requirements:\n\n- High performance\n- User friendly\n- Well tested",
            priority=Priority.HIGH,
            due_date="next Friday",
            tags=["feature", "backend"],
            notify_all=True
        )
        
        print(f"✨ Created task: {task.name} (ID: {task.id})")

if __name__ == "__main__":
    asyncio.run(main())
```

## 📚 Comprehensive Feature Guide

### 🔐 Authentication & Setup

```python
from clickup_async import ClickUp

# Basic setup
client = ClickUp(api_token="your_token")

# Advanced configuration
client = ClickUp(
    api_token="your_token",
    retry_rate_limited_requests=True,
    rate_limit_buffer=5,
    timeout=30,
    base_url="https://api.clickup.com/api/v2"
)
```

### 📋 Task Management

Create, update, and manage tasks with rich functionality:

```python
# Create a task with custom fields
task = await client.list("list_id").tasks.create_task(
    name="New Feature Implementation",
    description="Implement the new feature",
    assignees=["user_id"],
    tags=["feature"],
    custom_fields=[{
        "id": "field_id",
        "value": "High Impact"
    }]
)

# Update task status
updated_task = await client.task(task.id).update(
    status="In Progress",
    priority=Priority.URGENT
)

# Add time tracking
await client.task(task.id).time.add_time_entry(
    duration=3600,  # 1 hour in seconds
    description="Initial implementation"
)

# Add a comment with attachments
await client.task(task.id).comments.create_comment(
    text="Please review the implementation",
    assignee="user_id",
    notify_all=True
)
```

### 🔄 Working with Lists and Views

Manage task lists and custom views efficiently:

```python
# Create a new list
new_list = await client.folder("folder_id").lists.create_list(
    name="Q4 Projects",
    content="Strategic projects for Q4",
    due_date="end of quarter"
)

# Get tasks with advanced filtering
tasks = await client.list("list_id").tasks.get_tasks(
    due_date_gt="today",
    due_date_lt="next month",
    assignees=["user_id"],
    include_closed=False,
    subtasks=True,
    order_by="due_date"
)

# Create a custom view
view = await client.list("list_id").views.create_view(
    name="High Priority Tasks",
    type="list",
    filters={
        "priority": [Priority.HIGH, Priority.URGENT]
    }
)
```

### 📊 Goals and Tracking

Set up and track goals with key results:

```python
# Create a new goal
goal = await client.team("team_id").goals.create_goal(
    name="Increase Performance",
    due_date="end of quarter",
    description="Improve system performance metrics"
)

# Add key results
key_result = await client.goal(goal.id).key_results.create_key_result(
    name="Reduce Response Time",
    steps=100,
    unit="ms",
    start_value=200,
    target_value=50
)
```

### 🔔 Webhooks and Automation

Set up real-time notifications and automation:

```python
# Create a webhook
webhook = await client.workspace("workspace_id").webhooks.create_webhook(
    endpoint="https://your-domain.com/webhook",
    events=["taskCreated", "taskUpdated"],
    space_id="space_id"
)

# Get webhook history
history = await client.webhook(webhook.id).get_webhook_history()
```

### 🔄 Smart Pagination

Handle large datasets efficiently with automatic pagination:

```python
async def get_all_tasks(list_id: str) -> list[Task]:
    tasks_page = await client.list(list_id).tasks.get_tasks()
    all_tasks = []
    
    while True:
        all_tasks.extend(tasks_page.items)
        if not tasks_page.has_more:
            break
        tasks_page = await tasks_page.next_page()
    
    return all_tasks
```

## 🛠️ Development and Testing

### Setting Up Development Environment

1. Clone the repository
   ```bash
   git clone https://github.com/catorch/clickup-async.git
   cd clickup-async
   ```

2. Create virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install development dependencies
   ```bash
   pip install -e ".[dev,test]"
   ```

### Running Tests

```bash
# Set up environment variables
export CLICKUP_API_KEY=your_token_here

# Run tests with coverage
pytest --cov=clickup_async
```

## License

MIT License - See [LICENSE](LICENSE) for details.

---

⭐ If you find this library helpful, please consider starring it on GitHub!

💡 Need help? [Open an issue](https://github.com/catorch/clickup-async/issues) or join our [Discord community](https://discord.gg/your-discord).