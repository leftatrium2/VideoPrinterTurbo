from fastapi import APIRouter

router = APIRouter(
    prefix="/llm_config",
    tags=["llm配置模块"]
)


@router.get("/")
def get_llm_config():
    return {"get_llm_config": "get_llm_config"}
