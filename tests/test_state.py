import pytest
from app.models import const
from app.services.state import MemoryState


@pytest.fixture()
def mem():
    return MemoryState()


def test_update_and_get_task(mem):
    mem.update_task("t1", state=const.TASK_STATE_PROCESSING, progress=10)
    task = mem.get_task("t1")
    assert task["task_id"] == "t1"
    assert task["state"] == const.TASK_STATE_PROCESSING
    assert task["progress"] == 10


def test_update_task_overwrites(mem):
    mem.update_task("t1", progress=10)
    mem.update_task("t1", progress=50)
    assert mem.get_task("t1")["progress"] == 50


def test_progress_clamped_to_100(mem):
    mem.update_task("t1", progress=150)
    assert mem.get_task("t1")["progress"] == 100


def test_get_nonexistent_task_returns_none(mem):
    assert mem.get_task("missing") is None


def test_delete_existing_task(mem):
    mem.update_task("t1", progress=10)
    mem.delete_task("t1")
    assert mem.get_task("t1") is None


def test_delete_nonexistent_task_is_idempotent(mem):
    mem.delete_task("ghost")  # must not raise


def test_get_all_tasks_pagination(mem):
    for i in range(5):
        mem.update_task(f"task-{i}", progress=i * 10)

    page2, total = mem.get_all_tasks(page=2, page_size=2)
    assert total == 5
    assert len(page2) == 2
