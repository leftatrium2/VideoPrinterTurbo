from fastapi import APIRouter

router = APIRouter(
    prefix="/publish_config",
    tags=["publish配置模块"]
)


@router.get("/")
def get_publish_config():
    return {"get_publish_config": "get_publish_config"}
