import pytest
from app.controllers.manager.base_manager import TaskQueueFullError
from app.models import const


# ── POST /api/v1/rewrite ────────────────────────────────────────────────────


def test_create_task_success(client, mock_task_manager):
    response = client.post("/api/v1/rewrite", json={"video_url": "https://example.com/v.mp4"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == 200
    task_id = body["data"]["task_id"]
    assert len(task_id) == 36  # UUID format
    mock_task_manager.assert_called_once()


def test_create_task_queue_full(client, mocker):
    from app.controllers.v1 import rewrite
    mocker.patch.object(
        rewrite.task_manager,
        "add_task",
        side_effect=TaskQueueFullError("queue full"),
    )
    response = client.post("/api/v1/rewrite", json={"video_url": "https://example.com/v.mp4"})
    assert response.status_code == 429


# ── GET /api/v1/tasks ───────────────────────────────────────────────────────


def test_get_all_tasks_pagination(client, state):
    state.update_task("task-1", state=const.TASK_STATE_PROCESSING, progress=10)
    state.update_task("task-2", state=const.TASK_STATE_COMPLETE, progress=100)

    response = client.get("/api/v1/tasks?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 2
    assert len(data["tasks"]) == 2
    assert data["page"] == 1


# ── GET /api/v1/tasks/{task_id} ─────────────────────────────────────────────


def test_get_task_found(client, state):
    state.update_task("abc-123", state=const.TASK_STATE_PROCESSING, progress=42)

    response = client.get("/api/v1/tasks/abc-123")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["task_id"] == "abc-123"
    assert data["progress"] == 42


def test_get_task_not_found(client):
    response = client.get("/api/v1/tasks/nonexistent-id")
    assert response.status_code == 404


# ── DELETE /api/v1/tasks/{task_id} ──────────────────────────────────────────


def test_delete_task_success(client, state):
    state.update_task("del-me", state=const.TASK_STATE_COMPLETE, progress=100)

    response = client.delete("/api/v1/tasks/del-me")
    assert response.status_code == 200
    assert state.get_task("del-me") is None


def test_delete_task_not_found(client):
    response = client.delete("/api/v1/tasks/nonexistent-id")
    assert response.status_code == 404


# ── GET /api/v1/musics ──────────────────────────────────────────────────────


def test_get_musics_returns_list(client):
    response = client.get("/api/v1/musics")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "files" in data
    assert isinstance(data["files"], list)
