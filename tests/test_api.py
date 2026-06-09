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


# ── GET /api/v1/stream/{file_path} ──────────────────────────────────────────


def test_stream_video_ok(client, tmp_task_dir):
    task_dir = tmp_task_dir / "task-stream-ok"
    task_dir.mkdir()
    video = task_dir / "final-1.mp4"
    video.write_bytes(b"\x00" * 1024)

    response = client.get("/api/v1/stream/task-stream-ok/final-1.mp4")
    assert response.status_code == 206
    assert "Content-Range" in response.headers


def test_stream_path_traversal_returns_403(client, mocker):
    """ValueError with 'path traversal' in message → 403."""
    mocker.patch(
        "app.controllers.v1.rewrite.file_security.resolve_path_within_directory",
        side_effect=ValueError("path traversal detected: /etc/passwd"),
    )
    response = client.get("/api/v1/stream/anything")
    assert response.status_code == 403


def test_stream_file_not_found_returns_404(client, tmp_task_dir):
    response = client.get("/api/v1/stream/ghost-task/missing.mp4")
    assert response.status_code == 404


# ── GET /api/v1/download/{file_path} ────────────────────────────────────────


def test_download_video_ok(client, tmp_task_dir):
    task_dir = tmp_task_dir / "task-dl-ok"
    task_dir.mkdir()
    video = task_dir / "final-1.mp4"
    video.write_bytes(b"\x00" * 512)

    response = client.get("/api/v1/download/task-dl-ok/final-1.mp4")
    assert response.status_code == 200
    assert "Content-Disposition" in response.headers
    assert "final-1" in response.headers["Content-Disposition"]


def test_download_path_traversal_returns_403(client, mocker):
    """ValueError with 'path traversal' in message → 403."""
    mocker.patch(
        "app.controllers.v1.rewrite.file_security.resolve_path_within_directory",
        side_effect=ValueError("path traversal detected: /etc/passwd"),
    )
    response = client.get("/api/v1/download/anything")
    assert response.status_code == 403


def test_download_file_not_found_returns_404(client, tmp_task_dir):
    response = client.get("/api/v1/download/ghost-task/missing.mp4")
    assert response.status_code == 404
