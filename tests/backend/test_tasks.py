"""
Tests for tasks API endpoints.
"""
import sys
from pathlib import Path

import pytest

# Add server directory to path to import mock_data directly
server_path = Path(__file__).parent.parent.parent / "server"
sys.path.insert(0, str(server_path))

import mock_data


@pytest.fixture(autouse=True)
def reset_tasks():
    """Reset the in-memory tasks list around each test to keep tests independent."""
    original = list(mock_data.tasks)
    mock_data.tasks.clear()
    yield
    mock_data.tasks.clear()
    mock_data.tasks.extend(original)


class TestTasksEndpoints:
    """Test suite for tasks-related endpoints."""

    def test_get_tasks_empty(self, client):
        """Test getting all tasks when none exist."""
        response = client.get("/api/tasks")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert data == []

    def test_create_task(self, client):
        """Test creating a new task."""
        response = client.post("/api/tasks", json={
            "title": "Review Q1 inventory levels",
            "priority": "high",
            "dueDate": "2026-01-15"
        })
        assert response.status_code == 201

        task = response.json()
        assert "id" in task
        assert isinstance(task["id"], str)
        assert task["title"] == "Review Q1 inventory levels"
        assert task["priority"] == "high"
        assert task["dueDate"] == "2026-01-15"
        assert task["status"] == "pending"

    def test_get_tasks_after_create(self, client):
        """Test that a created task shows up in the task list."""
        client.post("/api/tasks", json={
            "title": "Approve Tokyo warehouse orders",
            "priority": "medium",
            "dueDate": "2026-02-01"
        })

        response = client.get("/api/tasks")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Approve Tokyo warehouse orders"

    def test_create_multiple_tasks_unique_ids(self, client):
        """Test that multiple created tasks get distinct, incrementing ids."""
        first = client.post("/api/tasks", json={
            "title": "Task One",
            "priority": "low",
            "dueDate": "2026-03-01"
        }).json()
        second = client.post("/api/tasks", json={
            "title": "Task Two",
            "priority": "low",
            "dueDate": "2026-03-02"
        }).json()

        assert first["id"] != second["id"]
        assert int(second["id"]) > int(first["id"])

    def test_delete_task(self, client):
        """Test deleting an existing task."""
        created = client.post("/api/tasks", json={
            "title": "Update reorder points",
            "priority": "medium",
            "dueDate": "2026-04-01"
        }).json()

        response = client.delete(f"/api/tasks/{created['id']}")
        assert response.status_code == 200

        remaining = client.get("/api/tasks").json()
        assert all(t["id"] != created["id"] for t in remaining)

    def test_delete_nonexistent_task(self, client):
        """Test deleting a task that doesn't exist."""
        response = client.delete("/api/tasks/nonexistent-task-999")
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_toggle_task_pending_to_completed(self, client):
        """Test toggling a pending task to completed."""
        created = client.post("/api/tasks", json={
            "title": "Review monthly spending report",
            "priority": "low",
            "dueDate": "2026-05-01"
        }).json()
        assert created["status"] == "pending"

        response = client.patch(f"/api/tasks/{created['id']}")
        assert response.status_code == 200

        task = response.json()
        assert task["id"] == created["id"]
        assert task["status"] == "completed"

    def test_toggle_task_completed_to_pending(self, client):
        """Test toggling a task back to pending after it was completed."""
        created = client.post("/api/tasks", json={
            "title": "Check pending shipments",
            "priority": "high",
            "dueDate": "2026-06-01"
        }).json()

        client.patch(f"/api/tasks/{created['id']}")
        response = client.patch(f"/api/tasks/{created['id']}")
        assert response.status_code == 200

        task = response.json()
        assert task["status"] == "pending"

    def test_toggle_nonexistent_task(self, client):
        """Test toggling a task that doesn't exist."""
        response = client.patch("/api/tasks/nonexistent-task-999")
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_task_fields(self, client):
        """Test that a task response contains all required fields."""
        created = client.post("/api/tasks", json={
            "title": "Verify supplier contracts",
            "priority": "medium",
            "dueDate": "2026-07-01"
        }).json()

        for field in ("id", "title", "priority", "dueDate", "status"):
            assert field in created
