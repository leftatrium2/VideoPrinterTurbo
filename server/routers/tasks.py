from fastapi import APIRouter

router = APIRouter(
    prefix="/tasks",
    tags=["任务模块"]
)


@router.get("/")
def get_tasks():
    return {"tasks": []}


@router.post("/add")
def add_tasks():
    return {"message": "任务添加成功"}
